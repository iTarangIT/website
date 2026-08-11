"""What reaches the Blogs tab, and what must not.

The tab's contents come from one filter in `console_board.read_board()`, and until
now nothing tested it — the console render suites feed a synthetic `blogs` list, so
they would stay green no matter what the filter admitted. That is how a 61-word
internal board-state summary came to sit on the Blogs tab: it is written by the
content skill, it lands in artifacts/ like an article, and every other condition
passed. ContentRuntime._select() already refuses that work type; this suite pins
the two to the same answer.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import console_board

BOARD_HEAD = """# iTarang CMO Task Board

## Backlog

## In Progress

## CMO Review

## Human Approval

"""

BOARD_TAIL = "## Completed\n"


def _card(task_id: str, title: str, *, skill: str = "content", work_type: str = "",
          attachment: str = "") -> str:
    lines = [
        f"### {task_id} — {title}",
        f"- ID: {task_id}",
        f"- Title: {title}",
        f"- Owner: {skill}",
        f"- Skill: {skill}",
        "- Priority: medium",
        "- Status: Human Approval",
        f"- Attachment: {attachment or 'none'}",
        "- Metric: Organic sessions",
        "- Tag: action to be taken by: human",
        "- Revision round: 0",
        "- Last updated: 2026-08-11T00:00:00Z",
        "- Updated: 2026-08-11T00:00:00Z",
    ]
    if work_type:
        lines.append(f"- Work type: {work_type}")
    return "\n".join(lines) + "\n"


ARTICLE = """---
title: Battery replacement, city by city
slug: battery-replacement
category: financing
---

# Battery replacement, city by city

A rider asking about replacement cost wants one number.

## Decision bullets:

- **Measure first.** Check Search Console before commissioning more pages.
"""


class BlogsTab(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "artifacts").mkdir()
        (self.root / "state").mkdir()

    def build(self, *cards: str) -> list[dict]:
        board = self.root / "tasks.md"
        board.write_text(BOARD_HEAD + "\n".join(cards) + "\n" + BOARD_TAIL, encoding="utf-8")
        return console_board.read_board(board, self.root)["blogs"]

    def article(self, task_id: str) -> str:
        name = f"{task_id}-content.md"
        (self.root / "artifacts" / name).write_text(ARTICLE, encoding="utf-8")
        return f"artifacts/{name}"

    def test_a_written_content_card_reaches_the_tab(self) -> None:
        blogs = self.build(_card("TASK-100", "A real article", attachment=self.article("TASK-100")))

        self.assertEqual([task["id"] for task in blogs], ["TASK-100"])

    def test_an_internal_board_summary_never_reaches_the_tab(self) -> None:
        # Content skill, real artifact, every other condition satisfied — and still
        # not a blog. This is the card that was actually on the tab.
        blogs = self.build(
            _card("TASK-069", "Produce a verified internal board-state summary",
                  work_type="internal-board-summary", attachment=self.article("TASK-069")),
            _card("TASK-100", "A real article", attachment=self.article("TASK-100")),
        )

        self.assertEqual([task["id"] for task in blogs], ["TASK-100"])

    def test_a_commissioning_card_never_reaches_the_tab(self) -> None:
        blogs = self.build(
            _card("TASK-066", "Commission task-file write",
                  work_type="commissioning", attachment=self.article("TASK-066")),
        )

        self.assertEqual(blogs, [])

    def test_an_unwritten_content_card_does_not_reach_the_tab(self) -> None:
        # No artifact: it is an approved topic queued for writing, not an article.
        blogs = self.build(_card("TASK-084", "E-Rickshaw Battery Repair or Replacement"))

        self.assertEqual(blogs, [])

    def test_a_card_from_another_skill_does_not_reach_the_tab(self) -> None:
        blogs = self.build(
            _card("TASK-082", "Install the GA4 measurement tag", skill="ops",
                  attachment=self.article("TASK-082")),
        )

        self.assertEqual(blogs, [])

    def test_the_tab_and_the_writer_refuse_the_same_work_types(self) -> None:
        # If _select() learns a new refusal, this fails until the tab agrees.
        import inspect

        from cmo_runtime.content_flow import ContentRuntime

        source = inspect.getsource(ContentRuntime._select)
        refused = set()
        for line in source.splitlines():
            if "work_type in" in line:
                refused = {part.strip().strip('"\'') for part in
                           line.split("{", 1)[1].split("}", 1)[0].split(",") if part.strip()}

        self.assertTrue(refused, "could not read the work types _select() refuses")
        self.assertEqual(refused, set(console_board.NON_ARTICLE_WORK_TYPES))


class ExcerptTruncation(unittest.TestCase):
    """A retained excerpt is cut without severing its Markdown.

    `test_ceo_reader.py` renders every artifact in the live profile and fails on
    raw Markdown. A flat character cut through `**bold**` put two literal asterisks
    into TASK-084's research brief and turned that suite red — from scraped source
    text, not from anything the writer produced.
    """

    def truncate(self, text: str, limit: int) -> str:
        from cmo_runtime.content_flow import _truncate_excerpt

        return _truncate_excerpt(text, limit)

    def test_short_text_is_returned_untouched(self) -> None:
        self.assertEqual(self.truncate("a short page", 3000), "a short page")

    def test_a_cut_through_bold_does_not_leave_a_dangling_marker(self) -> None:
        text = "x" * 40 + "\n" + "keep this line\n" + "**India E-Rickshaw Market Driver:**" + "y" * 200
        result = self.truncate(text, 60)

        self.assertEqual(result.count("**") % 2, 0, "an unpaired ** survived the cut")
        self.assertIn("[Excerpt truncated in retained brief.]", result)

    def test_the_cut_prefers_a_line_boundary(self) -> None:
        text = "first line\nsecond line\nthird line that runs past the limit\n"
        result = self.truncate(text, 30)

        self.assertTrue(result.startswith("first line\nsecond line"))
        self.assertNotIn("third line", result)

    def test_one_very_long_line_is_still_retained(self) -> None:
        # No newline to cut on: keep the budget rather than throw the page away.
        result = self.truncate("z" * 5000, 3000)

        self.assertGreater(len(result), 2900)

    def test_a_severed_bold_never_reaches_the_reader(self) -> None:
        # The production shape: prose with bold runs, cut mid-marker. This is what
        # put "**R" into TASK-084's brief and turned test_ceo_reader.py red.
        import ceo_reader

        text = (
            "India E-Rickshaw Market Driver\n"
            "Growth is driven by **low running cost** and rising demand.\n"
            "**Market Restraint:** charging access is uneven across states.\n"
        )
        for limit in range(40, len(text)):
            with self.subTest(limit=limit):
                rendered = ceo_reader.render_markdown_fragment(self.truncate(text, limit))
                self.assertNotIn("**", rendered, "bold survived as asterisks")


if __name__ == "__main__":
    unittest.main()
