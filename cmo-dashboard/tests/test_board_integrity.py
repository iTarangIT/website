"""The board cannot lose a card by accident.

An `re.sub` was run against tasks.md with `re.S`. With DOTALL, `.` matches
newlines, so `- Completed date: .*\\n` consumed everything from that field to the
end of the file. Four cards in Completed went with it, and every check in the
write path passed: the result was a perfectly well-formed board that happened to
be missing a quarter of its history.

Two guards, because they catch it at two different moments. The write-time one
compares what is about to be committed against what is there and refuses any
write that makes a card stop existing — that would have refused the substitution
outright. The floor catches a board that is already short, whatever put it that
way, including a hand-edit no writer ever saw.

The third test enforces the rule rather than the symptom: no module that writes
the board may use `re.S` against it.
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from cmo_runtime.agent_runtime import BoardStore
from cmo_runtime.task_file import (
    TaskFile,
    TaskFileError,
    card_count_floor,
    validate_structure,
)

CARDS = ["TASK-100", "TASK-101", "TASK-102"]


def board() -> str:
    def card(task_id: str, section: str) -> str:
        return "\n".join([
            f"### {task_id} — A card",
            f"- ID: {task_id}",
            f"- Title: A card",
            "- Owner: content",
            "- Skill: content",
            "- Priority: medium",
            f"- Status: {section}",
            "- Attachment: none",
            "- Completed date: 2026-08-12T09:00:00Z",
            "- Latest summary: something",
            "- Last updated: 2026-08-12T09:00:00Z",
            "- Updated: 2026-08-12T09:00:00Z",
        ]) + "\n"

    return (
        "# Board\n\n## Backlog\n\n"
        + card("TASK-100", "Backlog") + "\n"
        + "## In Progress\n\n## CMO Review\n\n## Human Approval\n\n"
        + card("TASK-101", "Human Approval") + "\n"
        + "## Completed\n\n"
        + card("TASK-102", "Completed") + "\n"
    )


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        self.path = self.root / "tasks.md"
        self.path.write_text(board(), encoding="utf-8")
        self.task_file = TaskFile(self.path, lock_path=self.root / "state" / "tasks.lock")


class NoWriteMayLoseACard(Fixture):
    def test_the_incident_itself_is_refused(self) -> None:
        """The exact substitution that did the damage, run through the write path."""
        original = self.path.read_text(encoding="utf-8")
        truncated = re.sub(r"- Completed date: .*\n", "- Completed date: not completed\n",
                           original, count=1, flags=re.S)
        self.assertNotIn("TASK-102", truncated, "the fixture does not reproduce the damage")

        with self.assertRaises(TaskFileError) as raised:
            self.task_file._refuse_lost_cards(original, truncated, "test")

        self.assertIn("would remove", str(raised.exception))
        self.assertIn("TASK-102", str(raised.exception))

    def test_a_field_update_that_would_drop_a_card_is_refused(self) -> None:
        broken = TaskFile(self.path, lock_path=self.root / "state" / "tasks.lock")
        original = self.path.read_text(encoding="utf-8")

        with self.assertRaises(TaskFileError):
            broken._commit(original, original.split("## Completed")[0], "field update")

        self.assertEqual(self.path.read_text(encoding="utf-8"), original, "the board was written")

    def test_an_ordinary_field_update_still_works(self) -> None:
        self.task_file.set_board_fields("TASK-100", {"Latest summary": "changed"})

        text = self.path.read_text(encoding="utf-8")
        self.assertIn("- Latest summary: changed", text)
        self.assertEqual(sorted(TaskFile.card_ids(text)), CARDS)

    def test_a_move_still_works_and_keeps_every_card(self) -> None:
        self.task_file.move("TASK-100", "CMO Review", change_status="pending CMO review")

        self.assertEqual(sorted(TaskFile.card_ids(self.path.read_text(encoding="utf-8"))), CARDS)

    def test_adding_a_card_is_not_mistaken_for_losing_one(self) -> None:
        self.task_file.add_board_cards([
            "### TASK-103 — A new card\n- ID: TASK-103\n- Title: A new card\n- Owner: content\n"
            "- Skill: content\n- Priority: medium\n- Status: Backlog\n- Attachment: none\n"
            "- Last updated: 2026-08-12T09:00:00Z\n- Updated: 2026-08-12T09:00:00Z"
        ])

        self.assertIn("TASK-103", TaskFile.card_ids(self.path.read_text(encoding="utf-8")))

    def test_a_board_mutation_through_boardstore_is_guarded_too(self) -> None:
        store = BoardStore(self.root)
        original = self.path.read_text(encoding="utf-8")

        store.mutate("TASK-100", updates={"Latest summary": "still here"})

        self.assertEqual(sorted(TaskFile.card_ids(self.path.read_text(encoding="utf-8"))), CARDS)
        self.assertNotEqual(self.path.read_text(encoding="utf-8"), original)


class TheFloorCatchesABoardThatIsAlreadyShort(Fixture):
    def test_no_floor_recorded_is_not_an_error(self) -> None:
        self.assertEqual(card_count_floor(self.path), 0)
        self.assertEqual(validate_structure(self.path), [])

    def test_a_board_below_its_floor_fails_validation(self) -> None:
        (self.root / "tasks.card-floor").write_text("5\n", encoding="ascii")

        issues = validate_structure(self.path)

        self.assertEqual([issue.code for issue in issues], ["card-count"])
        self.assertIn("holds 3 cards", issues[0].message)
        self.assertIn("at least 5", issues[0].message)

    def test_a_board_at_or_above_its_floor_passes(self) -> None:
        (self.root / "tasks.card-floor").write_text("3\n", encoding="ascii")

        self.assertEqual(validate_structure(self.path), [])

    def test_a_malformed_floor_is_an_error_not_a_silent_zero(self) -> None:
        (self.root / "tasks.card-floor").write_text("lots\n", encoding="ascii")

        with self.assertRaises(TaskFileError):
            card_count_floor(self.path)


class TheRuleItself(unittest.TestCase):
    """No module that writes the board may use `re.S` against it.

    A rule written only in a README is a rule the next incident ignores. `re.S`
    turns every `.` into a newline-matching wildcard, and a board is a file whose
    record boundaries are newlines — so the two are incompatible by construction,
    not by carelessness.
    """

    #: Everything that reads or writes tasks.md's structure. `content_flow` and
    #: `blog_publisher` are deliberately absent: they parse article Markdown, where
    #: DOTALL is the correct tool and a front-matter block really does span lines.
    BOARD_MODULES = (
        "cmo_runtime/task_file.py",
        "cmo_runtime/agent_runtime.py",
        "cmo_runtime/decisions.py",
        "cmo_runtime/content_worker.py",
        "cmo_runtime/topic_proposals.py",
        "console_board.py",
        "ceo_actions.py",
        "ceo_blog_publish.py",
    )

    #: A DOTALL flag passed to a real regex call, or inlined into a pattern. Matching
    #: the words alone would flag every comment explaining why not to use them —
    #: including the ones in this file.
    DOTALL_CALL = re.compile(
        r"re\.(?:compile|match|fullmatch|search|sub|subn|split|findall|finditer)\("
        r".*\bre\.(?:S|DOTALL)\b"
    )
    DOTALL_INLINE = re.compile(r"""r?["'][^"']*\(\?[aiLmsux]*s[aiLmsux]*\)""")

    #: The escape hatch, and it has to be one line and say what it is reading. A
    #: rule with no exemption gets deleted the first time it is inconvenient; one
    #: with a visible exemption gets argued with, which is the point.
    EXEMPT = "not the board:"

    def source(self, relative: str) -> str:
        return (Path(__file__).resolve().parents[1] / relative).read_text(encoding="utf-8")

    def test_no_board_module_uses_dotall(self) -> None:
        offenders = []
        for relative in self.BOARD_MODULES:
            for number, line in enumerate(self.source(relative).splitlines(), start=1):
                # A line that is only a comment cannot run a regex, and half the
                # comments in these modules exist to explain this very rule.
                if line.strip().startswith("#") or self.EXEMPT in line:
                    continue
                if self.DOTALL_CALL.search(line) or self.DOTALL_INLINE.search(line):
                    offenders.append(f"{relative}:{number}: {line.strip()}")

        self.assertEqual(offenders, [], "DOTALL against a line-structured board file")

    def test_the_exemption_has_to_say_what_it_is_reading(self) -> None:
        """Every exemption in the tree names a source that is not tasks.md."""
        for relative in self.BOARD_MODULES:
            for number, line in enumerate(self.source(relative).splitlines(), start=1):
                if self.EXEMPT not in line:
                    continue
                reason = line.split(self.EXEMPT, 1)[1].strip()
                self.assertTrue(reason, f"{relative}:{number} exempts itself without saying why")

    def test_the_check_would_catch_the_substitution_that_caused_this(self) -> None:
        """A guard nobody has seen fail is a guard nobody should trust."""
        damage = 're.sub(r"(?m)^(### TASK-084 .*?)^- Completed date: .*\\n", fix, text, flags=re.S)'

        self.assertTrue(self.DOTALL_CALL.search(damage), "the scanner misses the real thing")
        self.assertTrue(self.DOTALL_INLINE.search('re.search(r"(?s)^### ", text)'))
        self.assertFalse(self.DOTALL_CALL.search('# never use re.S on the board'))

    def test_the_card_reader_is_shared_rather_than_re_derived(self) -> None:
        """One way to ask which cards exist, so no caller invents a looser one."""
        text = "## Backlog\n\n### TASK-1 — One\n\n### TASK-22\n\nnot a card\n### TASK-3 — Three\n"

        self.assertEqual(TaskFile.card_ids(text), ["TASK-1", "TASK-22", "TASK-3"])


if __name__ == "__main__":
    unittest.main()
