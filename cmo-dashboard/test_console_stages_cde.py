import io
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import analytics_readers
import dashboard_server
import ceo_artifacts
import tech_console
import page_builders
from tech_page import render_page
from tech_script import SCRIPT


def _tracked(relative: str) -> Path:
    """Resolve a tracked source asset from either the repo or the profile layout."""
    here = Path(__file__).resolve().parent
    for base in (here, *here.parents):
        candidate = base / relative
        if candidate.exists():
            return candidate
    raise FileNotFoundError(relative)


class Handler:
    def __init__(self, path, body=None):
        raw = json.dumps(body or {}).encode("utf-8")
        self.path = path
        self.headers = {"Authorization": "Bearer token", "Content-Length": str(len(raw))}
        self.rfile = io.BytesIO(raw)
        self.wfile = io.BytesIO()
        self.status = None

    def send_response(self, status):
        self.status = int(status)

    def send_header(self, _key, _value):
        pass

    def end_headers(self):
        pass

    def value(self):
        return json.loads(self.wfile.getvalue())


def five_lane_board() -> str:
    return """# iTarang CMO Task Board

## Backlog
### TASK-001 — Backlog card
- Owner: seo
- Skill: seo
- Status: queued
- Priority: P2
- Description: backlog
- Attachment: none
- Metric: rank
- Created: 2026-08-10T00:00:00Z
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
- Tags: action to be taken by: agent
- Dependencies: none

## In Progress
### TASK-002 — Active card
- Owner: content
- Skill: content
- Status: in-progress
- Priority: P1
- Description: active
- Attachment: none
- Metric: article
- Created: 2026-08-10T00:00:00Z
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
- Tags: action to be taken by: agent
- Dependencies: none

## CMO Review
### TASK-003 — Review card
- Owner: social
- Skill: social
- Status: pending CMO review
- Priority: P2
- Description: review
- Attachment: none
- Metric: reach
- Created: 2026-08-10T00:00:00Z
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
- Tags: action to be taken by: cmo
- Dependencies: none

## Human Approval
### TASK-004 — Approval card
- Owner: content
- Skill: content
- Status: pending human approval
- Priority: P0
- Description: approval
- Attachment: none
- Metric: conversion
- Acceptance criteria: route verified
- Change type: website
- Branch: cmo-changes
- Commit hash(es): abc1234
- Preview URL: https://preview.example.test
- Metrics evidence: state/metrics.json
- Change status: awaiting Gate 2
- Created: 2026-08-10T00:00:00Z
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
- Tags: action to be taken by: human
- Dependencies: none

## Completed
### TASK-005 — Completed card
- Owner: seo
- Skill: seo
- Status: completed
- Priority: P3
- Description: done
- Attachment: none
- Metric: complete
- Created: 2026-08-10T00:00:00Z
- Last updated: 2026-08-10T00:00:00Z
- Updated: 2026-08-10T00:00:00Z
- Tags: action to be taken by: human
- Dependencies: none
"""


class ConsoleStagesCDETests(unittest.TestCase):
    def test_tech_uses_unified_front_door_session_and_has_no_second_login(self):
        page = render_page().decode("utf-8")
        self.assertIn("cmo_token", SCRIPT)
        self.assertIn("cmo_email", SCRIPT)
        self.assertIn("cmo_role", SCRIPT)
        self.assertNotIn("itarang_console_token", SCRIPT)
        self.assertNotIn('id="login-form"', page)
        self.assertIn("/?msg=expired", SCRIPT)

    def test_board_exposes_five_lanes_full_fields_decision_and_thread(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "tasks.md").write_text(five_lane_board(), encoding="utf-8")
            (root / "state").mkdir()
            (root / "logs").mkdir()
            decision = {
                "task_id": "TASK-004", "decision": "approve",
                "approver_id": "owner@example.test", "surface": "dashboard",
                "timestamp": "2026-08-10T01:00:00Z", "commit_sha": "abc1234",
                "send_back_text": "",
            }
            (root / "state" / "human-approvals.json").write_text(
                json.dumps({"TASK-004": decision}), encoding="utf-8"
            )
            (root / "logs" / "approvals.log").write_text(
                json.dumps({**decision, "outcome": "recorded"}) + "\n", encoding="utf-8"
            )
            with (
                patch.object(tech_console, "PROFILE_DIR", root),
                patch.object(tech_console, "CMO_SKILLS_DIR", root / "cmo_skills"),
                patch.object(tech_console, "SPEND_LOG", root / "logs" / "spend.log"),
                patch.object(tech_console, "APPROVAL_LOG", root / "logs" / "approvals.log"),
                patch.object(tech_console, "LOGIN_LOG", root / "logs" / "console-auth.log"),
                patch.object(tech_console, "ELEVENLABS_LOG", root / "logs" / "elevenlabs-usage.jsonl"),
                patch.object(tech_console, "DATABASE_HEALTH", root / "state" / "database-health.json"),
                patch.object(tech_console, "CALLING_USAGE", root / "logs" / "calling-usage.jsonl"),
                patch.object(tech_console, "CRM_USAGE", root / "logs" / "crm-usage.jsonl"),
                patch.object(dashboard_server, "gsc_summary", return_value={"status": "collecting"}),
                patch.object(tech_console.analytics_readers, "ga4_technical_summary", return_value={"status": "not_connected"}),
            ):
                payload = tech_console.state_payload()
        self.assertEqual(list(payload["board"]), list(tech_console.LANE_NAMES))
        card = next(item for item in payload["tasks"] if item["id"] == "TASK-004")
        for field in ("skill", "priority", "acceptance_criteria", "change_type", "branch", "preview_url", "metrics_evidence", "change_status"):
            self.assertIn(field, card)
        self.assertEqual(card["decision_summary"]["approver_id"], "owner@example.test")
        self.assertEqual(len(card["approval_thread"]), 1)

    def test_runtime_reads_cmo_skill_files_and_full_last_run_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills = root / "cmo_skills"
            logs = root / "logs"
            skills.mkdir()
            logs.mkdir()
            for name in ("seo", "content", "social"):
                (skills / f"{name}.skill").write_text(
                    f"SKILL: {name}\nOBJECTIVE: test\nKPIS:\n", encoding="utf-8"
                )
            (skills / "ads.skill").write_text(
                "SKILL: ads\nOBJECTIVE: test\nKPIS:\nOUTPUT: draft-only\n", encoding="utf-8"
            )
            (skills / "ops.skill").write_text(
                "SKILL: ops\nOBJECTIVE: not defined — skill disabled\nKPIS:\n", encoding="utf-8"
            )
            (logs / "spend.log").write_text(
                json.dumps({"record_type": "run", "date": "2026-08-10T01:00:00Z", "run_type": "plan", "skill_loaded": "none", "approximate_tokens": 10, "status": "completed"}) + "\n" +
                json.dumps({"record_type": "run", "date": "2026-08-10T02:00:00Z", "run_type": "execute", "skill_loaded": "content", "approximate_tokens": 20, "status": "completed"}) + "\n" +
                json.dumps({"record_type": "run", "date": "2026-08-10T03:00:00Z", "run_type": "review", "skill_used": "none", "approximate_tokens": 30, "status": "completed"}) + "\n",
                encoding="utf-8",
            )
            tasks = [{"id": "TASK-002", "section": "In Progress"}]
            with patch.object(tech_console, "PROFILE_DIR", root), \
                 patch.object(tech_console, "CMO_SKILLS_DIR", skills), \
                 patch.object(tech_console, "SPEND_LOG", logs / "spend.log"):
                runtime = tech_console.runtime_state(tasks)
        self.assertEqual(runtime["current_run_type"], "execute")
        self.assertEqual(runtime["in_progress_task"], "TASK-002")
        self.assertEqual(runtime["last_runs"]["execute"]["skill"], "content")
        self.assertEqual(runtime["last_runs"]["review"]["source"], "logs/spend.log")
        by_name = {item["name"]: item for item in runtime["skills"]}
        self.assertIn("human-approved KPI", by_name["seo"]["disabled_reason"])
        self.assertIn("draft-only", by_name["ads"]["disabled_reason"])
        self.assertIn("disabled", by_name["ops"]["disabled_reason"])

    def test_runtime_log_route_returns_only_last_fifty_allowlisted_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "logs").mkdir()
            (root / "logs" / "hourly-cycle.log").write_text(
                "\n".join(f"line-{index}" for index in range(60)) + "\n", encoding="utf-8"
            )
            handler = Handler("/tech/api/logs?name=hourly-cycle.log")
            with patch.object(tech_console, "PROFILE_DIR", root), \
                 patch.object(tech_console.console_auth, "authorize", return_value=("tech@example.test", "tech")):
                tech_console.dispatch(handler, "GET")
        self.assertEqual(handler.status, 200)
        self.assertEqual(len(handler.value()["lines"]), 50)
        self.assertEqual(handler.value()["lines"][0], "line-10")

    def test_runtime_validator_reports_exit_code_and_structural_issues(self):
        completed = SimpleNamespace(
            returncode=1,
            stdout='[{"message": "mirrored fields disagree"}]\n',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(tech_console, "PROFILE_DIR", root), \
                 patch.object(tech_console.subprocess, "run", return_value=completed) as run:
                result = tech_console._validate()
        self.assertEqual(result["exit_code"], 1)
        self.assertEqual(result["issues"], [{"message": "mirrored fields disagree"}])
        command = run.call_args.args[0]
        self.assertEqual(command[1:], ["-m", "cmo_runtime.task_file", "--file", "tasks.md", "validate"])
        self.assertEqual(run.call_args.kwargs["cwd"], root)

    def test_spend_uses_only_measured_costs_and_measured_firecrawl_credits(self):
        now = tech_console.dt.datetime.now(tech_console.dt.timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spend.log"
            path.write_text(
                json.dumps({"record_type": "call", "date": now, "provider": "firecrawl", "estimated_credits": 9}) + "\n" +
                json.dumps({"record_type": "call", "date": now, "provider": "firecrawl", "credits_consumed": 2, "rupee_cost": 1}) + "\n" +
                json.dumps({"record_type": "run", "date": now, "run_type": "plan", "skill_loaded": "none", "approximate_tokens": 10, "approximate_cost_inr": 0.0}) + "\n" +
                json.dumps({"record_type": "run", "date": now, "run_type": "execute", "skill_loaded": "content", "tokens": 20, "rupee_cost": 301}) + "\n",
                encoding="utf-8",
            )
            with patch.object(tech_console, "SPEND_LOG", path):
                state = tech_console.spend_state()
        self.assertEqual(state["providers"], {"firecrawl": {"calls": 2, "unmeasured": 1}})
        self.assertEqual(len(state["runs"]), 2)
        self.assertIsNone(state["runs"][0]["rupee_cost"])
        self.assertEqual(state["unmeasured"], 2)
        self.assertIsNone(state["firecrawl"]["today"])
        self.assertIn("1 Firecrawl call", state["firecrawl"]["today_detail"])
        self.assertEqual(state["daily_rupees"], 301)
        self.assertEqual(state["daily_halt_state"], "HALT")

    def test_daily_halt_is_unmeasured_when_today_has_no_measured_rupee_cost(self):
        now = tech_console.dt.datetime.now(tech_console.dt.timezone.utc).isoformat()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spend.log"
            path.write_text(
                json.dumps({"record_type": "run", "date": now, "run_type": "review", "approximate_cost_inr": 0.0}) + "\n",
                encoding="utf-8",
            )
            with patch.object(tech_console, "SPEND_LOG", path):
                state = tech_console.spend_state()
        self.assertEqual(state["daily_halt_state"], "unmeasured")
        self.assertFalse(state["daily_halt"])

    def test_infrastructure_tiles_state_meaning_source_and_missing_source_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            login = root / "console-auth.log"
            elevenlabs = root / "elevenlabs-usage.jsonl"
            database = root / "database-health.json"
            calling = root / "calling-usage.jsonl"
            crm = root / "crm-usage.jsonl"
            login.write_text('{}\n', encoding="utf-8")
            elevenlabs.write_text('{"characters": 120}\n', encoding="utf-8")
            database.write_text('{"status": "healthy"}\n', encoding="utf-8")
            calling.write_text('{"calls": 3}\n', encoding="utf-8")
            with patch.object(tech_console, "LOGIN_LOG", login), \
                 patch.object(tech_console, "ELEVENLABS_LOG", elevenlabs), \
                 patch.object(tech_console, "DATABASE_HEALTH", database), \
                 patch.object(tech_console, "CALLING_USAGE", calling), \
                 patch.object(tech_console, "CRM_USAGE", crm):
                tiles = tech_console.infrastructure_state({"rows": [{"rupee_cost": 7}]})
        self.assertEqual(len(tiles), 6)
        by_name = {tile["name"]: tile for tile in tiles}
        self.assertEqual(by_name["Number of logins"]["value"], "1")
        self.assertEqual(by_name["ElevenLabs usage"]["value"], "120")
        self.assertEqual(by_name["Tech spend"]["value"], "7")
        self.assertEqual(by_name["Database health"]["value"], "healthy")
        self.assertEqual(by_name["Calling volume"]["value"], "3")
        self.assertEqual(by_name["CRM usage"]["value"], "no source connected")
        self.assertIn("crm-usage.jsonl", by_name["CRM usage"]["detail"])
        for tile in tiles:
            self.assertTrue(tile["meaning"])
            self.assertIn("source_connected", tile)

    def test_existing_usage_file_without_metric_is_not_rendered_as_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "calling-usage.jsonl"
            path.write_text('{"status": "completed"}\n', encoding="utf-8")
            tile = tech_console._source_tile(
                "Calling volume", path, key="calls", meaning="Recorded calls."
            )
        self.assertEqual(tile["value"], "no source connected")
        self.assertIn("calling-usage.jsonl:calls", tile["detail"])

    def test_ga4_technical_absence_is_not_connected_without_zero_or_decline(self):
        with patch.dict(analytics_readers.os.environ, {}, clear=True):
            value = analytics_readers.ga4_technical_summary()
        self.assertEqual(value["status"], "not_connected")
        self.assertEqual(value["pages"], [])
        self.assertIsNone(value["collection_start"])
        self.assertTrue(all(item is None for item in value["metrics"].values()))
        self.assertNotIn("decline", json.dumps(value).casefold())

    def test_ga4_technical_detail_reads_pages_and_real_collection_start(self):
        base = {
            "status": "ready", "message": "", "range_days": 28, "device": "all",
            "metrics": {"sessions": 12}, "previous": {"sessions": 10},
            "deltas": {"sessions": 2},
        }
        pages = {"rows": [{
            "dimensionValues": [{"value": "/battery"}],
            "metricValues": [{"value": "20"}, {"value": "12"}, {"value": "0.75"}],
        }]}
        start = {"rows": [{
            "dimensionValues": [{"value": "20260715"}],
            "metricValues": [{"value": "1"}],
        }]}
        environment = {
            "GA4_PROPERTY_ID": "123", "GA4_CREDENTIALS_PATH": "/credentials.json",
            "GA4_MEASUREMENT_ID": "G-TEST", "GA4_TAG_INSTALLED": "true",
        }
        analytics_readers._ga4_detail_cache.clear()
        with patch.dict(analytics_readers.os.environ, environment, clear=True), \
             patch.object(analytics_readers, "ga4_summary", return_value=base), \
             patch.object(analytics_readers, "_ga4_request", side_effect=[pages, start]) as reader:
            value = analytics_readers.ga4_technical_summary(28, "all")
        analytics_readers._ga4_detail_cache.clear()
        self.assertEqual(value["pages"], [{
            "page": "/battery", "screen_page_views": 20,
            "sessions": 12, "engagement_rate": 0.75,
        }])
        self.assertEqual(value["collection_start"], "2026-07-15")
        self.assertEqual(reader.call_args_list[0].args[2]["dimensions"], [{"name": "pagePath"}])
        self.assertEqual(reader.call_args_list[1].args[2]["dimensions"], [{"name": "date"}])

    def test_tech_analytics_has_both_sources_and_no_fabricated_start_date(self):
        self.assertIn("Google Search Console", SCRIPT)
        self.assertIn("Google Analytics 4", SCRIPT)
        self.assertIn("Per-page discovery", SCRIPT)
        self.assertIn("Per-page behavior", SCRIPT)
        self.assertNotIn("4 August 2026", SCRIPT)

    def test_committed_svg_under_artifacts_binds_to_an_article_image_slot(self):
        committed = _tracked("tests/fixtures/stage-d-writer-seam.svg")
        self.assertTrue(committed.is_file())
        self.assertIn(b"<svg", committed.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            article = artifacts / "TASK-900-content.md"
            diagram = artifacts / "TASK-900-flow.svg"
            article.write_text(
                "---\ntitle: Test article\n---\n\n{{image:flow|Approved topic to blog flow}}\n",
                encoding="utf-8",
            )
            diagram.write_bytes(committed.read_bytes())
            task = {
                "id": "TASK-900",
                "image_slot_flow": "artifacts/TASK-900-flow.svg",
            }
            payload = ceo_artifacts.artifact_payload(task, article, root)
            resolved = ceo_artifacts.image_for(task, "flow", root)
        self.assertEqual(resolved, diagram)
        self.assertEqual(payload["image_slots"], [{
            "id": "flow", "caption": "Approved topic to blog flow",
            "bound": True, "url": "/ceo/image?task=TASK-900&slot=flow",
            "filename": "TASK-900-flow.svg",
            # A diagram carries no generation prompt and needs no alt field: its
            # alt text is read out of the SVG's own <title> at publish.
            "prompt": "", "alt": "", "kind": "diagram",
        }])
        self.assertIn(
            {"name": "TASK-900-flow.svg", "kind": "image:flow", "bytes": len(committed.read_bytes())},
            payload["files"],
        )

    def test_an_unbound_diagram_slot_is_not_offered_a_generate_button(self):
        """The kind used to be inferred from the bound file's suffix, so a slot
        with no file yet always reported `illustration` -- and the console offered
        to buy a picture for the one the writer is meant to draw."""
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            article = artifacts / "TASK-901-content.md"
            article.write_text(
                "---\ntitle: Test article\n---\n\n"
                "{{image:flow|A diagram nobody has drawn yet}}\n\n"
                "{{image:depot|A scene nobody has generated yet}}\n",
                encoding="utf-8",
            )
            payload = ceo_artifacts.artifact_payload(
                {"id": "TASK-901", "image_kind_flow": "diagram"}, article, root
            )

        kinds = {slot["id"]: slot["kind"] for slot in payload["image_slots"]}
        self.assertEqual(kinds, {"flow": "diagram", "depot": "illustration"})
        self.assertFalse(any(slot["bound"] for slot in payload["image_slots"]))

    def test_four_declared_slots_all_reach_the_files_tab(self):
        """Positioning is the marker's position, and the payload is what the Files
        tab renders a row from -- so every declared slot has to arrive."""
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            article = artifacts / "TASK-902-content.md"
            article.write_text(
                "---\ntitle: Test article\n---\n\nOpening paragraph.\n\n"
                "{{image:one|First}}\n\nSecond paragraph.\n\n"
                "{{image:two|Second}}\n\nThird paragraph.\n\n"
                "{{image:three|Third}}\n\nFourth paragraph.\n\n"
                "{{image:four|Fourth}}\n",
                encoding="utf-8",
            )
            payload = ceo_artifacts.artifact_payload({"id": "TASK-902"}, article, root)

        self.assertEqual(
            [slot["id"] for slot in payload["image_slots"]], ["one", "two", "three", "four"]
        )
        self.assertEqual([slot["caption"] for slot in payload["image_slots"]][:2], ["First", "Second"])

    def test_content_skill_output_keeps_path_ceiling_and_concept_standard(self):
        path = _tracked("cmo_skills/content.skill")
        output = next(
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("OUTPUT:")
        )
        self.assertIn("artifacts/<TASK-ID>-content.md", output)
        self.assertIn("900–1,400 words", output)
        self.assertIn("explains one concept", output)
        self.assertIn("easy-to-read", output)
        self.assertIn("not a news post", output)

    def test_no_dashboard_module_names_supabase_service_role_key(self):
        dashboard = Path(__file__).resolve().parent
        offenders = [
            path.name for path in dashboard.glob("*.py")
            if "SUPABASE_" + "SERVICE_ROLE_KEY" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])

    def test_every_operational_console_page_is_self_contained_and_discovery_is_dynamic(self):
        discovered = []
        with patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://auth.invalid", "SUPABASE_ANON_KEY": "test-anon-key"},
            clear=False,
        ):
            for name, builder in page_builders.iter_page_builders():
                discovered.append(name)
                page = builder().decode("utf-8")
                self.assertEqual(re.findall(r'(?:src|href)=["\']https?://', page, re.I), [])
                if name != "front_door_page":
                    self.assertNotIn("https://auth.invalid", page)
                    self.assertNotRegex(page, r"fetch\s*\(\s*['\"]https?://")
        expected = sorted(path.stem for path in Path(__file__).parent.glob("*_page.py"))
        self.assertEqual(discovered, expected)


if __name__ == "__main__":
    unittest.main()
