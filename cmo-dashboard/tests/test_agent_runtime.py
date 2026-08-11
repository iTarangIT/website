from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cmo_runtime.agent_runtime import (
    AuthorityError,
    MetricRequiredError,
    Runtime,
    RunAccountant,
)
from cmo_runtime.skill_loader import SkillLoader
from cmo_runtime.task_file import ActiveTaskError, validate_structure


SECTIONS = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")


def card(
    task_id: str,
    section: str,
    *,
    title: str = "Internal board summary",
    skill: str = "content",
    metric: str = "One verified board summary produced.",
    change: str = "ready",
    attachment: str = "none",
    extra: str = "",
) -> str:
    suffix = f"\n{extra.strip()}" if extra.strip() else ""
    return f"""### {task_id} — {title}

- ID: {task_id}
- Title: {title}
- Owner: {skill}
- Priority: high
- Status: {section}
- Start date: not started
- Completed date: not completed
- Objective: Produce a tool-free internal summary from tasks.md alone.
- Acceptance criteria:
  - State lane counts.
- Latest summary: Ready for commissioning.
- Last updated: 2026-08-04T10:00:00Z
- Skill: {skill}
- Description: Produce a tool-free internal summary from tasks.md alone.
- Attachment: {attachment}
- Metric: {metric}
- Tag: action to be taken by: cmo
- Updated: 2026-08-04T10:00:00Z
- Change status: {change}{suffix}
"""


def board(*cards: tuple[str, str]) -> str:
    grouped = {name: [] for name in SECTIONS}
    for section, text in cards:
        grouped[section].append(text.strip())
    parts = ["# Test Board", ""]
    for section in SECTIONS:
        parts.extend([f"## {section}", ""])
        if grouped[section]:
            parts.extend(["\n\n".join(grouped[section]), ""])
    return "\n".join(parts)


class RuntimeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "state").mkdir()
        (self.root / "cmo_skills").mkdir()
        (self.root / "artifacts").mkdir()
        for skill in ("seo", "content", "social", "ads"):
            (self.root / "cmo_skills" / f"{skill}.skill").write_text(
                f"SKILL: {skill}\nSTATUS: enabled\n", encoding="utf-8"
            )
        (self.root / "cmo_skills" / "ops.skill").write_text(
            "SKILL: ops\nSTATUS: skill disabled\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def runtime(self, text: str, *, loader: SkillLoader | None = None) -> Runtime:
        (self.root / "tasks.md").write_text(text, encoding="utf-8")
        return Runtime(self.root, skill_loader=loader)

    def test_plan_with_review_queue_adds_nothing_and_loads_no_skill(self) -> None:
        reads: list[Path] = []
        loader = SkillLoader(self.root / "cmo_skills", reader=lambda path: reads.append(path) or path.read_text())
        runtime = self.runtime(
            board(
                ("Backlog", card("TASK-001", "Backlog")),
                ("CMO Review", card("TASK-002", "CMO Review", attachment="artifact.md")),
            ),
            loader=loader,
        )
        before = (self.root / "tasks.md").read_bytes()
        result = runtime.plan("2026-08-04")
        self.assertEqual(result.created, [])
        self.assertIn("clear the CMO Review queue", result.reason)
        self.assertEqual(reads, [])
        self.assertEqual((self.root / "tasks.md").read_bytes(), before)

    def test_execute_creates_artifact_and_moves_one_card_to_review(self) -> None:
        runtime = self.runtime(board(("Backlog", card("TASK-001", "Backlog", extra="- Work type: internal-board-summary\n- Required tool: none\n- KPI gate: not-required"))))
        result = runtime.execute()
        self.assertEqual(result.task_id, "TASK-001")
        self.assertEqual(result.status, "pending CMO review")
        self.assertTrue((self.root / "artifacts" / "TASK-001-content.md").is_file())
        text = (self.root / "tasks.md").read_text()
        self.assertIn("## CMO Review\n\n### TASK-001", text)
        self.assertIn("- Tag: action to be taken by: cmo", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])

    def test_execute_refuses_when_another_card_is_active_before_skill_read(self) -> None:
        reads: list[Path] = []
        loader = SkillLoader(self.root / "cmo_skills", reader=lambda path: reads.append(path) or path.read_text())
        runtime = self.runtime(
            board(
                ("Backlog", card("TASK-001", "Backlog")),
                ("In Progress", card("TASK-002", "In Progress")),
            ),
            loader=loader,
        )
        before = (self.root / "tasks.md").read_bytes()
        with self.assertRaisesRegex(ActiveTaskError, "TASK-002 is already in In Progress"):
            runtime.execute()
        self.assertEqual(reads, [])
        self.assertEqual((self.root / "tasks.md").read_bytes(), before)

    def test_review_send_back_escalate_and_flag(self) -> None:
        send_artifact = self.root / "artifacts" / "send.md"
        send_artifact.write_text("Incomplete draft.\n", encoding="utf-8")
        good_artifact = self.root / "artifacts" / "good.md"
        good_artifact.write_text(
            "# Summary\n\nDecision bullets:\n- Shows current lane counts.\n- Separates open and completed work.\n- Uses tasks.md as its only evidence.\n",
            encoding="utf-8",
        )
        flag_artifact = self.root / "artifacts" / "flag.md"
        flag_artifact.write_text("PENDING HUMAN DECISION: choose reporting date.\n", encoding="utf-8")
        runtime = self.runtime(
            board(
                ("CMO Review", card("TASK-001", "CMO Review", attachment=str(send_artifact))),
                ("CMO Review", card("TASK-002", "CMO Review", attachment=str(good_artifact))),
                ("CMO Review", card("TASK-003", "CMO Review", attachment=str(flag_artifact))),
            )
        )
        self.assertEqual(runtime.review("TASK-001").outcome, "send-back")
        escalated = runtime.review("TASK-002")
        self.assertEqual(escalated.outcome, "escalate")
        self.assertIn("TAG:          pending", escalated.approval_card)
        self.assertEqual(runtime.review("TASK-003").outcome, "flag")
        text = (self.root / "tasks.md").read_text()
        self.assertIn("## Backlog\n\n### TASK-001", text)
        self.assertIn("## Human Approval\n\n### TASK-002", text)
        self.assertIn("- Change status: pending human decision", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])

    def test_authority_blocks_approved_and_completed(self) -> None:
        runtime = self.runtime(board(("Human Approval", card("TASK-001", "Human Approval"))))
        with self.assertRaisesRegex(AuthorityError, "Only a human"):
            runtime.mark_approved("TASK-001")
        with self.assertRaisesRegex(AuthorityError, "cannot mark tasks completed"):
            runtime.mark_completed("TASK-001")

    def test_metric_gate_and_human_comment_requeues(self) -> None:
        artifact = self.root / "artifacts" / "good.md"
        artifact.write_text(
            "Decision bullets:\n- Shows lane counts.\n- Uses one board source.\n- Provides an auditable summary.\n",
            encoding="utf-8",
        )
        runtime = self.runtime(
            board(("Human Approval", card("TASK-001", "Human Approval", metric="none", attachment=str(artifact))))
        )
        with self.assertRaises(MetricRequiredError):
            runtime.approval_card("TASK-001")
        runtime.comment("TASK-001", "State the review date explicitly.")
        text = (self.root / "tasks.md").read_text()
        self.assertIn("## Backlog\n\n### TASK-001", text)
        self.assertIn("- Change status: revision requested", text)
        self.assertIn("- Human decision comment: State the review date explicitly.", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])

    def test_refusal_paths_are_recorded_without_artifact(self) -> None:
        runtime = self.runtime(
            board(("Backlog", card("TASK-001", "Backlog", extra="- Required tool: unavailable-tool\n- KPI gate: approved")))
        )
        result = runtime.execute()
        self.assertEqual(result.status, "blocked")
        self.assertFalse((self.root / "artifacts" / "TASK-001-content.md").exists())
        self.assertIn("- Change status: blocked", (self.root / "tasks.md").read_text())

        runtime = self.runtime(
            board(("Backlog", card("TASK-002", "Backlog", extra="- Required tool: none\n- KPI gate: pending")))
        )
        result = runtime.execute()
        self.assertEqual(result.status, "pending human decision")
        self.assertFalse((self.root / "artifacts" / "TASK-002-content.md").exists())
        self.assertIn("- Change status: pending human decision", (self.root / "tasks.md").read_text())

    def test_accounting_is_appended_only_after_operation_returns(self) -> None:
        log = self.root / "logs" / "spend.log"
        accountant = RunAccountant(log)
        observed: list[bool] = []

        def operation() -> str:
            observed.append(log.exists())
            return "done"

        result = accountant.run("plan", "none", operation)
        self.assertEqual(result, "done")
        self.assertEqual(observed, [False])
        entry = json.loads(log.read_text().splitlines()[-1])
        self.assertEqual(entry["run_type"], "plan")
        self.assertEqual(entry["status"], "completed")
        self.assertIn("approximate_cost_inr", entry)


if __name__ == "__main__":
    unittest.main()
