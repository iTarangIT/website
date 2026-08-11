from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Response:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return io.StringIO(json.dumps(self.payload))

    def __exit__(self, *_args):
        return False


class MorningSeoTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("morning_seo_job_test", "morning-seo-job.py")
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.module.PROFILE = root
        self.module.STATE = root / "state/morning-seo-last-run"
        self.module.LOG = root / "logs/morning-review.log"
        self.module.BOARD = root / "tasks.md"
        self.module.TASKS_LOCK = root / "state/tasks.lock"
        self.module.BOARD.write_text("## Backlog\n", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_failed_daily_attempt_writes_marker_and_does_not_retry_same_day(self):
        calls = []

        def fail_crawl():
            calls.append("attempt")
            raise RuntimeError("expected failure")

        with (
            patch.object(self.module, "firecrawl", side_effect=fail_crawl),
            patch.object(self.module, "spend_paused", return_value=False),
            patch.object(self.module, "post", return_value=None),
        ):
            self.assertEqual(1, self.module.run())
            self.assertEqual(0, self.module.run())

        self.assertEqual(["attempt"], calls)
        marker = json.loads(self.module.STATE.read_text(encoding="utf-8"))
        self.assertEqual(self.module.now_ist().date().isoformat(), marker["day"])
        self.assertEqual("failed", marker["status"])

    def test_force_cannot_bypass_the_one_attempt_per_day_marker(self):
        calls = []

        def fail_crawl():
            calls.append("attempt")
            raise RuntimeError("expected failure")

        with (
            patch.object(self.module, "firecrawl", side_effect=fail_crawl),
            patch.object(self.module, "spend_paused", return_value=False),
            patch.object(self.module, "post", return_value=None),
        ):
            self.assertEqual(1, self.module.run(force=True))
            self.assertEqual(0, self.module.run(force=True))

        self.assertEqual(["attempt"], calls)

    def test_firecrawl_limit_is_twenty_and_success_accounting_happens_after_result(self):
        requests = []
        records = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return Response({"id": "crawl-1"})
            return Response({"status": "completed", "data": [{"url": "a"}, {"url": "b"}]})

        def record(*args, **kwargs):
            self.assertEqual(2, len(requests), "accounting must happen after the crawl result returns")
            records.append((args, kwargs))

        with (
            patch.dict(self.module.os.environ, {"FIRECRAWL_API_KEY": "test-key"}, clear=False),
            patch.object(self.module, "urlopen", side_effect=fake_urlopen),
            patch.object(self.module, "record_firecrawl", side_effect=record),
        ):
            pages = self.module.firecrawl()

        payload = json.loads(requests[0].data)
        self.assertEqual(20, payload["limit"])
        self.assertEqual(2, len(pages))
        self.assertEqual(2, records[0][1]["pages_fetched"])
        self.assertEqual(2, records[0][1]["estimated_credits"])
        self.assertEqual("completed", records[0][1]["status"])

    def test_failed_firecrawl_is_accounted_after_failure_with_nonzero_credit_estimate(self):
        records = []

        def fake_urlopen(_request, timeout):
            raise RuntimeError("transport failed")

        with (
            patch.dict(self.module.os.environ, {"FIRECRAWL_API_KEY": "test-key"}, clear=False),
            patch.object(self.module, "urlopen", side_effect=fake_urlopen),
            patch.object(self.module, "record_firecrawl", side_effect=lambda **kwargs: records.append(kwargs)),
        ):
            with self.assertRaisesRegex(RuntimeError, "transport failed"):
                self.module.firecrawl()

        self.assertEqual(1, len(records))
        self.assertEqual("failed", records[0]["status"])
        self.assertEqual(0, records[0]["pages_fetched"])
        self.assertGreaterEqual(records[0]["estimated_credits"], 1)

    def test_commit_tasks_reloads_board_under_shared_lock_and_preserves_newer_content(self):
        newer_card = """### TASK-001 — Existing newer card

- ID: TASK-001
- Title: Existing newer card
- Owner: seo
- Skill: seo
- Status: Backlog
- Last updated: 2026-08-04T00:00:00Z
- Updated: 2026-08-04T00:00:00Z
"""
        self.module.BOARD.write_text(
            "## Backlog\n\n" + newer_card
            + "\n## In Progress\n\n_No tasks._\n"
            + "\n## CMO Review\n\n_No tasks._\n"
            + "\n## Human Approval\n\n_No tasks._\n"
            + "\n## Completed\n\n_No tasks._\n",
            encoding="utf-8",
        )
        suggestions = [{
            "title": "Fresh SEO finding",
            "owner": "seo",
            "priority": "high",
            "objective": "Preserve concurrent board content.",
            "acceptance_criteria": ["Keep the newer card."],
        }]

        added = self.module.commit_tasks(suggestions, "2026-08-04")
        persisted = self.module.BOARD.read_text(encoding="utf-8")

        self.assertEqual(["TASK-002"], [item["id"] for item in added])
        self.assertIn("TASK-001 — Existing newer card", persisted)
        self.assertIn("TASK-002 — Fresh SEO finding", persisted)
        self.assertEqual([], self.module.validate_structure(self.module.BOARD))


class SpendTrackerTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script("spend_tracker_test", "spend-tracker.py")
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.module.LOG = root / "logs/spend.log"
        self.module.ALERT_STATE = root / "state/spend-alert-state"

    def tearDown(self):
        self.temp.cleanup()

    def test_daily_firecrawl_credit_accounting_includes_failed_calls(self):
        common = {
            "provider": "firecrawl",
            "model": "crawl-api",
            "task_id": "morning-seo-2026-08-04",
            "cost": "none",
            "credit_day": "2026-08-04",
        }
        with patch.object(self.module, "send", return_value=False):
            self.module.record(SimpleNamespace(**common, status="completed", pages_fetched=12, estimated_credits=12))
            self.module.record(SimpleNamespace(**common, status="failed", pages_fetched=0, estimated_credits=1))

        result = self.module.daily_firecrawl_credits("2026-08-04")
        self.assertEqual(2, result["calls"])
        self.assertEqual(12, result["pages_fetched"])
        self.assertEqual(13, result["estimated_credits"])
        self.assertEqual(1, result["failed_calls"])

    def test_legacy_pre_call_records_are_reported_as_unaccounted_not_zero_credit_failures(self):
        self.module.LOG.parent.mkdir(parents=True, exist_ok=True)
        self.module.LOG.write_text(json.dumps({
            "record_type": "call",
            "date": "2026-08-04T02:00:00+00:00",
            "provider": "firecrawl",
            "model": "crawl-api",
            "task_id": "legacy",
            "estimated_cost_usd": None,
            "status": "unknown",
        }) + "\n", encoding="utf-8")

        result = self.module.daily_firecrawl_credits("2026-08-04")

        self.assertEqual(1, result["calls"])
        self.assertEqual(1, result["unaccounted_calls"])
        self.assertEqual(0, result["failed_calls"])
        self.assertIn("1 unaccounted", self.module.firecrawl_credit_line("2026-08-04"))


OLD = "a" * 40
NEW = "b" * 40


class MorningCrawlCadenceTests(unittest.TestCase):
    """The crawl is sized to the sitemap and triggers on the deployed commit."""

    def setUp(self) -> None:
        self.module = load_script("morning_seo_job", "morning-seo-job.py")
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.state = Path(directory.name) / "morning-seo-last-run"
        self.module.STATE = self.state

    def mark(self, day: str, commit: str | None = OLD) -> None:
        marker = {"day": day, "status": "success"}
        if commit:
            marker["commit"] = commit
        self.state.write_text(json.dumps(marker), encoding="utf-8")

    def test_a_first_ever_run_is_due(self) -> None:
        due, reason = self.module.due("2026-08-11", NEW)
        self.assertTrue(due)
        self.assertEqual(reason, "first run")

    def test_an_unchanged_commit_does_not_crawl(self) -> None:
        self.mark("2026-08-09", OLD)
        due, reason = self.module.due("2026-08-11", OLD)
        self.assertFalse(due)
        self.assertIn("unchanged", reason)

    def test_a_changed_commit_crawls(self) -> None:
        self.mark("2026-08-09", OLD)
        due, reason = self.module.due("2026-08-11", NEW)
        self.assertTrue(due)
        self.assertIn("changed", reason)

    def test_the_weekly_floor_crawls_even_when_nothing_deployed(self) -> None:
        self.mark("2026-08-01", OLD)
        due, reason = self.module.due("2026-08-11", OLD)
        self.assertTrue(due)
        self.assertIn("weekly floor", reason)

    def test_a_busy_deploy_day_buys_at_most_one_crawl(self) -> None:
        self.mark("2026-08-11", OLD)
        due, reason = self.module.due("2026-08-11", NEW)
        self.assertFalse(due, "a second deploy the same day must not crawl again")
        self.assertIn("already crawled", reason)

    def test_an_unreadable_commit_holds_rather_than_crawling_every_cycle(self) -> None:
        self.mark("2026-08-10", OLD)
        due, reason = self.module.due("2026-08-11", None)
        self.assertFalse(due)
        self.assertIn("could not be read", reason)

    def test_an_unreadable_commit_still_yields_to_the_weekly_floor(self) -> None:
        self.mark("2026-08-01", OLD)
        due, _reason = self.module.due("2026-08-11", None)
        self.assertTrue(due, "a read failure must not stop the crawl forever")

    def test_a_legacy_marker_without_a_commit_crawls_once(self) -> None:
        self.mark("2026-08-10", commit=None)
        due, reason = self.module.due("2026-08-11", NEW)
        self.assertTrue(due)
        self.assertEqual(reason, "no crawled commit recorded")

    def test_an_unreadable_marker_does_not_block_the_crawl_forever(self) -> None:
        self.state.write_text("not json and not a date", encoding="utf-8")
        due, _reason = self.module.due("2026-08-11", NEW)
        self.assertTrue(due)

    def test_a_failed_attempt_keeps_the_last_known_commit(self) -> None:
        self.mark("2026-08-10", OLD)
        self.module.write_daily_marker("2026-08-11", "failed", "boom", commit=None)
        self.assertEqual(self.module.read_marker()["commit"], OLD)

    def test_the_crawl_ceiling_matches_the_sitemap(self) -> None:
        # 12 static routes + 4 blog posts + 4 active category pages.
        self.assertEqual(self.module.CRAWL_PAGE_LIMIT, 20)
        self.assertEqual(self.module.MAXIMUM_DAYS_BETWEEN_CRAWLS, 7)


if __name__ == "__main__":
    unittest.main()
