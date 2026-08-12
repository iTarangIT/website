"""The loop that starts a run when a topic is approved.

Every test here answers one of the invariants the chain depends on. They use a real
`tasks.md` on disk and a real `BoardStore`, and stub only the subprocess — the thing
under test is which card gets picked and what happens to a card nobody is writing,
not whether the writer works.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cmo_runtime.agent_runtime import BoardStore
from cmo_runtime.content_worker import (
    ContentWorker,
    eligible_cards,
    revision_cards,
)


def fresh() -> str:
    """A card touched just now — the normal case, and not stranded by anybody."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def card(
    task_id: str,
    title: str,
    *,
    skill: str = "content",
    priority: str = "medium",
    stage: str = "approved",
    change_status: str = "queued",
    attachment: str = "none",
    work_type: str = "",
    updated: str = "",
    extra: str = "",
) -> str:
    updated = updated or fresh()
    lines = [
        f"### {task_id} — {title}",
        "",
        f"- ID: {task_id}",
        f"- Title: {title}",
        f"- Owner: {skill}",
        f"- Skill: {skill}",
        f"- Priority: {priority}",
        f"- Status: Backlog",
        "- Objective: Write the approved topic.",
        f"- Attachment: {attachment}",
        f"- Topic stage: {stage}",
        f"- Change status: {change_status}",
        "- Latest summary: none",
        f"- Last updated: {updated}",
        f"- Updated: {updated}",
    ]
    if work_type:
        lines.append(f"- Work type: {work_type}")
    if extra:
        lines.append(extra)
    return "\n".join(lines)


def board(backlog: list[str], in_progress: list[str] | None = None) -> str:
    return "\n\n".join(
        [
            "# Marketing Operations Kanban",
            "## Backlog",
            "\n\n".join(backlog) if backlog else "_No tasks._",
            "## In Progress",
            "\n\n".join(in_progress or []) if in_progress else "_No tasks._",
            "## CMO Review",
            "_No tasks._",
            "## Human Approval",
            "_No tasks._",
            "## Completed",
            "_No tasks._",
            "",
        ]
    )


class WorkerFixture(unittest.TestCase):
    def build(self, text: str, **options: object) -> tuple[ContentWorker, list[list[str]]]:
        root = Path(tempfile.mkdtemp())
        (root / "state").mkdir()
        (root / "tasks.md").write_text(text, encoding="utf-8")
        commands: list[list[str]] = []

        def runner(command: list[str]) -> int:
            commands.append(list(command))
            return 0

        worker = ContentWorker(
            root,
            runner=runner,
            stale_seconds=float(options.pop("stale_seconds", 1800)),
            now=options.pop("now", None),  # type: ignore[arg-type]
        )
        return worker, commands

    def cards(self, worker: ContentWorker) -> list:
        return worker.board.cards()


class ApprovingATopicStartsARun(WorkerFixture):
    """Invariant 1 — no human shell command stands between approval and the run."""

    def test_an_approved_queued_card_is_started_by_one_tick(self) -> None:
        worker, commands = self.build(board([card("TASK-100", "Battery range in heat")]))

        job = worker.tick()

        self.assertIsNotNone(job)
        self.assertEqual(job.task_id, "TASK-100")
        self.assertEqual(job.kind, "write")
        self.assertEqual(len(commands), 1)
        self.assertIn("content-execute", commands[0])

    def test_a_card_whose_topic_is_not_approved_is_not_started(self) -> None:
        worker, commands = self.build(board([card("TASK-100", "Proposed only", stage="proposed")]))

        self.assertIsNone(worker.tick())
        self.assertEqual(commands, [])

    def test_a_card_that_already_has_an_article_is_not_rewritten(self) -> None:
        worker, commands = self.build(
            board([card("TASK-100", "Already written", attachment="artifacts/TASK-100-content.md")])
        )

        self.assertIsNone(worker.tick())
        self.assertEqual(commands, [])


class WhatTheWorkerRefusesToTouch(WorkerFixture):
    """Held cards, ops cards and board summaries are somebody else's business."""

    def test_a_held_card_is_skipped(self) -> None:
        # TASK-085..088 on the live board carry exactly this: a CEO hold.
        worker, commands = self.build(board([card("TASK-085", "Held by instruction", change_status="blocked")]))

        self.assertIsNone(worker.tick())
        self.assertEqual(commands, [])

    def test_a_card_pending_a_human_decision_is_skipped(self) -> None:
        worker, _ = self.build(
            board([card("TASK-083", "Held for proposal review", change_status="pending human decision")])
        )
        self.assertIsNone(worker.tick())

    def test_an_ops_card_is_skipped(self) -> None:
        # TASK-082 — install the GA4 tag. Not the content writer's work.
        worker, _ = self.build(board([card("TASK-082", "Install GA4", skill="ops", stage="")]))
        self.assertIsNone(worker.tick())

    def test_an_internal_board_summary_is_skipped(self) -> None:
        worker, _ = self.build(
            board([card("TASK-069", "Board state summary", work_type="internal-board-summary")])
        )
        self.assertIsNone(worker.tick())

    def test_a_failed_card_is_not_retried_on_its_own(self) -> None:
        """A retry is Sanchit's click; the loop must not spin on a failure."""
        worker, commands = self.build(board([card("TASK-084", "Failed nine times", change_status="write failed")]))

        self.assertIsNone(worker.tick())
        self.assertEqual(commands, [])


class BoardOrderHolds(WorkerFixture):
    def test_the_first_eligible_card_in_board_order_is_taken(self) -> None:
        worker, _ = self.build(
            board([card("TASK-084", "First on the board"), card("TASK-100", "Second on the board")])
        )

        self.assertEqual(worker.tick().task_id, "TASK-084")

    def test_a_priority_marker_moves_a_card_up_and_nothing_else_does(self) -> None:
        worker, _ = self.build(
            board(
                [
                    card("TASK-084", "First on the board"),
                    card("TASK-100", "Marked high", priority="high"),
                    card("TASK-101", "Third on the board"),
                ]
            )
        )

        picked = [item.task_id for item in eligible_cards(self.cards(worker))]
        self.assertEqual(picked, ["TASK-100", "TASK-084", "TASK-101"])


class OneAtATime(WorkerFixture):
    """Invariant 2 — a second approval queues, it does not run."""

    def test_nothing_starts_while_a_card_is_in_progress(self) -> None:
        active = card("TASK-084", "Being written", change_status="executing").replace(
            "- Status: Backlog", "- Status: In Progress"
        )
        worker, commands = self.build(board([card("TASK-100", "Queued behind it")], in_progress=[active]))

        self.assertIsNone(worker.tick())
        self.assertEqual(commands, [])

    def test_the_queued_card_is_still_eligible_and_runs_once_the_lane_clears(self) -> None:
        active = card("TASK-084", "Being written", change_status="executing").replace(
            "- Status: Backlog", "- Status: In Progress"
        )
        worker, commands = self.build(board([card("TASK-100", "Queued behind it")], in_progress=[active]))
        self.assertIsNone(worker.tick())

        (worker.root / "tasks.md").write_text(board([card("TASK-100", "Queued behind it")]), encoding="utf-8")

        self.assertEqual(worker.tick().task_id, "TASK-100")
        self.assertEqual(len(commands), 1)


class ACrashDoesNotStrandACard(WorkerFixture):
    """Invariant 3 — a card cannot sit In Progress forever with nobody behind it."""

    def stranded_board(self, updated: str) -> str:
        active = card("TASK-084", "Abandoned mid-write", change_status="executing", updated=updated).replace(
            "- Status: Backlog", "- Status: In Progress"
        )
        return board([card("TASK-100", "Waiting behind it")], in_progress=[active])

    def test_a_long_stranded_card_returns_to_backlog_with_a_reason(self) -> None:
        worker, _ = self.build(self.stranded_board("2026-08-12T00:00:00Z"), stale_seconds=1800)
        worker.now = lambda: datetime(2026, 8, 12, 6, 0, 0, tzinfo=UTC)

        returned = worker.recover_stranded(self.cards(worker))

        self.assertEqual(returned, ["TASK-084"])
        recovered = worker.board.get("TASK-084")
        self.assertEqual(recovered.section, "Backlog")
        self.assertEqual(recovered.fields["Change status"], "write failed")
        self.assertIn("stopped without finishing", recovered.fields["Latest summary"])

    def test_a_card_that_only_just_started_is_left_alone(self) -> None:
        """A hand-run `content-execute` has no heartbeat here and must survive."""
        worker, _ = self.build(self.stranded_board("2026-08-12T05:59:00Z"), stale_seconds=1800)
        worker.now = lambda: datetime(2026, 8, 12, 6, 0, 0, tzinfo=UTC)

        self.assertEqual(worker.recover_stranded(self.cards(worker)), [])
        self.assertEqual(worker.board.get("TASK-084").section, "In Progress")

    def test_a_live_worker_keeps_its_own_card(self) -> None:
        worker, _ = self.build(self.stranded_board("2026-08-12T00:00:00Z"), stale_seconds=1800)
        worker.now = lambda: datetime(2026, 8, 12, 6, 0, 0, tzinfo=UTC)
        (worker.root / "state" / "content-worker.json").write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "task_id": "TASK-084",
                    "kind": "write",
                    "started_at": "2026-08-12T05:59:00Z",
                    "updated_at": "2026-08-12T05:59:30Z",
                }
            ),
            encoding="utf-8",
        )

        self.assertEqual(worker.recover_stranded(self.cards(worker)), [])
        self.assertEqual(worker.board.get("TASK-084").section, "In Progress")

    def test_recovery_unblocks_the_card_waiting_behind_it(self) -> None:
        worker, commands = self.build(self.stranded_board("2026-08-12T00:00:00Z"), stale_seconds=1800)
        worker.now = lambda: datetime(2026, 8, 12, 6, 0, 0, tzinfo=UTC)

        job = worker.tick()

        self.assertEqual(job.task_id, "TASK-100")
        self.assertEqual(len(commands), 1)


class AskingForChangesStartsTheRewrite(WorkerFixture):
    """Invariant 6 — submitting a comment is the whole of it."""

    def revision_board(self) -> str:
        asked = card(
            "TASK-075",
            "Article he commented on",
            change_status="revision requested",
            attachment="artifacts/TASK-075-content.md",
            extra="- Revision round: 1",
        ).replace("- Status: Backlog", "- Status: Human Approval")
        return "\n\n".join(
            [
                "# Marketing Operations Kanban",
                "## Backlog",
                card("TASK-100", "A queued write"),
                "## In Progress",
                "_No tasks._",
                "## CMO Review",
                "_No tasks._",
                "## Human Approval",
                asked,
                "## Completed",
                "_No tasks._",
                "",
            ]
        )

    def test_a_revision_request_starts_a_revise_run(self) -> None:
        worker, commands = self.build(self.revision_board())

        job = worker.tick()

        self.assertEqual(job.kind, "revise")
        self.assertEqual(job.task_id, "TASK-075")
        self.assertIn("content-revise", commands[0])
        self.assertIn("TASK-075", commands[0])

    def test_a_rewrite_outranks_a_fresh_write(self) -> None:
        """He is waiting on the reply; an unstarted topic is not waiting on anything."""
        worker, _ = self.build(self.revision_board())

        self.assertEqual(worker.next_job(self.cards(worker)).task_id, "TASK-075")

    def test_a_revision_is_not_started_while_something_is_in_progress(self) -> None:
        text = self.revision_board().replace("## In Progress\n\n_No tasks._", "## In Progress\n\n" + card(
            "TASK-084", "Mid-write", change_status="executing"
        ).replace("- Status: Backlog", "- Status: In Progress"))
        worker, commands = self.build(text)

        self.assertIsNone(worker.tick())
        self.assertEqual(commands, [])


class AFailureDoesNotBecomeALoop(WorkerFixture):
    """What the first live run of this worker actually did.

    It found cards marked `revision requested` with no round and no recorded
    comment. Each pick-up moved the card to In Progress, refused, and moved it
    back — and because a tick that started a job did not sleep, it did that 147
    times in fifteen seconds. Two separate defects, so two separate guards and one
    test each. The cards that triggered it have since been cleared, which is
    exactly why the guards are tested here rather than trusted to the data.
    """

    def legacy_board(self) -> str:
        stale = card(
            "TASK-037",
            "A revision marker from before the flow existed",
            change_status="revision requested",
            attachment="artifacts/TASK-037-content.md",
        ).replace("- Status: Backlog", "- Status: CMO Review")
        return "\n\n".join(
            [
                "# Marketing Operations Kanban",
                "## Backlog",
                card("TASK-100", "A queued write"),
                "## In Progress",
                "_No tasks._",
                "## CMO Review",
                stale,
                "## Human Approval",
                "_No tasks._",
                "## Completed",
                "_No tasks._",
                "",
            ]
        )

    def test_a_revision_request_with_no_round_is_never_picked_up(self) -> None:
        worker, commands = self.build(self.legacy_board())

        self.assertEqual(revision_cards(self.cards(worker)), [])
        job = worker.tick()

        self.assertEqual(job.task_id, "TASK-100", "the unservable revision was preferred")
        self.assertIn("content-execute", commands[0])

    def test_the_unservable_card_is_left_exactly_where_it_was(self) -> None:
        worker, _ = self.build(self.legacy_board())
        before = (worker.root / "tasks.md").read_text(encoding="utf-8")

        worker.tick()
        worker.tick()

        stale = worker.board.get("TASK-037")
        self.assertEqual(stale.section, "CMO Review")
        self.assertEqual(stale.fields["Change status"], "revision requested")
        self.assertIn("### TASK-037", before)

    def test_a_card_whose_run_fails_is_not_offered_again_immediately(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "state").mkdir()
        (root / "tasks.md").write_text(board([card("TASK-100", "Fails instantly")]), encoding="utf-8")
        attempts: list[list[str]] = []

        worker = ContentWorker(root, runner=lambda command: attempts.append(command) or 1)

        self.assertIsNotNone(worker.tick())
        self.assertEqual(len(attempts), 1)
        # Same board, same card, immediately afterwards: nothing runs.
        self.assertIsNone(worker.tick())
        self.assertIsNone(worker.tick())
        self.assertEqual(len(attempts), 1, "a failing card was retried in a tight loop")

    def test_the_backoff_grows_and_clears_on_success(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "state").mkdir()
        (root / "tasks.md").write_text(board([card("TASK-100", "Fails then works")]), encoding="utf-8")
        outcomes = [1, 1]

        def runner(command: list[str]) -> int:
            return outcomes.pop(0) if outcomes else 0

        worker = ContentWorker(root, runner=runner)
        clock = 1000.0

        worker.tick()
        first = worker._cooling["TASK-100"][1] - clock
        worker._cooling["TASK-100"] = (1, 0.0)  # let the cooldown lapse
        worker.tick()
        second = worker._cooling["TASK-100"][1] - clock

        self.assertGreater(second, first, "the backoff did not grow after a second failure")
        worker._cooling["TASK-100"] = (2, 0.0)
        worker.tick()
        self.assertNotIn("TASK-100", worker._cooling, "a success left the card in backoff")


class TheHeartbeatSaysWhatIsHappening(WorkerFixture):
    def test_a_running_job_is_visible_in_the_heartbeat_while_it_runs(self) -> None:
        seen: list[dict] = []
        root = Path(tempfile.mkdtemp())
        (root / "state").mkdir()
        (root / "tasks.md").write_text(board([card("TASK-100", "Being written")]), encoding="utf-8")

        worker = ContentWorker(root, runner=lambda command: seen.append(worker.read_heartbeat()) or 0)
        worker.tick()

        self.assertEqual(seen[0]["task_id"], "TASK-100")
        self.assertEqual(seen[0]["kind"], "write")
        self.assertTrue(seen[0]["started_at"])
        self.assertEqual(seen[0]["pid"], os.getpid())

    def test_the_heartbeat_is_cleared_when_the_run_ends(self) -> None:
        worker, _ = self.build(board([card("TASK-100", "Being written")]))
        worker.tick()

        self.assertEqual(worker.read_heartbeat()["task_id"], "")

    def test_the_heartbeat_is_cleared_even_when_the_run_raises(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "state").mkdir()
        (root / "tasks.md").write_text(board([card("TASK-100", "Being written")]), encoding="utf-8")

        def explode(command: list[str]) -> int:
            raise RuntimeError("the writer died")

        worker = ContentWorker(root, runner=explode)
        with self.assertRaises(RuntimeError):
            worker.tick()

        self.assertEqual(worker.read_heartbeat()["task_id"], "")


if __name__ == "__main__":
    unittest.main()
