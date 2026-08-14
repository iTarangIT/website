from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, "/opt/hermes")

from cmo_runtime.approval_cards import (
    APPROVAL_TARGET,
    ApprovalCardError,
    ApprovalCardEmitter,
    DiscordApprovalReplyHandler,
)
from cmo_runtime.task_file import validate_structure
from gateway.config import Platform
from gateway.platforms.base import BasePlatformAdapter
from gateway.session import SessionSource


SECTIONS = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")
APPROVER = "1534458345119944767"
COMMIT = "a" * 40


def card(
    task_id: str = "TASK-017",
    *,
    metric: str = "Increase qualified organic visits by measuring search impressions.",
    bullets: tuple[str, ...] = (
        "Adds a clear service explanation for battery teams.",
        "Makes the next action obvious for interested visitors.",
        "Provides an evidence file for the approval decision.",
    ),
    attachment: str = "artifacts/TASK-017/report.pdf",
    change_type: str = "",
    commit: str = "",
) -> str:
    lines = [
        f"### {task_id} — Search landing-page approval",
        f"- ID: {task_id}",
        "- Title: Search landing-page approval",
        "- Owner: seo",
        "- Priority: high",
        "- Status: Human Approval",
        "- Start date: 2026-08-05T08:00:00Z",
        "- Completed date: not completed",
        "- Objective: Improve qualified search traffic.",
        "- Acceptance criteria:",
        "  - Human approval is recorded once.",
        "- Decision summary:",
    ]
    lines.extend(f"  - {bullet}" for bullet in bullets)
    lines.extend(
        [
            "- Latest summary: Ready for human approval.",
            "- Last updated: 2026-08-05T09:00:00Z",
            "- Skill: seo",
            "- Description: Search landing-page decision packet.",
            f"- Attachment: {attachment}",
            f"- Metric: {metric}",
            "- Tag: action to be taken by: human",
            "- Updated: 2026-08-05T09:00:00Z",

        ]
    )
    if change_type:
        lines.append(f"- Change type: {change_type}")
    if commit:
        lines.append(f"- Change commit: {commit}")
    return "\n".join(lines)


def board(task_card: str) -> str:
    chunks = ["# Approval-card test board"]
    for section in SECTIONS:
        chunks.append(f"## {section}")
        if section == "Human Approval":
            chunks.append(task_card)
    return "\n\n".join(chunks) + "\n"


def event(*, user_id: str = APPROVER, text: str = "approve", reply_to: str = "message-1"):
    source = SessionSource(
        platform=Platform.DISCORD,
        chat_id=APPROVAL_TARGET.split(":", 1)[1],
        chat_type="channel",
        user_id=user_id,
    )
    return SimpleNamespace(
        source=source,
        text=text,
        reply_to_message_id=reply_to,
        reply_to_is_own_message=True,
    )


class ApprovalCardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "state").mkdir()
        (self.root / "logs").mkdir()
        artifact = self.root / "artifacts" / "TASK-017" / "report.pdf"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"%PDF-1.4\nfixture\n")
        (self.root / "tasks.md").write_text(board(card()), encoding="utf-8")
        self.send = Mock(return_value={"success": True, "message_id": "message-1"})
        self.emitter = ApprovalCardEmitter(
            self.root,
            sender=self.send,
            media_validator=lambda _path: True,
        )

    def test_emits_exact_five_fields_in_order_and_native_media(self) -> None:
        result = self.emitter.emit("TASK-017")

        self.assertEqual(result.message_id, "message-1")
        self.send.assert_called_once()
        target, message = self.send.call_args.args
        self.assertEqual(target, APPROVAL_TARGET)
        labels = [
            line.split(":", 1)[0] + ":"
            for line in message.splitlines()
            if line and not line.startswith("  - ") and not line.startswith("MEDIA:")
        ]
        self.assertEqual(
            labels,
            ["TASK NAME:", "DESCRIPTION:", "ATTACHMENT:", "WHAT IT HELPS:", "TAG:"],
        )
        media, cleaned = BasePlatformAdapter.extract_media(message)
        self.assertEqual(
            media,
            [(str(self.root / "artifacts" / "TASK-017" / "report.pdf"), False)],
        )
        self.assertNotIn("MEDIA:", cleaned)
        self.assertIn("ATTACHMENT:   report.pdf (attached to this Discord card)", cleaned)
        self.assertTrue(message.rstrip().endswith("TAG:          pending"))

    def test_non_website_card_without_change_commit_is_emittable(self) -> None:
        result = self.emitter.emit("TASK-017")

        self.assertEqual(result.message_id, "message-1")
        registry = json.loads((self.root / "state" / "approval-card.json").read_text(encoding="utf-8"))
        self.assertEqual(registry["active"]["card_commit_sha"], "")

    def test_website_card_without_change_commit_is_refused(self) -> None:
        (self.root / "tasks.md").write_text(
            board(card(change_type="website")),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ApprovalCardError, "valid Change commit"):
            self.emitter.emit("TASK-017")

        self.send.assert_not_called()

    def test_no_metric_refuses_without_sending_or_moving_task(self) -> None:
        original = board(card(metric="not set"))
        (self.root / "tasks.md").write_text(original, encoding="utf-8")

        with self.assertRaisesRegex(ApprovalCardError, "measurable metric"):
            self.emitter.emit("TASK-017")

        self.send.assert_not_called()
        self.assertEqual((self.root / "tasks.md").read_text(encoding="utf-8"), original)

    def test_fewer_than_three_bullets_refuses_without_sending(self) -> None:
        (self.root / "tasks.md").write_text(
            board(card(bullets=("One business change.", "A second business change."))),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ApprovalCardError, "3-5 decision bullets"):
            self.emitter.emit("TASK-017")

        self.send.assert_not_called()

    def test_media_path_rejected_by_hermes_refuses_without_sending(self) -> None:
        emitter = ApprovalCardEmitter(
            self.root,
            sender=self.send,
            media_validator=lambda _path: False,
        )

        with self.assertRaisesRegex(ApprovalCardError, "not allowed by Hermes MEDIA delivery"):
            emitter.emit("TASK-017")

        self.send.assert_not_called()

    def test_only_one_card_can_be_active(self) -> None:
        self.emitter.emit("TASK-017")
        with self.assertRaisesRegex(ApprovalCardError, "already active"):
            self.emitter.emit("TASK-017")
        self.send.assert_called_once()

    def test_unauthorized_reply_is_ignored(self) -> None:
        self.emitter.emit("TASK-017")
        handler = DiscordApprovalReplyHandler(self.root, approver_id=APPROVER)

        outcome = handler.handle(event(user_id="someone-else"))

        self.assertEqual(outcome, {"action": "skip", "reason": "approval-card-unauthorized"})
        self.assertFalse((self.root / "state" / "human-approvals.json").exists())
        self.assertIn("- Status: Human Approval", (self.root / "tasks.md").read_text(encoding="utf-8"))

    def test_non_website_approval_records_decision_and_completes_card(self) -> None:
        self.emitter.emit("TASK-017")
        handler = DiscordApprovalReplyHandler(self.root, approver_id=APPROVER)

        outcome = handler.handle(event(text="approve"))

        self.assertEqual(outcome, {"action": "skip", "reason": "approval-card-decided"})
        text = (self.root / "tasks.md").read_text(encoding="utf-8")
        completed = text.index("## Completed")
        task = text.index("### TASK-017")
        self.assertLess(completed, task)
        self.assertIn("- Status: Completed", text)
        self.assertNotIn("- Status: In Progress", text)
        self.assertIn("- Human decision: approve", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])
        state = json.loads((self.root / "state" / "human-approvals.json").read_text(encoding="utf-8"))
        self.assertEqual(state["TASK-017"]["approver_id"], APPROVER)

    def test_website_gate_1_approval_stays_in_human_approval_and_is_never_completed(self) -> None:
        (self.root / "tasks.md").write_text(
            board(card(change_type="website", commit=COMMIT)),
            encoding="utf-8",
        )
        self.emitter.emit("TASK-017")
        handler = DiscordApprovalReplyHandler(self.root, approver_id=APPROVER)

        outcome = handler.handle(event(text="approve"))

        self.assertEqual(outcome, {"action": "skip", "reason": "approval-card-decided"})
        text = (self.root / "tasks.md").read_text(encoding="utf-8")
        human_approval = text.index("## Human Approval")
        completed = text.index("## Completed")
        task = text.index("### TASK-017")
        self.assertLess(human_approval, task)
        self.assertLess(task, completed)
        self.assertIn("- Status: Human Approval", text)
        self.assertIn("- Change status: awaiting Gate 2", text)
        self.assertNotIn("- Status: Completed", text)
        self.assertNotIn("- Status: In Progress", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])

    def test_comment_is_rejection_reason_and_returns_card_to_backlog(self) -> None:
        self.emitter.emit("TASK-017")
        handler = DiscordApprovalReplyHandler(self.root, approver_id=APPROVER)

        outcome = handler.handle(event(text="State the expected SEO gain more clearly."))

        self.assertEqual(outcome, {"action": "skip", "reason": "approval-card-decided"})
        text = (self.root / "tasks.md").read_text(encoding="utf-8")
        backlog = text.index("## Backlog")
        in_progress = text.index("## In Progress")
        task = text.index("### TASK-017")
        self.assertLess(backlog, task)
        self.assertLess(task, in_progress)
        self.assertIn("- Status: Backlog", text)
        self.assertIn("- Change status: revision requested", text)
        self.assertIn("- Human decision comment: State the expected SEO gain more clearly.", text)
        self.assertEqual(validate_structure(self.root / "tasks.md"), [])

    def test_reply_to_unrelated_message_is_not_intercepted(self) -> None:
        self.emitter.emit("TASK-017")
        handler = DiscordApprovalReplyHandler(self.root, approver_id=APPROVER)
        self.assertIsNone(handler.handle(event(reply_to="other-message")))

    def test_branch_move_voids_reply_and_requires_card_reissue(self) -> None:
        (self.root / "tasks.md").write_text(
            board(card(change_type="website", commit=COMMIT)),
            encoding="utf-8",
        )
        self.emitter.emit("TASK-017")
        tasks_path = self.root / "tasks.md"
        tasks_path.write_text(
            tasks_path.read_text(encoding="utf-8").replace(COMMIT, "b" * 40),
            encoding="utf-8",
        )
        handler = DiscordApprovalReplyHandler(self.root, approver_id=APPROVER)

        outcome = handler.handle(event(text="approve"))

        self.assertEqual(
            outcome,
            {"action": "skip", "reason": "approval-card-reissue-required"},
        )
        self.assertIn("- Status: Human Approval", tasks_path.read_text(encoding="utf-8"))
        registry = json.loads((self.root / "state" / "approval-card.json").read_text(encoding="utf-8"))
        self.assertIsNone(registry["active"])


if __name__ == "__main__":
    unittest.main()
