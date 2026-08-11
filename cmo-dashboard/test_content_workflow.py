from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import dashboard_server  # noqa: F401 — initializes the profile import path
import ceo_actions
from ceo_script import SCRIPT


EMPTY_BOARD = """# CMO Task Board

## Backlog

_No tasks._

## In Progress

_No tasks._

## CMO Review

_No tasks._

## Human Approval

_No tasks._

## Completed

_No tasks._
"""


class ContentWorkflowConsoleTest(unittest.TestCase):
    def make_root(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        (root / "state").mkdir()
        (root / "tasks.md").write_text(EMPTY_BOARD, encoding="utf-8")
        return directory, root

    def test_submitting_topic_is_the_writing_instruction_without_a_topic_gate(self) -> None:
        directory, root = self.make_root()
        self.addCleanup(directory.cleanup)

        result = ceo_actions.add_topics(
            root,
            ["How heat changes usable EV battery range"],
            "sanchit@example.test",
        )

        self.assertEqual(len(result["added"]), 1)
        card = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("- Topic stage: proposed", card)
        self.assertIn("queued for research-first writing", card)
        self.assertIn("no separate topic approval is required", card)
        self.assertIn("Google Search Console Search Analytics API", card)
        self.assertNotIn("blocked on content KPI approval", card)

    def test_topic_screen_has_no_separate_approve_or_decline_control(self) -> None:
        self.assertNotIn("Approve topic", SCRIPT)
        self.assertNotIn("data-topic=", SCRIPT)
        self.assertNotIn("/ceo/api/topic-stage", SCRIPT)
        self.assertIn("Submitting this topic is the instruction to research and write it", SCRIPT)


if __name__ == "__main__":
    unittest.main()
