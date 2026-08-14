from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cmo_runtime.task_file import ActiveTaskError, TaskFile, validate_structure


SECTIONS = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")


def card(
    task_id: str,
    *,
    section_status: str,
    owner: str = "seo",
    skill: str = "seo",
    last_updated: str = "2026-08-04T10:00:00Z",
    updated: str = "2026-08-04T10:00:00Z",
) -> str:
    return "\n".join(
        (
            f"### {task_id} — Validator fixture",
            f"- ID: {task_id}",
            "- Title: Validator fixture",
            f"- Owner: {owner}",
            "- Priority: high",
            f"- Status: {section_status}",
            "- Start date: not started",
            "- Completed date: not completed",
            "- Objective: Prove validator behavior.",
            "- Acceptance criteria:",
            "  - The expected structural issue is reported.",
            "- Latest summary: Test fixture.",
            f"- Last updated: {last_updated}",
            f"- Skill: {skill}",
            "- Description: Prove validator behavior.",
            "- Attachment: none",
            "- Metric: One validator behavior verified.",
            "- Tag: action to be taken by: cmo",
            f"- Updated: {updated}",
        )
    )


def board(cards_by_section: dict[str, list[str]], *, sections: tuple[str, ...] = SECTIONS) -> str:
    chunks = ["# Test board"]
    for section in sections:
        chunks.append(f"## {section}")
        chunks.extend(cards_by_section.get(section, []))
    return "\n\n".join(chunks) + "\n"


class StructuralValidatorNegativeTests(unittest.TestCase):
    def validate(self, content: str) -> set[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.md"
            path.write_text(content, encoding="utf-8")
            return {issue.code for issue in validate_structure(path)}

    def test_duplicate_sections_fail_validation(self) -> None:
        content = board({}, sections=("Backlog", "In Progress", "Backlog", "CMO Review", "Human Approval", "Completed"))

        self.assertIn("duplicate-section", self.validate(content))

    def test_wrong_section_order_fails_validation(self) -> None:
        content = board({}, sections=("In Progress", "Backlog", "CMO Review", "Human Approval", "Completed"))

        self.assertIn("section-order", self.validate(content))

    def test_section_status_mismatch_fails_validation(self) -> None:
        content = board({"Backlog": [card("TASK-001", section_status="CMO Review")]})

        self.assertIn("section-status", self.validate(content))

    def test_mirror_mismatch_fails_validation(self) -> None:
        content = board(
            {
                "Backlog": [
                    card(
                        "TASK-001",
                        section_status="Backlog",
                        owner="seo",
                        skill="content",
                        last_updated="2026-08-04T10:00:00Z",
                        updated="2026-08-04T10:01:00Z",
                    )
                ]
            }
        )

        codes = self.validate(content)
        self.assertIn("owner-skill", codes)
        self.assertIn("updated-mirror", codes)

    def test_two_cards_in_progress_fail_validation(self) -> None:
        content = board(
            {
                "In Progress": [
                    card("TASK-001", section_status="In Progress"),
                    card("TASK-002", section_status="In Progress"),
                ]
            }
        )

        self.assertIn("multiple-in-progress", self.validate(content))


class BoardMoveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "tasks.md"

    def test_move_relocates_card_and_updates_mirrors_together(self) -> None:
        self.path.write_text(
            board({"Backlog": [card("TASK-001", section_status="Backlog")]}),
            encoding="utf-8",
        )
        tasks = TaskFile(self.path)

        tasks.move("TASK-001", "CMO Review", updated="2026-08-04T11:00:00Z")

        text = self.path.read_text(encoding="utf-8")
        self.assertGreater(text.index("### TASK-001"), text.index("## CMO Review"))
        self.assertLess(text.index("### TASK-001"), text.index("## Human Approval"))
        self.assertIn("- Status: CMO Review", text)
        self.assertIn("- Last updated: 2026-08-04T11:00:00Z", text)
        self.assertIn("- Updated: 2026-08-04T11:00:00Z", text)
        self.assertEqual(validate_structure(self.path), [])

    def test_move_refuses_second_card_in_progress_without_mutation(self) -> None:
        self.path.write_text(
            board(
                {
                    "Backlog": [card("TASK-002", section_status="Backlog")],
                    "In Progress": [card("TASK-001", section_status="In Progress")],
                }
            ),
            encoding="utf-8",
        )
        before = self.path.read_bytes()
        tasks = TaskFile(self.path)

        with self.assertRaisesRegex(
            ActiveTaskError,
            "TASK-001 is already in In Progress; TASK-002 cannot enter In Progress",
        ):
            tasks.move("TASK-002", "In Progress", updated="2026-08-04T11:00:00Z")

        self.assertEqual(self.path.read_bytes(), before)

    def test_set_change_status_updates_card_under_board_validation(self) -> None:
        self.path.write_text(
            board({"Backlog": [card("TASK-001", section_status="Backlog")]}),
            encoding="utf-8",
        )
        tasks = TaskFile(self.path)

        tasks.set_change_status(
            "TASK-001",
            "commissioning",
            updated="2026-08-04T11:30:00Z",
        )

        text = self.path.read_text(encoding="utf-8")
        self.assertIn("- Change status: commissioning", text)
        self.assertIn("- Last updated: 2026-08-04T11:30:00Z", text)
        self.assertIn("- Updated: 2026-08-04T11:30:00Z", text)
        self.assertEqual(validate_structure(self.path), [])


if __name__ == "__main__":
    unittest.main()
