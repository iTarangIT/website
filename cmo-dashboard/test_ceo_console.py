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

    def test_only_artifact_backed_content_reaches_the_blogs_tab(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artifacts").mkdir()
            (root / "artifacts" / "draft.md").write_text("draft", encoding="utf-8")
            board = root / "tasks.md"
            text = board_card("TASK-1", "none") + board_card("TASK-2", "artifacts/draft.md").split("## Human Approval", 1)[1].split("## Completed", 1)[0]
            board.write_text(text, encoding="utf-8")
            result = console_board.read_board(board, root)
        # An unwritten content card is no longer surfaced as a "topic" here; topics
        # live in the proposals store until they are approved.
        self.assertNotIn("topics", result)
        self.assertEqual([x["id"] for x in result["blogs"]], ["TASK-2"])

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

    def test_page_modules_import_in_both_orders(self):
        for first, second in (("ceo_console", "ceo_page"), ("ceo_page", "ceo_console")):
            importlib.reload(importlib.import_module(first))
            importlib.reload(importlib.import_module(second))
        self.assertNotIn("ceo_console", Path(ceo_console.__file__).with_name("ceo_page.py").read_text(encoding="utf-8"))

    def test_page_has_no_external_asset_links(self):
        page = render_page().decode()
        self.assertNotRegex(page, r'''(?:src|href)=["'](?:https?:)?//''')


if __name__ == "__main__":
    unittest.main()
