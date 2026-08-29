import importlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ceo_actions
import ceo_console
import console_auth
import console_board
from ceo_page import render_page


class Handler:
    def __init__(self, path, method="GET", payload=None, token="Bearer token"):
        self.path = path
        body = json.dumps(payload or {}).encode()
        self.headers = {"Authorization": token, "Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        self.status = None

    def send_response(self, status): self.status = status
    def send_header(self, _name, _value): pass
    def end_headers(self): pass


def board_card(task_id="TASK-1", attachment="none", section="Human Approval"):
    return f'''# Board

## Backlog

## In Progress

## CMO Review

## Human Approval

### {task_id} — Content idea
- ID: {task_id}
- Title: Content idea
- Owner: content
- Skill: content
- Status: {section}
- Priority: high
- Attachment: {attachment}
- Decision summary:
  - The reviewed content is ready.
  - The claims remain subject to human review.
  - The artifact can be revised.
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z

## Completed
'''


class CEOConsoleTests(unittest.TestCase):
    def test_handles_is_boundary_pinned(self):
        self.assertTrue(ceo_console.handles("/ceo"))
        self.assertTrue(ceo_console.handles("/ceo/api/state"))
        self.assertFalse(ceo_console.handles("/ceoanything"))
        self.assertFalse(ceo_console.handles("/tech"))

    def test_tech_role_cannot_reach_ceo_write_route(self):
        handler = Handler("/ceo/api/revision", payload={"task_id": "TASK-001", "comment": "change"})
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://auth.invalid", "SUPABASE_ANON_KEY": "anon",
            "CMO_CEO_EMAIL": "ceo@example.test", "CMO_TECH_EMAIL": "tech@example.test",
        }, clear=False), patch.object(
            console_auth, "_supabase_get_user", return_value="tech@example.test"
        ):
            console_auth._token_cache.clear()
            ceo_console.dispatch(handler, "POST")
        self.assertEqual(handler.status, 403)

    def test_preview_blocks_every_ceo_write_route(self):
        with patch.dict(os.environ, {"CMO_DASHBOARD_PREVIEW": "1"}), patch.object(
            ceo_console.console_auth, "authorize", return_value=("ceo@example.test", "ceo")
        ):
            for route in (
                "/ceo/api/decision",
                "/ceo/api/revision",
                "/ceo/api/propose",
                "/ceo/api/proposal/approve",
                "/ceo/api/proposal/suggest",
                "/ceo/api/proposal/reject",
                "/ceo/api/proposal/undo-rejection",
            ):
                handler = Handler(
                    route,
                    payload={
                        "task_id": "TASK-001",
                        "decision": "approve",
                        "comment": "change",
                        "subject": "battery data",
                        "proposal_id": 1,
                        "reason": "covered",
                    },
                )
                ceo_console.dispatch(handler, "POST")
                self.assertEqual(handler.status, 403)

    def test_shell_needs_no_token_and_contains_no_board_data(self):
        handler = Handler("/ceo", token="")
        self.assertTrue(ceo_console.dispatch(handler, "GET"))
        body = handler.wfile.getvalue().decode()
        self.assertEqual(handler.status, 200)
        self.assertIn("Topics", body)
        self.assertNotIn("TASK-", body)
        self.assertNotIn("Content idea", body)

    def test_artifact_rule_uses_only_real_artifacts_directory_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifacts").mkdir()
            (root / "other").mkdir()
            artifact = root / "artifacts" / "draft.md"
            artifact.write_text("draft", encoding="utf-8")
            outside = root / "other" / "draft.md"
            outside.write_text("draft", encoding="utf-8")
            self.assertEqual(console_board.artifact_for({"attachment": "artifacts/draft.md"}, root), artifact)
            self.assertIsNone(console_board.artifact_for({"attachment": "other/draft.md"}, root))
            self.assertIsNone(console_board.artifact_for({"attachment": "none"}, root))

    def test_every_content_card_reaches_the_blogs_tab_with_a_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifacts").mkdir()
            (root / "artifacts" / "draft.md").write_text("draft", encoding="utf-8")
            board = root / "tasks.md"
            text = board_card("TASK-1", "none") + board_card("TASK-2", "artifacts/draft.md").split("## Human Approval", 1)[1].split("## Completed", 1)[0]
            board.write_text(text, encoding="utf-8")
            result = console_board.read_board(board, root)
        # An unwritten content card is not a "topic" here — topics live in the
        # proposals store until they are approved — but it is on the tab, saying
        # what it is waiting for. Only the written one carries an article payload.
        self.assertNotIn("topics", result)
        self.assertEqual([x["id"] for x in result["blogs"]], ["TASK-1", "TASK-2"])
        self.assertIsNone(result["blogs"][0]["article"])
        self.assertIsNotNone(result["blogs"][1]["article"])

    def test_revision_is_fields_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            path = root / "tasks.md"
            path.write_text(board_card(section="Human Approval"), encoding="utf-8")
            ceo_actions.request_revision(root, "TASK-1", "Add source notes", "ceo@example.test")
            after_revision = path.read_text(encoding="utf-8")
            self.assertIn("## Human Approval", after_revision)
            self.assertIn("- Status: Human Approval", after_revision)
            self.assertIn("- Revision round: 1", after_revision)
            self.assertFalse((root / "state" / "human-approvals.json").exists())

    def test_a_revision_is_refused_on_a_card_that_never_reached_him(self):
        """Hiding the button is the courtesy; this is the guard.

        Asking for changes on a card still in CMO Review used to succeed. It set
        `Change status: revision requested` and `Revision round: 1` on an article
        its reader had never been shown — and once the content worker existed,
        that started a rewrite. `DecisionStore` already refuses approvals outside
        Human Approval; the other half of the decision surface now agrees.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            path = root / "tasks.md"
            # The card's own Status names its lane, and board_card files it there.
            path.write_text(
                board_card(section="CMO Review").replace(
                    "## CMO Review\n\n## Human Approval\n\n### TASK-1",
                    "## CMO Review\n\n### TASK-1",
                ),
                encoding="utf-8",
            )
            before = path.read_text(encoding="utf-8")

            from cmo_runtime.task_file import TaskFileError

            with self.assertRaises(TaskFileError) as raised:
                ceo_actions.request_revision(root, "TASK-1", "Shorten the opening", "ceo@example.test")

            self.assertIn("not Human Approval", str(raised.exception))
            self.assertEqual(path.read_text(encoding="utf-8"), before, "the board was written anyway")

    def test_an_edit_that_removes_the_front_matter_is_refused(self):
        """The block between the --- lines is not prose; it is the published page.

        An edit that dropped it left an article that read perfectly and could not
        be published at all — and nothing said so until the publish check ran,
        after the card had been approved on the broken version. That happened.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            (root / "artifacts").mkdir()
            article = root / "artifacts" / "draft.md"
            article.write_text(
                "---\ntitle: A guide\nslug: a-guide\ncategory: financing\n---\n\n# A guide\n\nBody.\n",
                encoding="utf-8",
            )
            (root / "tasks.md").write_text(board_card(attachment="artifacts/draft.md"), encoding="utf-8")
            before = article.read_bytes()

            from cmo_runtime.task_file import TaskFileError

            with self.assertRaises(TaskFileError) as raised:
                ceo_actions.save_article_edit(
                    root, "TASK-1", "# A guide\n\nBody, edited.\n", "ceo@example.test"
                )

            self.assertIn("front matter", str(raised.exception))
            self.assertEqual(article.read_bytes(), before, "the article was written anyway")

    def test_an_edit_that_keeps_the_front_matter_is_saved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            (root / "artifacts").mkdir()
            header = "---\ntitle: A guide\nslug: a-guide\ncategory: financing\n---\n"
            article = root / "artifacts" / "draft.md"
            article.write_text(header + "\n# A guide\n\nBody.\n", encoding="utf-8")
            (root / "tasks.md").write_text(board_card(attachment="artifacts/draft.md"), encoding="utf-8")

            result = ceo_actions.save_article_edit(
                root, "TASK-1", header + "\n# A guide\n\nBody, edited.\n", "ceo@example.test"
            )

            self.assertTrue(result["ok"])
            self.assertIn("Body, edited.", article.read_text(encoding="utf-8"))

    def test_page_modules_import_in_both_orders(self):
        for first, second in (("ceo_console", "ceo_page"), ("ceo_page", "ceo_console")):
            importlib.reload(importlib.import_module(first))
            importlib.reload(importlib.import_module(second))
        self.assertNotIn("ceo_console", Path(ceo_console.__file__).with_name("ceo_page.py").read_text(encoding="utf-8"))

    def test_page_has_no_external_asset_links(self):
        page = render_page().decode()
        self.assertNotRegex(page, r'''(?:src|href)=["'](?:https?:)?//''')


class RenamingAnArticleMovesEveryCopyOfTheTitle(unittest.TestCase):
    """A blog title was written down four times and kept in step nowhere.

    The card heading, the card's mirrored `Title` field, the front-matter `title:`
    the published page's layout reads, and the article's own H1. A rename that moves
    some of them is how the console and the live site come to disagree, so these
    assert on all four and on the two that must not move: the slug, which is the
    page's address, and `meta_title`, which is a different sentence on purpose.
    """

    ARTICLE = (
        "---\ntitle: A guide\nmeta_title: Search title stays put\n"
        "meta_description: A description.\nslug: a-guide\ncategory: financing\n"
        "audience: EV owners\nsource_urls: https://example.org/one\n---\n\n"
        "# A guide\n\nBody.\n"
    )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        (self.root / "artifacts").mkdir()
        self.article = self.root / "artifacts" / "TASK-1-content.md"
        self.article.write_text(self.ARTICLE, encoding="utf-8")
        (self.root / "tasks.md").write_text(
            board_card(attachment="artifacts/TASK-1-content.md"), encoding="utf-8"
        )

    def card(self):
        import dashboard_server

        text = (self.root / "tasks.md").read_text(encoding="utf-8")
        return next(item for item in dashboard_server.parse_tasks(text) if item["id"] == "TASK-1")

    def rename(self, title, editor="ceo@example.test"):
        return ceo_actions.rename_article(self.root, "TASK-1", title, editor)

    def test_one_rename_moves_the_heading_the_field_the_header_and_the_h1(self):
        self.rename("Battery planning for Delhi NCR")

        board = (self.root / "tasks.md").read_text(encoding="utf-8")
        article = self.article.read_text(encoding="utf-8")
        self.assertIn("### TASK-1 — Battery planning for Delhi NCR", board)
        self.assertIn("- Title: Battery planning for Delhi NCR", board)
        self.assertIn("title: Battery planning for Delhi NCR", article)
        self.assertIn("# Battery planning for Delhi NCR", article)
        # And the console reads back the new one, through the parser it really uses.
        self.assertEqual(self.card()["title"], "Battery planning for Delhi NCR")

    def test_a_rename_leaves_the_address_and_the_search_title_alone(self):
        self.rename("A completely different headline")

        article = self.article.read_text(encoding="utf-8")
        self.assertIn("slug: a-guide", article, "the page's URL moved")
        self.assertIn("meta_title: Search title stays put", article)

    def test_a_rename_keeps_the_version_it_replaced_and_names_who_did_it(self):
        result = self.rename("A new headline", editor="sanchit@example.test")

        archive = self.root / "artifacts" / "TASK-1-content.r1.md"
        self.assertEqual(result["archived_as"], "TASK-1-content.r1.md")
        self.assertEqual(archive.read_text(encoding="utf-8"), self.ARTICLE)
        self.assertIn("sanchit@example.test", self.card()["approval_thread_1_edit"])

    def test_the_renamed_article_still_satisfies_the_publisher(self):
        from cmo_runtime.content_flow import _frontmatter

        self.rename("A headline the publisher must accept")

        fields, _body = _frontmatter(self.article.read_text(encoding="utf-8"))
        self.assertEqual(fields["title"], "A headline the publisher must accept")
        self.assertEqual(fields["slug"], "a-guide")

    def test_an_article_a_decision_covers_cannot_be_renamed(self):
        """The headline is part of what was approved, so it is closed with the rest."""
        from cmo_runtime.task_file import TaskFileError

        with patch.object(ceo_actions, "_decision_that_holds", return_value={"decision": "approve"}):
            with self.assertRaises(TaskFileError) as raised:
                self.rename("A new headline")

        self.assertIn("already carries a human decision", str(raised.exception))
        self.assertEqual(self.article.read_text(encoding="utf-8"), self.ARTICLE)

    def test_a_title_that_would_not_read_back_as_typed_is_refused(self):
        """The header is not YAML.

        `ceo_reader` strips surrounding quotes on the way in and the publisher does
        not, so a quoted title would show bare here and publish with the quotes on.
        Refusing beats silently picking one of the two readings.
        """
        from cmo_runtime.task_file import TaskFileError

        for bad, reason in (
            ("", "empty"),
            ("   ", "blank"),
            ('"Quoted"', "quoted"),
            ("x" * 181, "over the 180-character cap"),
        ):
            with self.subTest(reason=reason), self.assertRaises(TaskFileError):
                self.rename(bad)
        self.assertEqual(self.article.read_text(encoding="utf-8"), self.ARTICLE)

    def test_renaming_to_the_title_it_already_has_everywhere_is_refused(self):
        """Refused only once every copy agrees.

        The fixture is a card that has already drifted — the board says
        `Content idea`, the article says `A guide` — which is exactly the state this
        control exists to fix. So renaming to the article's own title is real work
        the first time and a no-op the second.
        """
        from cmo_runtime.task_file import TaskFileError

        self.assertEqual(self.card()["title"], "Content idea")
        self.rename("A guide")
        self.assertEqual(self.card()["title"], "A guide")

        with self.assertRaises(TaskFileError) as raised:
            self.rename("A guide")
        self.assertIn("unchanged", str(raised.exception))

    def test_a_rename_that_wrote_the_article_and_not_the_card_can_be_finished(self):
        """The two writes are two files and cannot be one transaction.

        So the failure has to be recoverable rather than merely reported: the article
        already says the new title, and asking only "did the article change" would
        refuse the retry and leave the card on the old one for good.
        """
        from cmo_runtime.task_file import TaskFile, TaskFileError

        with patch.object(TaskFile, "set_card_title", side_effect=OSError("disk full")):
            with self.assertRaises(TaskFileError) as raised:
                self.rename("Half a rename")
        self.assertIn("board card was not", str(raised.exception))
        self.assertIn("title: Half a rename", self.article.read_text(encoding="utf-8"))
        self.assertEqual(self.card()["title"], "Content idea")

        result = self.rename("Half a rename")

        self.assertEqual(self.card()["title"], "Half a rename")
        # The article was already right, so finishing the card mints no second
        # revision — a retry must not cost a version.
        self.assertNotIn("revision_round", result)
        self.assertFalse((self.root / "artifacts" / "TASK-1-content.r2.md").exists())

    def test_an_article_with_no_h1_does_not_grow_one(self):
        """Preserving what the writer left is not the same as inventing it."""
        source = "---\ntitle: Old\nslug: s\n---\n\nProse with no heading.\n"

        renamed = ceo_actions.retitle_markdown(source, "New")

        self.assertIn("title: New", renamed)
        self.assertNotIn("# New", renamed)

    def test_only_the_first_h1_is_the_headline(self):
        source = "---\ntitle: Old\n---\n\n# Old\n\n## Section\n\n# Later heading\n"

        renamed = ceo_actions.retitle_markdown(source, "New")

        self.assertEqual(
            [line for line in renamed.splitlines() if line.startswith("#")],
            ["# New", "## Section", "# Later heading"],
        )

if __name__ == "__main__":
    unittest.main()
