import io
import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import console_auth
import dashboard_server
import tech_console
from cmo_runtime.decisions import DecisionConflict, DecisionStore
from tech_page import render_page


class Handler:
    def __init__(self, path="/tech", body=None, authorization="Bearer token"):
        raw = json.dumps(body or {}).encode()
        self.path = path
        self.headers = {"Authorization": authorization, "Content-Length": str(len(raw))}
        self.rfile = io.BytesIO(raw)
        self.wfile = io.BytesIO()
        self.status = None
        self.response_headers = {}

    def send_response(self, status):
        self.status = int(status)

    def send_header(self, key, value):
        self.response_headers[key] = value

    def end_headers(self):
        pass

    def value(self):
        return json.loads(self.wfile.getvalue())


def board(task_id="TASK-001"):
    return f"""# iTarang CMO Task Board

## Backlog

## In Progress

## CMO Review

## Human Approval

### {task_id} — One card

- Owner: content
- Skill: content
- Status: pending human approval
- Priority: P1
- Description: board-secret-description
- Deliverable: artifacts/one.md
- Attachment: artifacts/one.md
- Metric: measurable
- Acceptance criteria: verified
- Created: 2026-08-10T00:00:00Z
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
- Tags: action to be taken by: human
- Dependencies: none
- Change status: pending

## Completed
"""


class TechConsoleTests(unittest.TestCase):
    def test_console_dispatch_is_first_statement_of_get_and_post(self):
        for method in (dashboard_server.DashboardHandler.do_GET, dashboard_server.DashboardHandler.do_POST):
            source = inspect.getsource(method)
            first_body_line = [line.strip() for line in source.splitlines()[1:] if line.strip()][0]
            self.assertIn("self._console_dispatch", first_body_line)

    def test_page_and_console_import_in_both_orders(self):
        for statement in (
            "import ceo_page; import ceo_console",
            "import ceo_console; import ceo_page",
            "import tech_page; import tech_console",
            "import tech_console; import tech_page",
        ):
            with self.subTest(statement=statement):
                result = subprocess.run(
                    [sys.executable, "-c", statement], cwd=Path(__file__).parent,
                    env={**os.environ, "CMO_DASHBOARD_PROFILE_DIR": ".."},
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_handles_exact_prefix_only(self):
        self.assertTrue(tech_console.handles("/tech"))
        self.assertTrue(tech_console.handles("/tech/api/state"))
        self.assertFalse(tech_console.handles("/techanything"))

    def test_browser_config_uses_shared_auth_configuration(self):
        handler = Handler("/tech/api/config", authorization="")
        with patch.object(
            console_auth, "supabase_browser_config", return_value={"url": "configured", "anon_key": "configured"}
        ):
            self.assertTrue(tech_console.dispatch(handler, "GET"))
        self.assertEqual(handler.status, 200)
        self.assertEqual(sorted(handler.value()), ["anon_key", "url"])

    def test_ceo_role_cannot_reach_tech_route(self):
        handler = Handler("/tech/api/state")
        with patch.dict(os.environ, {
            "SUPABASE_URL": "https://auth.invalid", "SUPABASE_ANON_KEY": "anon",
            "CMO_CEO_EMAIL": "ceo@example.test", "CMO_TECH_EMAIL": "tech@example.test",
        }, clear=False), patch.object(
            console_auth, "_supabase_get_user", return_value="ceo@example.test"
        ):
            console_auth._token_cache.clear()
            tech_console.dispatch(handler, "GET")
        self.assertEqual(handler.status, 403)

    def test_shell_has_no_board_data(self):
        handler = Handler("/tech")
        self.assertTrue(tech_console.dispatch(handler, "GET"))
        self.assertEqual(handler.status, 200)
        self.assertNotIn(b"board-secret-description", handler.wfile.getvalue())

    def test_state_reads_board_only_from_patched_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tasks.md").write_text(board(), encoding="utf-8")
            (root / "logs").mkdir()
            with patch.object(tech_console, "PROFILE_DIR", root), \
                 patch.object(tech_console, "SPEND_LOG", root / "logs" / "spend.log"), \
                 patch.object(tech_console, "APPROVAL_LOG", root / "logs" / "approvals.log"), \
                 patch.object(tech_console, "LOGIN_LOG", root / "logs" / "console-auth.log"), \
                 patch.object(tech_console, "ELEVENLABS_LOG", root / "logs" / "elevenlabs-usage.jsonl"), \
                 patch.object(tech_console, "DATABASE_HEALTH", root / "state" / "database-health.json"), \
                 patch.object(tech_console, "CALLING_USAGE", root / "logs" / "calling-usage.jsonl"), \
                 patch.object(tech_console, "CRM_USAGE", root / "logs" / "crm-usage.jsonl"), \
                 patch.object(tech_console.dashboard_server, "gsc_summary", return_value={"collection_start": "2026-08-04"}):
                payload = tech_console.state_payload()
        self.assertEqual([task["id"] for task in payload["tasks"]], ["TASK-001"])

    def test_spend_renders_every_row_and_unmeasured_is_not_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spend.log"
            path.write_text(
                json.dumps({"date": "2026-08-10T01:00:00Z", "provider": "firecrawl", "rupee_cost": 7, "credits_consumed": 2}) + "\n" +
                json.dumps({"date": "2026-08-10T02:00:00Z", "provider": "other"}) + "\n",
                encoding="utf-8",
            )
            with patch.object(tech_console, "SPEND_LOG", path):
                state = tech_console.spend_state()
        self.assertEqual(len(state["rows"]), 2)
        self.assertEqual(state["unmeasured"], 1)
        self.assertIsNone(state["rows"][1]["rupee_cost"])
        self.assertEqual(state["providers"]["other"]["unmeasured"], 1)

    def test_missing_infrastructure_sources_name_each_source(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory)
            patches = [
                patch.object(tech_console, "LOGIN_LOG", missing / "console-auth.log"),
                patch.object(tech_console, "ELEVENLABS_LOG", missing / "elevenlabs-usage.jsonl"),
                patch.object(tech_console, "DATABASE_HEALTH", missing / "database-health.json"),
                patch.object(tech_console, "CALLING_USAGE", missing / "calling-usage.jsonl"),
                patch.object(tech_console, "CRM_USAGE", missing / "crm-usage.jsonl"),
            ]
            for item in patches:
                item.start()
            try:
                tiles = tech_console.infrastructure_state({"rows": []})
            finally:
                for item in reversed(patches):
                    item.stop()
        by_name = {tile["name"]: tile for tile in tiles}
        self.assertEqual(by_name["Database health"]["value"], "no source connected")
        self.assertIn("database-health.json", by_name["Database health"]["detail"])
        self.assertEqual(by_name["CRM usage"]["value"], "no source connected")
        self.assertIn("crm-usage.jsonl", by_name["CRM usage"]["detail"])

    def test_pages_have_no_external_asset_request(self):
        text = render_page().decode()
        self.assertNotRegex(text, r'''(?:src|href)=["'](?:https?:)?//''')

    def test_first_decision_wins_in_all_surface_orders(self):
        orders = [("ceo", "tech"), ("tech", "ceo"), ("discord", "ceo"), ("discord", "tech")]
        for index, (first, second) in enumerate(orders, 1):
            with self.subTest(first=first, second=second), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "state").mkdir()
                (root / "logs").mkdir()
                (root / "tasks.md").write_text(board(f"TASK-{index:03d}"), encoding="utf-8")
                (root / "state" / "approvals.json").write_text("{}\n", encoding="utf-8")
                (root / "logs" / "approvals.log").write_text("", encoding="utf-8")
                store = DecisionStore(root)
                task_id = f"TASK-{index:03d}"
                first_surface = "discord" if first == "discord" else "dashboard"
                store.decide(task_id, "approve", surface=first_surface, approver_id=f"{first}@example.test")
                with self.assertRaises(DecisionConflict):
                    store.decide(task_id, "approve", surface="dashboard", approver_id=f"{second}@example.test")

    def test_preview_blocks_both_tech_posts(self):
        with patch.dict(os.environ, {"CMO_DASHBOARD_PREVIEW": "1"}), patch.object(
            tech_console.console_auth, "authorize", return_value=("tech@example.test", "tech")
        ):
            for route in ("/tech/api/decision", "/tech/api/validate"):
                handler = Handler(route, {"task_id": "TASK-001", "decision": "approve"})
                tech_console.dispatch(handler, "POST")
                self.assertEqual(handler.status, 403)


if __name__ == "__main__":
    unittest.main()
