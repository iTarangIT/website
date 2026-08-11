import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import preview_metrics


class PreviewMetricsTests(unittest.TestCase):
    def test_affected_pages_accepts_live_paths_and_rejects_other_hosts(self):
        task = {"affected_pages": "/ /products https://itarang.com/contact https://evil.example/phish"}
        self.assertEqual(
            preview_metrics.affected_pages(task),
            ["https://itarang.com/", "https://itarang.com/products", "https://itarang.com/contact"],
        )

    def test_capture_metrics_writes_lighthouse_baseline_and_zero_cost_entry(self):
        report = {
            "categories": {"performance": {"score": 0.83}},
            "audits": {
                "interactive": {"numericValue": 1200},
                "total-byte-weight": {"numericValue": 1234},
                "document-title": {"score": 1},
            },
        }

        class Result:
            stdout = json.dumps(report)

        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(preview_metrics, "METRICS_DIR", Path(tmp)), \
             patch.object(preview_metrics, "_record_spend") as spend, \
             patch.object(preview_metrics, "_fetch_seo_elements", return_value={"title": "iTarang"}):
            result = preview_metrics.capture_metrics(
                {"id": "TASK-1", "affected_pages": "/"}, "baseline", runner=lambda *a, **k: Result()
            )
            saved = json.loads((Path(tmp) / "TASK-1.baseline.json").read_text())
        self.assertEqual(result["status"], "captured")
        self.assertEqual(saved["pages"][0]["performance_score"], 83.0)
        self.assertEqual(saved["pages"][0]["load_time_ms"], 1200)
        self.assertEqual(saved["pages"][0]["page_weight_bytes"], 1234)
        self.assertEqual(saved["pages"][0]["seo_elements"], {"title": "iTarang"})
        spend.assert_called_once_with("TASK-1", "lighthouse", "lighthouse-ci", "captured", 0.0)

    def test_deploy_preview_reads_token_and_hook_at_call_time_without_leaking_token(self):
        seen = {}

        class Response:
            status = 201
            def read(self): return b'{"job":{"id":"deployment"}}'
            def __enter__(self): return self
            def __exit__(self, *args): return False

        def opener(request, timeout):
            seen["authorization"] = request.headers["Authorization"]
            seen["body"] = json.loads(request.data)
            return Response()

        with patch.dict(os.environ, {
            "VERCEL_DEPLOY_HOOK_URL": "https://vercel.test/hook",
            "VERCEL_TOKEN": "secret",
            "CMO_PREVIEW_URL": "https://cmo-changes.example.vercel.app",
        }, clear=False), patch.object(preview_metrics, "urlopen", opener), patch.object(preview_metrics, "_record_spend"):
            result = preview_metrics.deploy_preview("TASK-3", "abc1234")
        self.assertEqual(result["preview_url"], "https://cmo-changes.example.vercel.app")
        self.assertEqual(seen["authorization"], "Bearer secret")
        self.assertEqual(seen["body"]["ref"], "cmo-changes")
        self.assertNotIn("secret", json.dumps(result))

    def test_evidence_message_requires_exactly_three_change_specific_lines(self):
        task = {"id": "TASK-3", "agent_summary_1": "Hero copy", "agent_summary_2": "CTA", "agent_summary_3": "Mobile spacing"}
        message = preview_metrics.evidence_message(task, "abc1234", "https://preview.example")
        self.assertIn("Preview: https://preview.example", message)
        self.assertIn("Live: https://itarang.com", message)
        self.assertEqual(message.count("\n- "), 3)
        with self.assertRaises(ValueError):
            preview_metrics.evidence_message({"id": "TASK-4", "agent_summary_1": "only one"}, "abc1234")

    def test_compare_matches_pages_by_url_and_reports_seo_delta(self):
        baseline = {"pages": [
            {"url": "https://itarang.com/a", "page_weight_bytes": 100, "performance_score": 80, "load_time_ms": 1200, "seo_elements": {"title": "Old"}},
            {"url": "https://itarang.com/b", "page_weight_bytes": 200, "performance_score": 70, "load_time_ms": 1800, "seo_elements": {}},
        ]}
        live = {"pages": [
            {"url": "https://itarang.com/b", "page_weight_bytes": 150, "performance_score": 75, "load_time_ms": 1600, "seo_elements": {}},
            {"url": "https://itarang.com/a", "page_weight_bytes": 75, "performance_score": 85, "load_time_ms": 1000, "seo_elements": {"title": "New"}},
        ]}
        rows = preview_metrics.compare(baseline, live)
        a_weight = next(row for row in rows if row["metric"] == "page weight · https://itarang.com/a")
        seo = next(row for row in rows if row["metric"] == "SEO elements · https://itarang.com/a")
        self.assertEqual(a_weight["delta"], -25)
        self.assertEqual(seo["delta"], "changed")

    def test_weekly_summary_only_counts_current_week_live_captures(self):
        now = dt.datetime(2026, 7, 28, 10, tzinfo=dt.timezone.utc)
        before = {"pages": [{"url": "https://itarang.com/", "page_weight_bytes": 100, "performance_score": 80, "load_time_ms": 1000, "seo_elements": {"title": "Old"}}]}
        current = {"captured_at": "2026-07-28T09:00:00+00:00", "pages": [{"url": "https://itarang.com/", "page_weight_bytes": 70, "performance_score": 85, "load_time_ms": 900, "seo_elements": {"title": "New"}}]}
        old = {"captured_at": "2026-07-20T09:00:00+00:00", "pages": current["pages"]}
        with tempfile.TemporaryDirectory() as tmp, patch.object(preview_metrics, "METRICS_DIR", Path(tmp)):
            root = Path(tmp)
            (root / "TASK-1.baseline.json").write_text(json.dumps(before))
            (root / "TASK-1.live.json").write_text(json.dumps(current))
            (root / "TASK-2.baseline.json").write_text(json.dumps(before))
            (root / "TASK-2.live.json").write_text(json.dumps(old))
            totals = preview_metrics.weekly_summary(at=now)
        self.assertEqual(totals["changes"], 1)
        self.assertEqual(totals["page_weight_saved_bytes"], 30)
        self.assertEqual(totals["performance_score_delta"], 5)
        self.assertEqual(totals["seo_fixes_shipped"], 1)


if __name__ == "__main__":
    unittest.main()
