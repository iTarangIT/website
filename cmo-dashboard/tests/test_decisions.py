from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cmo_runtime.decisions import (
    BranchMovedError,
    DecisionConflict,
    DecisionStore,
    DecisionValidationError,
)
from cmo_runtime.task_file import validate_structure


SECTIONS = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")


def card(task_id: str, section: str = "Human Approval", change_type: str = "") -> str:
    lines = [
            f"### {task_id} — Approval fixture",
            f"- ID: {task_id}",
            "- Title: Approval fixture",
            "- Owner: content",
            "- Priority: high",
            f"- Status: {section}",
            "- Start date: not started",
            "- Completed date: not completed",
            "- Objective: Verify shared decisions.",
            "- Acceptance criteria:",
            "  - The decision is recorded exactly once.",
            "- Latest summary: Pending human approval.",
            "- Last updated: 2026-08-04T10:00:00Z",
            "- Skill: content",
            "- Description: Verify shared decisions.",
            "- Attachment: artifact.md",
            "- Metric: One approval path verified.",
            "- Tag: action to be taken by: human",
            "- Updated: 2026-08-04T10:00:00Z",
    ]
    if change_type:
        lines.append(f"- Change type: {change_type}")
    return "\n".join(lines)


def board(task: str) -> str:
    chunks = ["# Decision test board"]
    for section in SECTIONS:
        chunks.append(f"## {section}")
        if section == "Human Approval":
            chunks.append(task)
    return "\n\n".join(chunks) + "\n"


class DecisionStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "state").mkdir()
        (self.root / "logs").mkdir()
        (self.root / "tasks.md").write_text(board(card("TASK-017")), encoding="utf-8")
        self.clock = lambda: "2026-08-04T13:00:00Z"
        self.store = DecisionStore(self.root, timestamp=self.clock)

    def log_records(self) -> list[dict[str, object]]:
        path = self.root / "logs" / "approvals.log"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_first_decision_wins_and_refusal_names_the_winner(self) -> None:
        result = self.store.decide(
            "TASK-017",
            "approve",
            approver_id="sanchit-1",
            surface="discord",
            card_commit_sha="a" * 40,
            commit_sha="a" * 40,
        )

        with self.assertRaisesRegex(
            DecisionConflict,
            "already decided by sanchit-1 at 2026-08-04T13:00:00Z via discord",
        ):
            self.store.decide(
                "TASK-017",
                "send_back",
                approver_id="dashboard-user",
                surface="dashboard",
                card_commit_sha="a" * 40,
                commit_sha="a" * 40,
                send_back_text="Please revise the business explanation.",
            )

        self.assertTrue(result.recorded)
        state = json.loads((self.root / "state" / "human-approvals.json").read_text(encoding="utf-8"))
        self.assertEqual(
            state["TASK-017"],
            {
                "task_id": "TASK-017",
                "decision": "approve",
                "approver_id": "sanchit-1",
                "surface": "discord",
                "timestamp": "2026-08-04T13:00:00Z",
                "commit_sha": "a" * 40,
                "send_back_text": "",
                # Discord passes none, so none is recorded — and a publish against
                # this record refuses rather than assuming the card is unchanged.
                "publish_fingerprint": "",
            },
        )
        records = self.log_records()
        self.assertEqual([item["outcome"] for item in records], ["recorded", "refused"])
        self.assertEqual(
            records[1]["reason"],
            "already decided by sanchit-1 at 2026-08-04T13:00:00Z via discord",
        )

    def test_concurrent_surfaces_record_one_decision_and_refuse_the_other(self) -> None:
        gate = threading.Barrier(2)

        def submit(approver: str, surface: str) -> str:
            gate.wait()
            try:
                self.store.decide(
                    "TASK-017",
                    "approve",
                    approver_id=approver,
                    surface=surface,
                    card_commit_sha="b" * 40,
                    commit_sha="b" * 40,
                )
            except DecisionConflict as error:
                return str(error)
            return "recorded"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(lambda args: submit(*args), (("sanchit-1", "discord"), ("admin", "dashboard"))))

        self.assertEqual(outcomes.count("recorded"), 1)
        refusal = next(item for item in outcomes if item != "recorded")
        state = json.loads((self.root / "state" / "human-approvals.json").read_text(encoding="utf-8"))
        winner = state["TASK-017"]
        self.assertEqual(
            refusal,
            f"already decided by {winner['approver_id']} at {winner['timestamp']} via {winner['surface']}",
        )
        self.assertEqual([item["outcome"] for item in self.log_records()], ["recorded", "refused"])

    def test_send_back_moves_card_to_backlog_and_sets_revision_requested(self) -> None:
        self.store.decide(
            "TASK-017",
            "send_back",
            approver_id="sanchit-1",
            surface="discord",
            card_commit_sha="c" * 40,
            commit_sha="c" * 40,
            send_back_text="Clarify the customer benefit and revise the opening.",
        )

        text = (self.root / "tasks.md").read_text(encoding="utf-8")
        backlog_start = text.index("## Backlog")
        in_progress_start = text.index("## In Progress")
        task_start = text.index("### TASK-017")
        self.assertLess(backlog_start, task_start)
        self.assertLess(task_start, in_progress_start)
        self.assertIn("- Status: Backlog", text)
        self.assertIn("- Change status: revision requested", text)
        self.assertIn("- Human decision: send back", text)
        self.assertIn("- Human decision comment: Clarify the customer benefit and revise the opening.", text)
        self.assertIn("- Last updated: 2026-08-04T13:00:00Z", text)
        self.assertIn("- Updated: 2026-08-04T13:00:00Z", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])

    def test_branch_move_voids_decision_and_requests_reissue(self) -> None:
        (self.root / "tasks.md").write_text(
            board(card("TASK-017", change_type="website")),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            BranchMovedError,
            f"branch moved from {'d' * 40} to {'e' * 40}; re-issue card with {'e' * 40}",
        ):
            self.store.decide(
                "TASK-017",
                "approve",
                approver_id="sanchit-1",
                surface="discord",
                card_commit_sha="d" * 40,
                commit_sha="e" * 40,
            )

        state = json.loads((self.root / "state" / "human-approvals.json").read_text(encoding="utf-8"))
        self.assertEqual(state, {})
        refusal = self.log_records()[0]
        self.assertEqual(refusal["outcome"], "void")
        self.assertEqual(refusal["reissue_commit_sha"], "e" * 40)

    def test_send_back_requires_a_comment(self) -> None:
        with self.assertRaisesRegex(DecisionValidationError, "send-back text is required"):
            self.store.decide(
                "TASK-017",
                "send_back",
                approver_id="sanchit-1",
                surface="discord",
                card_commit_sha="f" * 40,
                commit_sha="f" * 40,
                send_back_text="",
            )


if __name__ == "__main__":
    unittest.main()
