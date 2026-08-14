"""Gate 2 refusals. Each one is proved separately — see SOUL.md section 12 clause 4."""
import json
import tempfile
import unittest
from pathlib import Path

import ceo_publish
from ceo_publish import PublicationConflict, PublicationRefused

APPROVED_COMMIT = "a" * 40
BASE_COMMIT = "b" * 40

CARD = """# Marketing Operations Kanban

## Human Approval

### TASK-500 — Publish a driver guide

- ID: TASK-500
- Title: Publish a driver guide
- Owner: content
- Priority: high
- Status: Human Approval
- Start date: 2026-08-11
- Completed date: not completed
- Objective: Prove the Gate 2 path.
- Acceptance criteria:
  - Refusals are proved separately.
- Latest summary: Awaiting Gate 2.
- Change type: website
- Branch: cmo-changes
- Commit hash(es): {commit}
- Preview URL: https://itarangwebsite.vercel.app
- Preview base: {base}
- Metrics evidence: state/website-metrics/TASK-500
"""


def _report(phase, score):
    return {
        "status": "captured",
        "phase": phase,
        "task_id": "TASK-500",
        "pages": [{
            "url": "https://www.itarang.com/blog",
            "metrics": {"performance_score": score, "page_weight_bytes": 500000},
            "raw_evidence": "x.json",
        }],
    }


class FakeGitHub:
    """Records every call so a test can prove no merge was attempted."""

    def __init__(self, head=APPROVED_COMMIT, base=BASE_COMMIT, can_merge=True):
        self.refs = {"cmo-changes": head, "main": base}
        self._can_merge = can_merge
        self.merges = []

    def ref_sha(self, ref):
        return self.refs[ref]

    def can_merge(self):
        return self._can_merge

    def merge(self, *, base, head, message):
        self.merges.append({"base": base, "head": head, "message": message})
        return "c" * 40


class GateTwoRefusalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "state" / "website-metrics").mkdir(parents=True)
        (self.root / "logs").mkdir(parents=True)
        (self.root / "tasks.md").write_text(
            CARD.format(commit=APPROVED_COMMIT, base=BASE_COMMIT), encoding="utf-8"
        )
        self.write_evidence()
        self.approve()

    def write_evidence(self):
        for phase, score in (("baseline", 43.0), ("preview", 58.0)):
            (self.root / "state" / "website-metrics" / f"TASK-500.{phase}.json").write_text(
                json.dumps(_report(phase, score)), encoding="utf-8"
            )

    def approve(self, commit=APPROVED_COMMIT):
        (self.root / "state" / "human-approvals.json").write_text(
            json.dumps({"TASK-500": {
                "task_id": "TASK-500", "decision": "approve",
                "approver_id": "ceo@itarang.com", "surface": "dashboard",
                "timestamp": "2026-08-11T06:00:00Z", "commit_sha": commit,
                "send_back_text": "",
            }}),
            encoding="utf-8",
        )

    def instruct(self, github):
        """The one path a human click takes: preflight, then a single-use instruction."""
        check = ceo_publish.preflight(self.root, "TASK-500", github=github)
        return ceo_publish.issue_request(
            self.root, "TASK-500", actor="ceo@itarang.com", commit=check.commit
        )

    def log_lines(self):
        path = self.root / "logs" / "approvals.log"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []

    # 1 — no Gate 1 approval cannot publish
    def test_without_gate_one_approval_the_button_is_ineligible_and_publish_refuses(self):
        (self.root / "state" / "human-approvals.json").write_text("{}", encoding="utf-8")
        github = FakeGitHub()
        check = ceo_publish.preflight(self.root, "TASK-500", github=github)
        self.assertFalse(check.eligible)
        self.assertIn("no Gate 1 approval is recorded for this card", check.blockers)
        # and no instruction can be honoured even if one is forged
        with self.assertRaises(PublicationConflict):
            ceo_publish.publish(
                self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
                request_id="forged", github=github,
            )
        self.assertEqual(github.merges, [])

    def test_a_validly_minted_instruction_still_refuses_once_gate_one_is_gone(self):
        """The re-check, not the token, is what enforces Gate 1."""
        github = FakeGitHub()
        request_id = self.instruct(github)
        (self.root / "state" / "human-approvals.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(PublicationConflict) as caught:
            ceo_publish.publish(
                self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
                request_id=request_id, github=github,
            )
        self.assertIn("no Gate 1 approval is recorded for this card", str(caught.exception))
        self.assertEqual(github.merges, [])

    # 2 — a moved branch or base returns 409 and merges nothing
    def test_a_moved_head_returns_conflict_and_merges_nothing(self):
        github = FakeGitHub()
        request_id = self.instruct(github)
        github.refs["cmo-changes"] = "d" * 40  # branch moves after the human clicks
        with self.assertRaises(PublicationConflict) as caught:
            ceo_publish.publish(
                self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
                request_id=request_id, github=github,
            )
        self.assertIn("branch moved", str(caught.exception))
        self.assertEqual(github.merges, [])

    def test_a_moved_base_returns_conflict_and_merges_nothing(self):
        github = FakeGitHub()
        request_id = self.instruct(github)
        github.refs["main"] = "e" * 40  # main moves after the preview was built
        with self.assertRaises(PublicationConflict) as caught:
            ceo_publish.publish(
                self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
                request_id=request_id, github=github,
            )
        self.assertIn("main moved since the preview was built", str(caught.exception))
        self.assertEqual(github.merges, [])

    # 3 — missing evidence disables the button with the reason shown
    def test_missing_lighthouse_evidence_blocks_with_a_visible_reason(self):
        (self.root / "state" / "website-metrics" / "TASK-500.preview.json").unlink()
        check = ceo_publish.preflight(self.root, "TASK-500", github=FakeGitHub())
        self.assertFalse(check.eligible)
        self.assertIn(
            "baseline-to-preview Lighthouse evidence is missing or incomplete", check.blockers
        )

    def test_incomplete_evidence_is_treated_as_missing_not_as_success(self):
        (self.root / "state" / "website-metrics" / "TASK-500.preview.json").write_text(
            json.dumps({"status": "failed", "phase": "preview", "pages": []}), encoding="utf-8"
        )
        check = ceo_publish.preflight(self.root, "TASK-500", github=FakeGitHub())
        self.assertFalse(check.eligible)
        self.assertIn(
            "baseline-to-preview Lighthouse evidence is missing or incomplete", check.blockers
        )

    # 4 — no agent path can publish without a human click
    def test_publish_without_a_single_use_human_instruction_is_refused(self):
        github = FakeGitHub()
        check = ceo_publish.preflight(self.root, "TASK-500", github=github)
        self.assertTrue(check.eligible, check.blockers)  # everything else is satisfied
        with self.assertRaises(PublicationConflict):
            ceo_publish.publish(
                self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
                request_id="", github=github,
            )
        self.assertEqual(github.merges, [])

    def test_an_instruction_is_single_use_and_cannot_be_replayed(self):
        github = FakeGitHub()
        request_id = self.instruct(github)
        first = ceo_publish.publish(
            self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
            request_id=request_id, github=github,
        )
        self.assertEqual(first["result"], "merged")
        with self.assertRaises(PublicationConflict):
            ceo_publish.publish(
                self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
                request_id=request_id, github=github,
            )
        self.assertEqual(len(github.merges), 1)

    def test_an_instruction_cannot_be_used_by_another_identity(self):
        github = FakeGitHub()
        request_id = self.instruct(github)
        with self.assertRaises(PublicationConflict):
            ceo_publish.publish(
                self.root, "TASK-500", actor="someone-else@itarang.com", role="ceo",
                request_id=request_id, github=github,
            )
        self.assertEqual(github.merges, [])

    def test_an_unauthenticated_actor_can_never_mint_or_use_an_instruction(self):
        github = FakeGitHub()
        with self.assertRaises(PublicationRefused):
            ceo_publish.issue_request(self.root, "TASK-500", actor="   ", commit=APPROVED_COMMIT)
        with self.assertRaises(PublicationRefused):
            ceo_publish.publish(
                self.root, "TASK-500", actor="", role="ceo",
                request_id="anything", github=github,
            )
        self.assertEqual(github.merges, [])


class GateTwoSuccessTests(unittest.TestCase, ):
    """The action, so the refusals above are proved against a path that does work."""

    setUp = GateTwoRefusalTests.setUp
    write_evidence = GateTwoRefusalTests.write_evidence
    approve = GateTwoRefusalTests.approve
    instruct = GateTwoRefusalTests.instruct
    log_lines = GateTwoRefusalTests.log_lines

    def test_a_human_click_merges_once_and_names_the_human_in_log_and_trailer(self):
        github = FakeGitHub()
        request_id = self.instruct(github)
        outcome = ceo_publish.publish(
            self.root, "TASK-500", actor="ceo@itarang.com", role="ceo",
            request_id=request_id, github=github,
        )
        self.assertEqual(outcome["result"], "merged")
        self.assertEqual(len(github.merges), 1)
        self.assertEqual(github.merges[0]["head"], APPROVED_COMMIT)
        self.assertEqual(github.merges[0]["base"], "main")
        self.assertIn("Published-by: ceo@itarang.com", github.merges[0]["message"])

        recorded = [line for line in self.log_lines() if line.get("event") == "publication"]
        self.assertEqual(len(recorded), 1)
        self.assertEqual(recorded[0]["actor"], "ceo@itarang.com")
        self.assertEqual(recorded[0]["approved_commit"], APPROVED_COMMIT)
        self.assertEqual(recorded[0]["request_id"], request_id)
        self.assertEqual(recorded[0]["merge_commit"], "c" * 40)

    def test_preflight_pairs_baseline_and_preview_scores_for_display(self):
        check = ceo_publish.preflight(self.root, "TASK-500", github=FakeGitHub())
        self.assertTrue(check.eligible, check.blockers)
        self.assertEqual(check.comparison, [{
            "path": "/blog",
            "performance_before": 43.0,
            "performance_after": 58.0,
            "weight_before": 500000,
            "weight_after": 500000,
        }])


if __name__ == "__main__":
    unittest.main()
