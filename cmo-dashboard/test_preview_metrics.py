import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import preview_metrics


class PreviewMetricsTests(unittest.TestCase):
    def test_affected_pages_requires_explicit_task_urls(self):
        self.assertEqual(preview_metrics.affected_pages({"id": "TASK-1"}), [])
        self.assertEqual(
            preview_metrics.affected_pages({"page_urls": "https://itarang.com https://itarang.com/products"}),
            ["https://itarang.com", "https://itarang.com/products"],
        )

    def test_capture_metrics_writes_baseline_without_credentials(self):
        report = {
            "categories": {"performance": {"score": 0.83}},
            "timing": {"total": 1200},
            "audits": {"total-byte-weight": {"numericValue": 1234}, "document-title": {"score": 1}},
        }

        class Result:
            stdout = json.dumps(report)

        def runner(*args, **kwargs):
            return Result()

        with tempfile.TemporaryDirectory() as tmp, patch.object(preview_metrics, "METRICS_DIR", Path(tmp)), \
             patch.object(preview_metrics, "SPEND_TRACKER", Path(tmp) / "missing-spend.py"):
            result = preview_metrics.capture_metrics(
                {"id": "TASK-1", "page_urls": "https://itarang.com"}, "baseline", runner=runner
            )
            saved = json.loads((Path(tmp) / "TASK-1.baseline.json").read_text())
        self.assertEqual(result["status"], "captured")
        self.assertEqual(saved["pages"][0]["performance_score"], 83.0)
        self.assertEqual(saved["pages"][0]["page_weight_bytes"], 1234)

    def test_capture_metrics_blocks_website_change_without_pages(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(preview_metrics, "METRICS_DIR", Path(tmp)):
            result = preview_metrics.capture_metrics({"id": "TASK-2"}, "baseline")
        self.assertEqual(result["status"], "blocked")
        self.assertIn("no Affected pages", result["reason"])

    def test_deploy_preview_uses_environment_token_and_fixed_url(self):
        seen = {}

        class Response:
            status = 201
            def read(self):
                return b'{"id":"deployment"}'
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False

        def opener(request, timeout):
            seen["authorization"] = request.headers["Authorization"]
            seen["body"] = json.loads(request.data)
            return Response()

        with patch.dict(os.environ, {"VERCEL_DEPLOY_HOOK_URL": "https://vercel.test/hook", "VERCEL_TOKEN": "secret"}), \
             patch.object(preview_metrics, "SPEND_TRACKER", Path("/does/not/exist")), \
             patch.object(preview_metrics, "urlopen", opener):
            result = preview_metrics.deploy_preview("TASK-3", "abc1234")
        self.assertEqual(result["status"], 201)
        self.assertEqual(seen["authorization"], "Bearer secret")
        self.assertEqual(seen["body"]["ref"], "cmo-changes")
        self.assertNotIn("secret", json.dumps(result))

    def test_compare_returns_before_after_delta_rows(self):
        baseline = {"pages": [{"url": "https://itarang.com", "page_weight_bytes": 100, "performance_score": 80, "load_time_ms": 1200, "seo": {}}]}
        live = {"pages": [{"url": "https://itarang.com", "page_weight_bytes": 75, "performance_score": 85, "load_time_ms": 1000, "seo": {}}]}
        rows = preview_metrics.compare(baseline, live)
        self.assertEqual(rows[0]["delta"], -25)
        self.assertEqual(rows[1]["delta"], 5)
        self.assertEqual(rows[2]["delta"], -200)

    def test_discord_evidence_contains_both_sites_and_three_look_at_lines(self):
        message = preview_metrics.evidence_message(
            {"id": "TASK-4", "agent_summary_1": "Check title", "agent_summary_2": "Check CTA", "agent_summary_3": "Check mobile"},
            "abc1234", "https://itarangwebsite.vercel.app",
        )
        self.assertIn("Preview: https://itarangwebsite.vercel.app", message)
        self.assertIn("Live: https://itarang.com", message)
        self.assertEqual(message.count("- "), 3)

    def test_weekly_summary_aggregates_merged_changes(self):
        baseline = {"pages": [{"url": "https://itarang.com", "page_weight_bytes": 100, "performance_score": 80, "load_time_ms": 1200, "seo": {"meta-description": {"score": 0}}}]}
        live = {"pages": [{"url": "https://itarang.com", "page_weight_bytes": 75, "performance_score": 85, "load_time_ms": 1000, "seo": {"meta-description": {"score": 1}}}]}
        with tempfile.TemporaryDirectory() as tmp, patch.object(preview_metrics, "METRICS_DIR", Path(tmp)):
            Path(tmp, "TASK-5.baseline.json").write_text(json.dumps(baseline))
            Path(tmp, "TASK-5.live.json").write_text(json.dumps(live))
            summary = preview_metrics.weekly_summary()
        self.assertEqual(summary["changes"], 1)
        self.assertEqual(summary["page_weight_saved_bytes"], 25)
        self.assertEqual(summary["performance_score_delta"], 5)
        self.assertEqual(summary["seo_fixes_shipped"], 1)


if __name__ == "__main__":
    unittest.main()
