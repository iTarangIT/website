"""Invariants 1, 2 and 3 — the reader, and the edit that makes a revision.

These tests exist because the previous reader lived in a JavaScript string inside
ceo_script.py. Nothing ever executed it, so no suite could see that it printed
table pipes and literal `**`. Rendering happens in Python now, and every rule
below asserts on the HTML the console actually serves.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ceo_actions
import ceo_artifacts
import ceo_reader
import dashboard_server

ARTICLE = """---
title: A Local EV Battery Strategy
slug: local-ev-battery
category: financing
---

# A Local EV Battery Strategy

A person combining a city name with a battery term wants **one decision** made
easier, not a *general* description. See [the calculator](/emi-calculator).

{{image:decision-path|How a city page moves a visitor to a verified next step.}}

## City-to-intent pilot matrix

| City | Battery price | EMI |
|---|---:|:---:|
| Delhi | **Hypothesis:** price explainer | calculator journey |
| Jaipur | **Hypothesis:** replacement | calculator journey |

> Every mapping is a hypothesis pending validation.

1. Define one decision.
2. Explain the inputs.

- first bullet
- second bullet

---

## Decision bullets:

- **Start with a limited test.** Review Search Console first.

## Claims requiring human verification

Confirm the calculator's city list before publication.

## Proposed internal links and call to action — not published

Proposed links include the EMI calculator.

## Source-backed outline

- **Local opportunity:** the calculator lists cities.

## Sources and dates

- [India EV Report](https://www.bain.com/x) — accessed 10 August 2026.
"""

SLOTS = [
    {
        "id": "decision-path",
        "caption": "How a city page moves a visitor to a verified next step.",
        "bound": True,
        "url": "/ceo/image?task=TASK-1&slot=decision-path",
        "filename": "d.svg",
    }
]


class FrontMatterNeverRenders(unittest.TestCase):
    """Invariant 2, first half."""

    def test_front_matter_is_stripped_from_the_fragment(self) -> None:
        html = ceo_reader.render_markdown_fragment(ARTICLE, slots=SLOTS)

        for leaked in ("slug:", "category:", "meta_title", "---\ntitle"):
            self.assertNotIn(leaked, html)
        self.assertNotIn("<p>---</p>", html)

    def test_metadata_is_returned_separately_rather_than_discarded(self) -> None:
        metadata, body = ceo_reader.strip_front_matter(ARTICLE)

        self.assertEqual(metadata["slug"], "local-ev-battery")
        self.assertTrue(body.lstrip().startswith("# A Local EV Battery Strategy"))

    def test_a_body_without_front_matter_is_left_alone(self) -> None:
        metadata, body = ceo_reader.strip_front_matter("# Title\n\nBody.\n")

        self.assertEqual(metadata, {})
        self.assertEqual(body, "# Title\n\nBody.\n")

    def test_a_horizontal_rule_is_not_mistaken_for_front_matter(self) -> None:
        html = ceo_reader.render_markdown_fragment("Before.\n\n---\n\nAfter.\n")

        self.assertIn("<hr>", html)
        self.assertIn("<p>Before.</p>", html)
        self.assertIn("<p>After.</p>", html)

    def test_the_document_route_strips_front_matter_too(self) -> None:
        document = dashboard_server._render_markdown(ARTICLE, "A Local EV Battery Strategy").decode()

        self.assertNotIn("slug:", document)
        self.assertIn("<table", document)


class MarkdownBecomesHtml(unittest.TestCase):
    """Invariant 1 — no raw Markdown reaches the page."""

    def setUp(self) -> None:
        self.html = ceo_reader.render_markdown_fragment(ARTICLE, slots=SLOTS)
        self.prose = ceo_reader.render_article(ARTICLE, SLOTS)["html"]

    def test_a_table_renders_as_a_table_with_header_and_alignment(self) -> None:
        self.assertIn("<table", self.prose)
        self.assertIn('<th scope="col">City</th>', self.prose)
        self.assertIn('<th scope="col" class="align-right">Battery price</th>', self.prose)
        self.assertIn('<th scope="col" class="align-center">EMI</th>', self.prose)
        self.assertIn("<td>Delhi</td>", self.prose)
        self.assertEqual(self.prose.count("<tr>"), 3)

    def test_no_table_pipe_survives_as_text(self) -> None:
        self.assertNotIn("|", self.prose)
        self.assertNotIn("---|", self.html)

    def test_bold_and_italic_become_elements_not_asterisks(self) -> None:
        self.assertIn("<strong>one decision</strong>", self.prose)
        self.assertIn("<em>general</em>", self.prose)
        self.assertNotIn("**", self.prose)

    def test_bold_inside_a_table_cell_renders(self) -> None:
        self.assertIn('<td class="align-right"><strong>Hypothesis:</strong> price explainer</td>', self.prose)

    def test_headings_render_at_their_level(self) -> None:
        self.assertIn("<h1>A Local EV Battery Strategy</h1>", self.prose)
        self.assertIn("<h2>City-to-intent pilot matrix</h2>", self.prose)
        self.assertNotIn("# A Local", self.prose)

    def test_lists_quotes_and_rules_render(self) -> None:
        self.assertIn("<ol><li>Define one decision.</li>", self.prose)
        self.assertIn("<ul><li>first bullet</li><li>second bullet</li></ul>", self.prose)
        self.assertIn("<blockquote><p>Every mapping is a hypothesis", self.prose)
        self.assertIn("<hr>", self.prose)

    def test_links_render_and_external_links_are_safe(self) -> None:
        self.assertIn('<a href="/emi-calculator">the calculator</a>', self.prose)
        notes = ceo_reader.render_article(ARTICLE, SLOTS)
        self.assertIn('rel="noopener noreferrer"', notes["html"])

    def test_escaping_runs_before_markup_so_html_cannot_be_injected(self) -> None:
        html = ceo_reader.render_markdown_fragment(
            "<script>alert(1)</script>\n\n| a |\n|---|\n| <img src=x onerror=y> |\n"
        )

        self.assertNotIn("<script>", html)
        self.assertNotIn("<img", html)
        self.assertIn("&lt;script&gt;", html)

    def test_a_javascript_link_target_is_refused(self) -> None:
        html = ceo_reader.render_markdown_fragment("[click](javascript:alert(1))")

        self.assertNotIn("<a ", html)
        self.assertNotIn("javascript", html)
        self.assertIn("click", html)
        self.assertNotIn("[click]", html)

    def test_a_backslash_escape_yields_the_literal_character(self) -> None:
        html = ceo_reader.render_markdown_fragment(r"A title \|\| Capital Calculus and \*not bold\*.")

        self.assertIn("A title || Capital Calculus and *not bold*.", html)
        self.assertNotIn("\\|", html)

    def test_a_remote_image_keeps_its_alt_text_and_makes_no_request(self) -> None:
        html = ceo_reader.render_markdown_fragment("![Bain logo](https://www.bain.com/logo.svg)")

        self.assertIn("Bain logo", html)
        self.assertNotIn("https://www.bain.com", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("![", html)

    def test_fenced_code_is_preserved_verbatim(self) -> None:
        html = ceo_reader.render_markdown_fragment("```py\n**not bold**\n```\n")

        self.assertIn("<pre><code class=\"language-py\">**not bold**</code></pre>", html)


class OneCaptionPerFigure(unittest.TestCase):
    """Invariant 1 — the duplicate caption."""

    def test_a_bound_slot_emits_exactly_one_caption(self) -> None:
        html = ceo_reader.render_markdown_fragment(ARTICLE, slots=SLOTS)

        self.assertEqual(html.count("<figcaption"), 1)
        self.assertEqual(html.count(SLOTS[0]["caption"]), 1)

    def test_the_loading_placeholder_does_not_repeat_the_caption(self) -> None:
        html = ceo_reader.render_markdown_fragment(ARTICLE, slots=SLOTS)

        self.assertIn("Loading diagram…", html)
        self.assertIn('data-image-url="/ceo/image?task=TASK-1&amp;slot=decision-path"', html)

    def test_an_unbound_slot_says_so_once(self) -> None:
        html = ceo_reader.render_markdown_fragment(
            "{{image:missing|A caption.}}", slots=[{"id": "other", "caption": "x", "bound": False}]
        )

        self.assertEqual(html.count("<figcaption"), 1)
        self.assertIn("No image is bound yet", html)

    def test_the_figure_is_labelled_by_its_caption(self) -> None:
        html = ceo_reader.render_markdown_fragment(ARTICLE, slots=SLOTS)

        self.assertIn('aria-labelledby="figcap-decision-path"', html)
        self.assertIn('<figcaption id="figcap-decision-path">', html)


class ReviewScaffoldingIsCollapsed(unittest.TestCase):
    """Invariant 2, second half."""

    def setUp(self) -> None:
        self.rendered = ceo_reader.render_article(ARTICLE, SLOTS)

    def test_scaffolding_headings_leave_the_prose(self) -> None:
        for heading in (
            "Decision bullets",
            "Claims requiring human verification",
            "Proposed internal links",
            "Source-backed outline",
        ):
            self.assertNotIn(heading, self.rendered["html"])

    def test_scaffolding_headings_arrive_in_the_notes_in_order(self) -> None:
        self.assertEqual(
            self.rendered["review_note_titles"],
            [
                "Decision bullets",
                "Claims requiring human verification",
                "Proposed internal links and call to action — not published",
                "Source-backed outline",
            ],
        )
        self.assertIn("Start with a limited test.", self.rendered["review_notes_html"])

    def test_a_scaffolding_section_takes_its_body_with_it(self) -> None:
        self.assertNotIn("Confirm the calculator", self.rendered["html"])
        self.assertIn("Confirm the calculator", self.rendered["review_notes_html"])

    def test_real_prose_after_a_scaffolding_section_returns_to_the_article(self) -> None:
        self.assertIn("Sources and dates", self.rendered["html"])
        self.assertIn("India EV Report", self.rendered["html"])
        self.assertNotIn("Sources and dates", self.rendered["review_notes_html"])

    def test_an_article_without_scaffolding_produces_no_notes(self) -> None:
        rendered = ceo_reader.render_article("# Title\n\nJust prose.\n")

        self.assertEqual(rendered["review_notes_html"], "")
        self.assertEqual(rendered["review_note_titles"], [])


def _board(task_id: str = "TASK-1", attachment: str = "artifacts/TASK-1-content.md") -> str:
    return f"""# Board

## Backlog

## In Progress

## CMO Review

## Human Approval

### {task_id} — Content idea
- ID: {task_id}
- Title: Content idea
- Owner: content
- Skill: content
- Status: Human Approval
- Priority: high
- Attachment: {attachment}
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z

## Completed
"""


class ConsoleEditMakesARevision(unittest.TestCase):
    """Invariant 3."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        (self.root / "artifacts").mkdir()
        self.article = self.root / "artifacts" / "TASK-1-content.md"
        self.article.write_text(ARTICLE, encoding="utf-8")
        (self.root / "tasks.md").write_text(_board(), encoding="utf-8")

    def edit(self, text: str, editor: str = "ceo@example.test") -> dict[str, object]:
        return ceo_actions.save_article_edit(self.root, "TASK-1", text, editor)

    def test_an_edit_preserves_the_previous_version_and_advances_the_round(self) -> None:
        result = self.edit(ARTICLE.replace("wants **one decision**", "needs **one decision**"))

        archive = self.root / "artifacts" / "TASK-1-content.r1.md"
        self.assertEqual(result["revision_round"], 1)
        self.assertEqual(result["archived_as"], "TASK-1-content.r1.md")
        self.assertEqual(archive.read_text(encoding="utf-8"), ARTICLE)
        self.assertIn("needs **one decision**", self.article.read_text(encoding="utf-8"))

    def test_a_second_edit_archives_beside_the_first_and_never_overwrites_it(self) -> None:
        first = ARTICLE.replace("wants", "needs")
        self.edit(first)
        self.edit(first.replace("needs", "requires"))

        self.assertEqual(
            (self.root / "artifacts" / "TASK-1-content.r1.md").read_text(encoding="utf-8"), ARTICLE
        )
        self.assertIn(
            "needs", (self.root / "artifacts" / "TASK-1-content.r2.md").read_text(encoding="utf-8")
        )

    def test_an_edit_is_recorded_in_the_thread_as_an_edit(self) -> None:
        self.edit(ARTICLE.replace("wants", "needs"), editor="sanchit@itarang.com")

        board = (self.root / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("- Revision round: 1", board)
        self.assertIn("- Approval thread 1 edit: sanchit@itarang.com edited the article", board)
        task = next(item for item in dashboard_server.parse_tasks(board) if item["id"] == "TASK-1")
        events = dashboard_server.approval_thread(task)
        self.assertEqual([event["type"] for event in events], ["edit"])

    def test_an_edit_writes_no_decision(self) -> None:
        self.edit(ARTICLE.replace("wants", "needs"))

        self.assertFalse((self.root / "state" / "human-approvals.json").exists())
        self.assertFalse((self.root / "state" / "decisions.db").exists())
        board = (self.root / "tasks.md").read_text(encoding="utf-8")
        self.assertNotIn("rejection", board)
        self.assertNotIn("Decision:", board)

    def test_an_empty_or_unchanged_edit_is_refused_without_touching_the_article(self) -> None:
        from cmo_runtime.task_file import TaskFileError

        before = self.article.read_bytes()
        for payload in ("", "   \n", ARTICLE):
            with self.assertRaises(TaskFileError):
                self.edit(payload)
        self.assertEqual(self.article.read_bytes(), before)
        self.assertFalse((self.root / "artifacts" / "TASK-1-content.r1.md").exists())

    def current_fingerprint(self) -> str:
        import console_board

        task = ceo_actions._task(self.root / "tasks.md", "TASK-1")
        return console_board.publish_fingerprint(task, self.root)

    def test_an_edit_after_a_human_decision_is_refused(self) -> None:
        """A decision that still covers the article closes it. That rule stands."""
        from cmo_runtime.task_file import TaskFileError

        record = {"decision": "approve", "approver_id": "ceo@example.test",
                  "timestamp": "2026-08-12T09:00:00Z",
                  "publish_fingerprint": self.current_fingerprint()}
        with patch("cmo_runtime.decisions.decision_record", return_value=record):
            with self.assertRaisesRegex(TaskFileError, "already carries a human decision"):
                self.edit(ARTICLE.replace("wants", "needs"))
        self.assertEqual(self.article.read_text(encoding="utf-8"), ARTICLE)

    def test_an_edit_is_allowed_again_once_the_decision_has_gone_stale(self) -> None:
        """Approve-again alone would be a trap.

        Re-read an article whose approval no longer covers it, find something
        wrong, and the only control on screen approves it anyway. The approval
        covers nothing, so nothing is weakened by reopening the editor.
        """
        record = {"decision": "approve", "approver_id": "ceo@example.test",
                  "timestamp": "2026-08-12T09:00:00Z", "publish_fingerprint": "f" * 64}
        with patch("cmo_runtime.decisions.decision_record", return_value=record):
            result = self.edit(ARTICLE.replace("wants", "needs"))

        self.assertEqual(result["revision_round"], 1)
        self.assertIn("needs", self.article.read_text(encoding="utf-8"))

    def test_an_oversized_edit_is_refused(self) -> None:
        from cmo_runtime.task_file import TaskFileError

        with self.assertRaisesRegex(TaskFileError, "512 KB"):
            self.edit("x" * (ceo_actions.MAX_ARTICLE_BYTES + 1))

    def test_a_card_without_an_article_cannot_be_edited(self) -> None:
        from cmo_runtime.task_file import TaskFileError

        (self.root / "tasks.md").write_text(_board(attachment="none"), encoding="utf-8")

        with self.assertRaisesRegex(TaskFileError, "no article to edit"):
            self.edit("# New\n")

    def test_the_edited_article_is_what_the_reader_renders_next(self) -> None:
        self.edit(ARTICLE.replace("wants **one decision**", "needs **two decisions**"))

        task = next(
            item
            for item in dashboard_server.parse_tasks((self.root / "tasks.md").read_text(encoding="utf-8"))
            if item["id"] == "TASK-1"
        )
        payload = ceo_artifacts.artifact_payload(task, self.article, self.root)
        self.assertIn("<strong>two decisions</strong>", payload["html"])
        self.assertEqual([item["round"] for item in payload["revisions"]], [1])


class PayloadCarriesRenderedHtml(unittest.TestCase):
    def test_artifact_payload_renders_html_and_notes_for_the_browser(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "artifacts").mkdir()
            article = root / "artifacts" / "TASK-1-content.md"
            article.write_text(ARTICLE, encoding="utf-8")
            payload = ceo_artifacts.artifact_payload({"id": "TASK-1"}, article, root)

        self.assertIn("<table", payload["html"])
        self.assertIn("<strong>", payload["html"])
        self.assertNotIn("slug:", payload["text"])
        self.assertIn("Decision bullets", payload["review_notes_html"])
        self.assertNotIn("Decision bullets", payload["html"])
        self.assertGreater(payload["word_count"], 0)


class NoRawMarkdownEscapesTheReader(unittest.TestCase):
    """A regression net over every artifact this profile actually holds."""

    def test_every_committed_artifact_renders_without_raw_markdown(self) -> None:
        artifacts = sorted(
            path
            for path in (dashboard_server.PROFILE_DIR / "artifacts").glob("*.md")
            if path.is_file()
        )
        if not artifacts:
            self.skipTest("no artifacts in this profile")
        for path in artifacts:
            with self.subTest(artifact=path.name):
                text = path.read_text(encoding="utf-8", errors="replace")
                html = ceo_reader.render_markdown_fragment(text)
                self.assertNotIn("**", html, "bold survived as asterisks")
                # A literal pipe in prose is fine; a table row rendered as prose is not.
                self.assertNotRegex(html, r"<(?:p|li)>\s*\|", "a table row rendered as text")
                self.assertNotRegex(html, r"\|\s*</(?:p|li)>", "a table row rendered as text")
                self.assertNotRegex(html, r"<p>#{1,6}\s", "a heading rendered as a paragraph")
                self.assertNotIn("<p>---</p>", html)
                self.assertNotIn("<p></p>", html)
                if re.search(r"(?m)^\s*\|?\s*:?-{3,}:?\s*\|", text):
                    self.assertIn("<table", html, "a Markdown table did not become a table")


if __name__ == "__main__":
    unittest.main()
