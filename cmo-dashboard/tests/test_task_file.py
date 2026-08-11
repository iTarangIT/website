from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmo_runtime.task_file import (
    ActiveTaskError,
    Task,
    TaskFile,
)


class TaskFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "tasks.md"
        self.path.write_bytes(b"")
        self.tasks = TaskFile(self.path)

    def task(self, title: str, *, status: str = "queued") -> Task:
        return Task(
            title=title,
            skill="content",
            description="A commissioning-only dummy task.",
            attachment="none",
            metric="Commissioning behavior verified: one result.",
            status=status,
            tag="action to be taken by: cmo",
        )

    def test_next_id_is_sequential_and_write_uses_section_4_schema(self) -> None:
        self.assertEqual(self.tasks.next_id(), "TASK-001")

        task_id = self.tasks.add(self.task("First task"), updated="2026-08-03T09:00:00Z")

        self.assertEqual(task_id, "TASK-001")
        self.assertEqual(self.tasks.next_id(), "TASK-002")
        text = "\n".join(
            line.rstrip()
            for line in self.path.read_text(encoding="utf-8").splitlines()
        )
        self.assertEqual(
            text,
            "\n".join(
                [
                    "### TASK-001",
                    "TITLE:        First task",
                    "SKILL:        content",
                    "DESCRIPTION:  A commissioning-only dummy task.",
                    "ATTACHMENT:   none",
                    "METRIC:       Commissioning behavior verified: one result.",
                    "STATUS:       queued",
                    "TAG:          action to be taken by: cmo",
                    "UPDATED:      2026-08-03T09:00:00Z",
                ]
            ),
        )

    def test_next_id_starts_above_fixed_archived_id_floor(self) -> None:
        floor = self.path.with_name("tasks.id-floor")
        floor.write_text("TASK-065\n", encoding="ascii")
        tasks = TaskFile(self.path)

        self.assertEqual(tasks.next_id(), "TASK-066")
        self.assertEqual(
            tasks.add(
                self.task("First post-archive task"),
                updated="2026-08-03T09:00:00Z",
            ),
            "TASK-066",
        )

    def test_top_open_tasks_stops_after_requested_count(self) -> None:
        for number in range(1, 6):
            self.tasks.add(
                self.task(f"Task {number}"),
                updated=f"2026-08-03T09:00:0{number}Z",
            )

        result = self.tasks.top_open(2)

        self.assertEqual([task.task_id for task in result.tasks], ["TASK-001", "TASK-002"])
        self.assertFalse(result.reached_eof)
        self.assertLess(result.lines_read, len(self.path.read_text(encoding="utf-8").splitlines()))

    def test_status_and_timestamp_update_is_atomic_and_not_fixed_width(self) -> None:
        self.tasks.add(self.task("Update me"), updated="2026-08-03T09:00:00Z")
        before = self.path.read_bytes()
        before_stat = os.stat(self.path)

        self.tasks.set_status(
            "TASK-001",
            "pending human decision",
            updated="2026-08-03T10:00:00Z",
        )

        after = self.path.read_bytes()
        after_stat = os.stat(self.path)
        self.assertNotEqual(before_stat.st_ino, after_stat.st_ino)
        self.assertGreater(len(after), len(before))
        self.assertIn(b"STATUS:       pending human decision\n", after)
        self.assertIn(b"UPDATED:      2026-08-03T10:00:00Z", after)
        self.assertEqual(self.tasks.get("TASK-001").status, "pending human decision")

    def test_failed_atomic_replace_keeps_original_file(self) -> None:
        self.tasks.add(self.task("Keep me"), updated="2026-08-03T09:00:00Z")
        before = self.path.read_bytes()

        with patch("cmo_runtime.task_file.os.replace", side_effect=OSError("simulated failure")):
            with self.assertRaisesRegex(OSError, "simulated failure"):
                self.tasks.set_status(
                    "TASK-001",
                    "pending human decision",
                    updated="2026-08-03T10:00:00Z",
                )

        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(list(self.path.parent.glob(f".{self.path.name}.*.tmp")), [])

    def test_second_task_cannot_enter_in_progress(self) -> None:
        self.tasks.add(self.task("First"), updated="2026-08-03T09:00:00Z")
        self.tasks.add(self.task("Second"), updated="2026-08-03T09:00:01Z")
        self.tasks.set_status("TASK-001", "in-progress", updated="2026-08-03T09:01:00Z")

        with self.assertRaisesRegex(
            ActiveTaskError,
            "TASK-001 is already in-progress; TASK-002 cannot enter in-progress",
        ):
            self.tasks.set_status(
                "TASK-002",
                "in-progress",
                updated="2026-08-03T09:02:00Z",
            )

        second = self.tasks.get("TASK-002")
        self.assertEqual(second.status, "queued")
        self.assertEqual(second.updated, "2026-08-03T09:00:01Z")


if __name__ == "__main__":
    unittest.main()
