import io
import json
import re
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import analytics_readers
import ceo_actions
import ceo_console
import ceo_artifacts
import console_board
from ceo_page import render_page
from cmo_runtime.decisions import DecisionStore
from cmo_runtime.task_file import TaskFileError


def empty_board() -> str:
    return """# iTarang CMO Task Board

## Backlog

## In Progress

## CMO Review

## Human Approval

## Completed
"""


def card_board(
    *,
    task_id: str = "TASK-001",
    title: str = "Battery article",
    section: str = "Human Approval",
    attachment: str = "artifacts/TASK-001-blog.md",
    extra: str = "",
) -> str:
    status = section
    return f"""# iTarang CMO Task Board

## Backlog

## In Progress

## CMO Review

## Human Approval

{f'''### {task_id} — {title}

- ID: {task_id}
- Title: {title}
- Owner: content
- Skill: content
- Priority: high
- Status: {status}
- Description: A sourced battery explainer.
- Attachment: {attachment}
- Metric: Organic sessions to the article
- Tag: action to be taken by: human
- Topic stage: proposed
- Revision round: 0
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
{extra}
''' if section == 'Human Approval' else ''}
## Completed
"""


class Handler:
    def __init__(self, path: str, body=None, raw: bytes | None = None, filename: str = ""):
        payload = raw if raw is not None else json.dumps(body or {}).encode()
        self.path = path
        self.headers = {
            "Authorization": "Bearer test-token",
            "Content-Length": str(len(payload)),
        }
        if filename:
            self.headers["X-Filename"] = filename
        self.rfile = io.BytesIO(payload)
        self.wfile = io.BytesIO()
        self.status = None
        self.response_headers = {}

    def send_response(self, status):
        self.status = int(status)

    def send_header(self, name, value):
        self.response_headers[name] = value

    def end_headers(self):
        pass


class CeoStageBTests(unittest.TestCase):
    def make_root(self, board_text: str) -> tuple[tempfile.TemporaryDirectory, Path]:
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        (root / "tasks.md").write_text(board_text, encoding="utf-8")
        (root / "state").mkdir()
        (root / "artifacts").mkdir()
        (root / "logs").mkdir()
        return directory, root

    def test_the_console_has_no_direct_board_writer_for_topics(self):
        # `add_topics` and `set_topic_stage` turned a typed subject straight into a
        # writable card. That is the behaviour the proposal flow replaced.
        self.assertFalse(hasattr(ceo_actions, "add_topics"))
        self.assertFalse(hasattr(ceo_actions, "set_topic_stage"))
        self.assertFalse(hasattr(ceo_actions, "greenlight_topic"))

    def test_only_artifact_backed_cards_are_blogs_and_never_topics(self):
        directory, root = self.make_root(card_board())
        self.addCleanup(directory.cleanup)
        (root / "artifacts" / "TASK-001-blog.md").write_text("# Draft\n\nBody", encoding="utf-8")
        value = console_board.read_board(root / "tasks.md", root)
        self.assertEqual([item["id"] for item in value["blogs"]], ["TASK-001"])
        self.assertNotIn("topics", value, "the board no longer produces a topics list")
        (root / "artifacts" / "TASK-001-blog.md").unlink()
        value = console_board.read_board(root / "tasks.md", root)
        # Without an artifact the card is simply not a blog; it is not a topic either.
        self.assertEqual(value["blogs"], [])

    def test_article_slots_render_unbound_then_bind_to_uploaded_artifact_image(self):
        directory, root = self.make_root(card_board())
        self.addCleanup(directory.cleanup)
        artifact = root / "artifacts" / "TASK-001-blog.md"
        artifact.write_text("# Draft\n\n{{image:flow-chart|Battery data flow}}", encoding="utf-8")
        task = console_board.read_board(root / "tasks.md", root)["blogs"][0]
        self.assertFalse(task["article"]["image_slots"][0]["bound"])
        destination = ceo_artifacts.save_upload(root, "TASK-001", "flow-chart", "flow.png", b"png-bytes")
        self.assertTrue(destination.is_file())
        task = console_board.read_board(root / "tasks.md", root)["blogs"][0]
        slot = task["article"]["image_slots"][0]
        self.assertTrue(slot["bound"])
        self.assertEqual(slot["url"], "/ceo/image?task=TASK-001&slot=flow-chart")

    def test_upload_rejects_svg_and_files_over_five_mb(self):
        directory, root = self.make_root(card_board())
        self.addCleanup(directory.cleanup)
        with self.assertRaisesRegex(TaskFileError, "SVG is not allowed"):
            ceo_artifacts.save_upload(root, "TASK-001", "hero", "hero.svg", b"<svg/>")
        with self.assertRaisesRegex(TaskFileError, "5 MB"):
            ceo_artifacts.save_upload(root, "TASK-001", "hero", "hero.png", b"x" * (ceo_artifacts.MAX_UPLOAD_BYTES + 1))

    def test_revision_stays_in_lane_increments_and_is_refused_after_decision(self):
        directory, root = self.make_root(card_board(extra="- Change type: website\n- Commit hash(es): abc1234\n"))
        self.addCleanup(directory.cleanup)
        first = ceo_actions.request_revision(root, "TASK-001", "Clarify the evidence.", "ceo@test")
        second = ceo_actions.request_revision(root, "TASK-001", "Add the source link.", "ceo@test")
        self.assertEqual((first, second), (1, 2))
        text = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("## Human Approval\n\n### TASK-001", text)
        DecisionStore(root).decide(
            "TASK-001",
            "approve",
            surface="dashboard",
            approver_id="ceo@test",
            card_commit_sha="abc1234",
            commit_sha="abc1234",
        )
        with self.assertRaisesRegex(TaskFileError, "decision already exists"):
            ceo_actions.request_revision(root, "TASK-001", "Too late.", "ceo@test")

    def test_row_approval_status_comes_from_decision_store(self):
        directory, root = self.make_root(card_board(extra="- Change type: website\n- Commit hash(es): abc1234\n"))
        self.addCleanup(directory.cleanup)
        (root / "artifacts" / "TASK-001-blog.md").write_text("# Draft", encoding="utf-8")
        self.assertFalse(console_board.read_board(root / "tasks.md", root)["blogs"][0]["decision_approved"])
        DecisionStore(root).decide(
            "TASK-001",
            "approve",
            surface="dashboard",
            approver_id="ceo@test",
            card_commit_sha="abc1234",
            commit_sha="abc1234",
        )
        item = console_board.read_board(root / "tasks.md", root)["blogs"][0]
        self.assertTrue(item["decision_approved"])
        self.assertEqual(item["decision_status"], "approved")

    def test_watchlist_never_changes_the_board(self):
        directory, root = self.make_root(empty_board())
        self.addCleanup(directory.cleanup)
        before = (root / "tasks.md").read_bytes()
        self.assertEqual(ceo_actions.update_watchlist(root, "battery passport", "add"), ["battery passport"])
        self.assertEqual((root / "tasks.md").read_bytes(), before)
        self.assertEqual(ceo_actions.update_watchlist(root, "battery passport", "remove"), [])
        self.assertEqual((root / "tasks.md").read_bytes(), before)

    def test_unconnected_x_and_facebook_collectors_emit_no_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            x_file = root / "x.json"
            facebook_file = root / "facebook.json"
            x_file.write_text('[{"title":"X topic"}]', encoding="utf-8")
            facebook_file.write_text('[{"title":"Facebook topic"}]', encoding="utf-8")
            with patch.object(analytics_readers, "X_TRENDS_FILE", x_file), patch.object(
                analytics_readers, "FACEBOOK_TRENDS_FILE", facebook_file
            ), patch.object(
                analytics_readers, "google_search_trends", return_value=([{"title": "Search topic", "source": "Google Search"}], "")
            ), patch.dict(os.environ, {}, clear=True):
                rows, messages = analytics_readers.trending_rows()
        self.assertEqual([row["source"] for row in rows], ["Google Search"])
        self.assertIn("X is not connected.", messages)
        self.assertIn("Facebook is not connected.", messages)

    def test_connected_collector_files_keep_their_own_source_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            x_file = root / "x.json"
            facebook_file = root / "facebook.json"
            x_file.write_text('[{"title":"X topic"}]', encoding="utf-8")
            facebook_file.write_text('[{"title":"Facebook topic"}]', encoding="utf-8")
            with patch.object(analytics_readers, "X_TRENDS_FILE", x_file), patch.object(
                analytics_readers, "FACEBOOK_TRENDS_FILE", facebook_file
            ), patch.object(analytics_readers, "google_search_trends", return_value=([], "")), patch.dict(
                os.environ,
                {"X_BEARER_TOKEN": "test", "FACEBOOK_ACCESS_TOKEN": "test", "FACEBOOK_PAGE_ID": "page"},
                clear=True,
            ):
                rows, _messages = analytics_readers.trending_rows()
        self.assertEqual([row["source"] for row in rows], ["X", "Facebook"])

    def test_ga4_absent_is_not_connected_never_zero_or_decline(self):
        with patch.dict(os.environ, {}, clear=True):
            value = analytics_readers.ga4_summary()
        self.assertEqual(value["status"], "not_connected")
        self.assertEqual(value["message"], "Google Analytics is not connected yet")
        self.assertTrue(all(metric is None for metric in value["metrics"].values()))
        self.assertTrue(all(metric is None for metric in value["deltas"].values()))
        self.assertNotIn("decline", json.dumps(value).casefold())

    def test_ga4_has_no_delta_when_the_previous_window_has_no_data(self):
        current = {
            "rows": [{
                "metricValues": [
                    {"value": "8"}, {"value": "12"}, {"value": "20"}, {"value": "0.5"}
                ]
            }]
        }
        with patch.dict(
            os.environ,
            {"GA4_CREDENTIALS_PATH": "/test/credentials.json", "GA4_PROPERTY_ID": "123"},
            clear=False,
        ), patch.object(analytics_readers, "_ga4_request", side_effect=[current, {"rows": []}]):
            value = analytics_readers._fetch_ga4(28, "all")
        self.assertEqual(value["metrics"]["sessions"], 12)
        self.assertIsNone(value["previous"]["sessions"])
        self.assertIsNone(value["deltas"]["sessions"])

    def test_gate_two_pipeline_state_is_rendered_for_the_human(self):
        extra = """- Change type: website
- Branch: cmo-changes
- Commit hash(es): abc123
- Commit URL: https://example.test/commit/abc123
- Preview URL: https://preview.example.test
- Metrics evidence: state/website-metrics/TASK-001
- Change status: awaiting Gate 2
"""
        directory, root = self.make_root(card_board(extra=extra))
        self.addCleanup(directory.cleanup)
        (root / "artifacts" / "TASK-001-blog.md").write_text("# Draft", encoding="utf-8")
        pipeline = console_board.read_board(root / "tasks.md", root)["blogs"][0]["publishing_pipeline"]
        self.assertIn("human to merge", pipeline["waiting_on"])
        self.assertEqual(pipeline["branch"], "cmo-changes")
        self.assertEqual(pipeline["commit"], "abc123")
        # SOUL.md section 12 clause 4 now permits a console publish control. The
        # control is inert on its own: it carries no authority, and every refusal
        # that guards it is proved separately in test_ceo_publish.py.
        page = render_page().decode("utf-8")
        self.assertIn("data-publish", page)
        self.assertIn("Publish to website", page)

    def test_ceo_page_has_four_nested_tabs_pdf_and_one_login_key_set(self):
        page = render_page().decode("utf-8")
        for label in ("Read", "Impact", "Discussion", "Files", "Download Markdown",
                      "Print or save as PDF"):
            self.assertIn(label, page)
        for key in ("cmo_token", "cmo_email", "cmo_role"):
            self.assertIn(key, page)
        self.assertNotIn("login-form", page)
        self.assertIn("api(frame.dataset.imageUrl,{raw:true})", page)
        # There is no blind reload left to hold. A background update is driven by
        # the version token, it stands down only for an action still in flight,
        # and what it must not disturb is proved in test_console_live.py.
        self.assertIn("if(quiet&&busy)return", page)
        self.assertIn("/ceo/api/version", page)
        self.assertNotIn("setInterval(()=>refresh(true),60000)", page)

    def test_every_ceo_post_route_is_covered_by_the_preview_test(self):
        # A new POST route must be added to the list below, or this fails.
        # Everything after the preview guard in dispatch() is POST-only handling.
        source = Path(ceo_console.__file__).read_text(encoding="utf-8")
        source = source.split('CMO_DASHBOARD_PREVIEW', 1)[1]
        declared = set(re.findall(r'path == "(/ceo/api/[a-z/-]+)"', source))
        declared |= {
            route
            for block in re.findall(r"path in \{([^}]+)\}", source)
            for route in re.findall(r'"(/ceo/api/[a-z/-]+)"', block)
        }
        covered = {path.split("?", 1)[0] for path, *_ in self.preview_routes()}
        self.assertEqual(declared - covered, set(), "a POST route escapes the preview-mode test")

    def preview_routes(self):
        return [
            ("/ceo/api/propose", {"subject": "battery data"}, None, ""),
            ("/ceo/api/proposal/approve", {"proposal_id": 1}, None, ""),
            ("/ceo/api/proposal/suggest", {"proposal_id": 1, "comment": "narrower"}, None, ""),
            ("/ceo/api/proposal/reject", {"proposal_id": 1, "reason": "covered"}, None, ""),
            ("/ceo/api/proposal/undo-rejection", {"proposal_id": 1}, None, ""),
            ("/ceo/api/watchlist", {"keyword": "battery", "action": "add"}, None, ""),
            ("/ceo/api/revision", {"task_id": "TASK-001", "comment": "change"}, None, ""),
            ("/ceo/api/decision", {"task_id": "TASK-001", "decision": "approve"}, None, ""),
            ("/ceo/api/upload?task=TASK-001&slot=hero", None, b"png", "hero.png"),
            ("/ceo/api/research-queue", {"subject": "battery price", "action": "add"}, None, ""),
            ("/ceo/api/article/edit", {"task_id": "TASK-001", "text": "# Edited\n"}, None, ""),
            ("/ceo/api/article/preview", {"text": "# Draft\n"}, None, ""),
            ("/ceo/api/competitor", {"target": "example.com"}, None, ""),
        ]

    def test_preview_forbids_every_ceo_write_route(self):
        routes = [
            ("/ceo/api/propose", {"subject": "battery data"}, None, ""),
            ("/ceo/api/proposal/approve", {"proposal_id": 1}, None, ""),
            ("/ceo/api/proposal/suggest", {"proposal_id": 1, "comment": "narrower"}, None, ""),
            ("/ceo/api/proposal/reject", {"proposal_id": 1, "reason": "covered"}, None, ""),
            ("/ceo/api/proposal/undo-rejection", {"proposal_id": 1}, None, ""),
            ("/ceo/api/watchlist", {"keyword": "battery", "action": "add"}, None, ""),
            ("/ceo/api/revision", {"task_id": "TASK-001", "comment": "change"}, None, ""),
            ("/ceo/api/decision", {"task_id": "TASK-001", "decision": "approve"}, None, ""),
            ("/ceo/api/upload?task=TASK-001&slot=hero", None, b"png", "hero.png"),
            ("/ceo/api/research-queue", {"subject": "battery price", "action": "add"}, None, ""),
            ("/ceo/api/article/edit", {"task_id": "TASK-001", "text": "# Edited\n"}, None, ""),
            ("/ceo/api/article/preview", {"text": "# Draft\n"}, None, ""),
        ]
        with patch.dict(os.environ, {"CMO_DASHBOARD_PREVIEW": "1"}), patch.object(
            ceo_console.console_auth, "authorize", return_value=("ceo@test", "ceo")
        ):
            for path, body, raw, filename in routes:
                with self.subTest(path=path):
                    handler = Handler(path, body, raw, filename)
                    ceo_console.dispatch(handler, "POST")
                    self.assertEqual(handler.status, 403)


if __name__ == "__main__":
    unittest.main()
