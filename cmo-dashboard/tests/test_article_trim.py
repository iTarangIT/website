"""The word cap, enforced by measuring and cutting rather than by asking nicely.

Thirteen writer attempts across three scopings were told a word target and landed
between 1,442 and 1,806 words. The correction pass was told the same target and
overshot the same way. Nothing about the instruction was unclear — a model cannot
count words while it is producing them, so a numeric band is unverifiable at the
point of writing and only enforceable afterwards.

So the arithmetic moved into Python. These tests are about that arithmetic and the
splice: which sections give up how many words, what happens when a shortened
section comes back wrong, and what is reported when three passes are not enough.
The writer is stubbed throughout — what it returns is the input to this machinery,
not the thing under test.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cmo_runtime.content_flow import (
    MAX_TRIM_PASSES,
    MIN_SECTION_WORDS,
    TRIM_TARGET,
    WORD_CEILING,
    ArticlePackage,
    ArticleSection,
    ArticleTooLong,
    ContentRunRefused,
    ContentRuntime,
    ResearchBundle,
    ResearchSource,
    accept_trim,
    count_words,
    plan_trim,
    split_front_matter_text,
    split_sections,
)

FRONT_MATTER = """---
title: A useful finance guide
meta_title: Useful Finance Guide
meta_description: A description.
slug: useful-finance-guide
category: financing
audience: EV owners
source_urls: https://example.org/source
---
"""


def words(count: int, seed: str = "word") -> str:
    return " ".join(f"{seed}{index}" for index in range(count))


def section(heading: str, count: int) -> str:
    return f"## {heading}\n\n{words(count, heading.replace(' ', ''))}\n\n"


def article(sections: list[tuple[str, int]], intro: int = 120) -> str:
    body = f"# A useful finance guide\n\n{words(intro, 'intro')}\n\n"
    body += "".join(section(heading, count) for heading, count in sections)
    body += "{{image:decision-flow|How a reader decides.}}\n\n"
    body += "## Decision bullets:\n\n- **One.** A bullet.\n- **Two.** A bullet.\n- **Three.** A bullet.\n"
    return FRONT_MATTER + body


def bundle() -> ResearchBundle:
    return ResearchBundle(
        sources=[ResearchSource("A source", "https://example.org/source", "2026-01-01", "2026-08-12", "text")],
        pages_requested=1,
        pages_fetched=1,
        credits_before=10,
        credits_after=9,
        credits_used=1,
        credits_remaining=9,
    )


class SplittingIsLossless(unittest.TestCase):
    """A splice that loses a blank line changes the rendered article."""

    def test_the_sections_rejoin_to_exactly_the_original_body(self) -> None:
        _head, body = split_front_matter_text(article([("First", 200), ("Second", 200)]))

        self.assertEqual("".join(part.text for part in split_sections(body)), body)

    def test_the_text_before_the_first_heading_is_the_introduction(self) -> None:
        _head, body = split_front_matter_text(article([("First", 200)]))

        first = split_sections(body)[0]
        self.assertEqual(first.heading, "")
        self.assertEqual(first.label, "the introduction")
        self.assertIn("# A useful finance guide", first.text)

    def test_front_matter_survives_a_round_trip(self) -> None:
        source = article([("First", 200)])
        head, body = split_front_matter_text(source)

        self.assertEqual(head + body, source.strip())


class TheArithmeticDecidesWhatGoes(unittest.TestCase):
    def sections(self, *sizes: tuple[str, int]) -> list[ArticleSection]:
        _head, body = split_front_matter_text(article(list(sizes)))
        return split_sections(body)

    def test_the_longest_section_is_cut_first(self) -> None:
        plan = plan_trim(self.sections(("Short", 150), ("Long", 400), ("Middle", 250)), 60)

        self.assertEqual(len(plan), 1)
        self.assertIn("Long", plan[0].section.heading)
        self.assertEqual(plan[0].cut, 60)

    def test_a_large_excess_spreads_over_several_sections(self) -> None:
        """One section asked to lose two thirds comes back as a summary of itself."""
        plan = plan_trim(self.sections(("A", 300), ("B", 300), ("C", 300)), 250)

        self.assertGreater(len(plan), 1)
        self.assertEqual(sum(item.cut for item in plan), 250)
        for item in plan:
            self.assertLessEqual(item.cut, item.section.words * 0.36)

    def test_no_section_is_cut_below_the_floor(self) -> None:
        plan = plan_trim(self.sections(("Tiny", MIN_SECTION_WORDS + 5), ("Big", 400)), 900)

        for item in plan:
            self.assertGreaterEqual(item.target, MIN_SECTION_WORDS)

    def test_the_decision_bullets_are_never_handed_to_the_trimmer(self) -> None:
        """They are validated for count; a shortening pass loses one."""
        plan = plan_trim(self.sections(("A", 300)), 900)

        for item in plan:
            self.assertNotIn("Decision bullets", item.section.heading)

    def test_nothing_is_planned_when_there_is_no_excess(self) -> None:
        self.assertEqual(plan_trim(self.sections(("A", 300)), 0), [])


class ABadTrimIsNotSpliced(unittest.TestCase):
    """Each of these would be invisible until the article was published."""

    def original(self) -> ArticleSection:
        return ArticleSection(1, "## What to check", "## What to check\n\n" + words(200) + "\n\n")

    def test_a_shortened_section_is_accepted(self) -> None:
        accepted = accept_trim(self.original(), "## What to check\n\n" + words(140))

        self.assertIsNotNone(accepted)
        self.assertTrue(accepted.startswith("## What to check"))
        self.assertTrue(accepted.endswith("\n\n"), "the next heading would be glued to this section")

    def test_a_section_that_came_back_longer_is_rejected(self) -> None:
        self.assertIsNone(accept_trim(self.original(), "## What to check\n\n" + words(260)))

    def test_a_section_that_lost_its_heading_gets_it_back(self) -> None:
        accepted = accept_trim(self.original(), words(140))

        self.assertTrue(accepted.startswith("## What to check"))

    def test_a_section_that_dropped_the_image_marker_is_rejected(self) -> None:
        held = ArticleSection(1, "## What to check",
                              "## What to check\n\n{{image:flow|A caption.}}\n\n" + words(200) + "\n\n")

        self.assertIsNone(accept_trim(held, "## What to check\n\n" + words(120)))

    def test_a_section_that_kept_the_image_marker_is_accepted(self) -> None:
        held = ArticleSection(1, "## What to check",
                              "## What to check\n\n{{image:flow|A caption.}}\n\n" + words(200) + "\n\n")

        self.assertIsNotNone(
            accept_trim(held, "## What to check\n\n{{image:flow|A caption.}}\n\n" + words(120))
        )

    def test_an_empty_section_is_rejected(self) -> None:
        self.assertIsNone(accept_trim(self.original(), "   \n\n"))


class StubWriter:
    """Returns each section at whatever length the test asks for."""

    def __init__(self, *, shortfall: int = 0, misbehave: bool = False) -> None:
        self.shortfall = shortfall
        self.misbehave = misbehave
        self.asked: list[tuple[str, int, int]] = []

    def trim_section(self, *, task_id: str, instruction) -> tuple[str, dict]:
        self.asked.append((instruction.section.label, instruction.section.words, instruction.target))
        if self.misbehave:
            return instruction.section.text, {"total_tokens": 10}
        # Come back at the target, plus whatever the test says it overshoots by.
        length = max(1, instruction.target + self.shortfall)
        heading = instruction.section.heading
        body = (heading + "\n\n" if heading else "") + words(length, "trimmed")
        return body, {"total_tokens": 10}


class TheTrimLoop(unittest.TestCase):
    def runtime(self, writer: StubWriter) -> ContentRuntime:
        root = Path(tempfile.mkdtemp())
        (root / "state").mkdir()
        (root / "artifacts").mkdir()
        (root / "tasks.md").write_text("# board\n\n## Backlog\n\n## In Progress\n\n## CMO Review\n\n"
                                       "## Human Approval\n\n## Completed\n", encoding="utf-8")
        return ContentRuntime(root, writer=writer, researcher=object())

    def package(self, markdown: str) -> ArticlePackage:
        return ArticlePackage(markdown, "decision-flow", "How a reader decides.", "<svg/>", {})

    def long_article(self) -> str:
        # 1,551 words: the exact length attempt ten produced.
        return article([("Repair or replace", 330), ("What a repair costs", 330),
                        ("What a replacement costs", 330), ("Warning signs", 300)], intro=240)

    def test_a_long_article_is_cut_into_the_band(self) -> None:
        source = self.long_article()
        _head, body = split_front_matter_text(source)
        before = count_words(body)
        self.assertGreater(before, WORD_CEILING)

        writer = StubWriter()
        trimmed, history = self.runtime(writer)._trim(
            self.package(source), task_id="TASK-084", too_long=ArticleTooLong(before)
        )

        _head, after_body = split_front_matter_text(trimmed.markdown)
        self.assertLessEqual(count_words(after_body), WORD_CEILING)
        self.assertEqual(len(history), 1, "one pass should have been enough")

    def test_each_section_is_asked_for_its_own_number_not_a_global_one(self) -> None:
        """The whole point: a local cut of a named section by a named amount."""
        source = self.long_article()
        _head, body = split_front_matter_text(source)
        writer = StubWriter()

        self.runtime(writer)._trim(
            self.package(source), task_id="TASK-084", too_long=ArticleTooLong(count_words(body))
        )

        self.assertTrue(writer.asked)
        for label, current, target in writer.asked:
            self.assertTrue(label)
            self.assertLess(target, current, f"{label} was not asked to get shorter")
            self.assertGreaterEqual(target, MIN_SECTION_WORDS)

    def test_the_history_records_what_each_pass_measured(self) -> None:
        source = self.long_article()
        _head, body = split_front_matter_text(source)
        start = count_words(body)

        _trimmed, history = self.runtime(StubWriter())._trim(
            self.package(source), task_id="TASK-084", too_long=ArticleTooLong(start)
        )

        self.assertEqual(history[0]["words_before"], start)
        self.assertLess(history[0]["words_after"], start)
        self.assertTrue(history[0]["sections"])
        self.assertEqual(history[0]["sections"][0]["result"], "spliced")

    def test_it_gives_up_after_three_passes_and_states_the_shortfall(self) -> None:
        source = self.long_article()
        _head, body = split_front_matter_text(source)
        # Every section comes back 120 words over what it was asked for, so the
        # article converges slowly and never lands.
        writer = StubWriter(shortfall=120)

        with self.assertRaises(ContentRunRefused) as raised:
            self.runtime(writer)._trim(
                self.package(source), task_id="TASK-084", too_long=ArticleTooLong(count_words(body))
            )

        message = str(raised.exception)
        self.assertIn("trim pass", message)
        self.assertIn("over the 1400 ceiling", message)
        self.assertRegex(message, r"is \d+ words, \d+ over")
        self.assertIn(str(count_words(body)), message, "the starting length is not reported")

    def test_a_writer_that_returns_the_section_unchanged_is_reported_not_spliced(self) -> None:
        source = self.long_article()
        _head, body = split_front_matter_text(source)
        writer = StubWriter(misbehave=True)

        with self.assertRaises(ContentRunRefused):
            self.runtime(writer)._trim(
                self.package(source), task_id="TASK-084", too_long=ArticleTooLong(count_words(body))
            )

        self.assertLessEqual(len(writer.asked), 6, "the call cap did not hold")

    def test_a_writer_with_no_trim_support_raises_the_original_length_error(self) -> None:
        class NoTrim:
            pass

        source = self.long_article()
        original = ArticleTooLong(1551)

        with self.assertRaises(ArticleTooLong) as raised:
            self.runtime(NoTrim())._trim(
                self.package(source), task_id="TASK-084", too_long=original
            )

        self.assertIs(raised.exception, original)


class TheValidatorSeparatesLongFromEverythingElse(unittest.TestCase):
    def test_too_long_raises_the_trimmable_error(self) -> None:
        from cmo_runtime.content_flow import _validate_package

        source = article([("A", 500), ("B", 500), ("C", 500)], intro=200)

        with self.assertRaises(ArticleTooLong):
            _validate_package(
                ArticlePackage(source, "decision-flow", "How a reader decides.", "<svg/>", {}),
                bundle(),
            )

    def test_too_short_is_not_trimmable_and_says_so_the_old_way(self) -> None:
        from cmo_runtime.content_flow import _validate_package

        source = article([("A", 80)], intro=40)

        with self.assertRaises(ContentRunRefused) as raised:
            _validate_package(
                ArticlePackage(source, "decision-flow", "How a reader decides.", "<svg/>", {}),
                bundle(),
            )

        self.assertNotIsInstance(raised.exception, ArticleTooLong)
        self.assertIn("WRITER_CONTRACT requires 900–1,400", str(raised.exception))

    def test_the_band_itself_is_unchanged(self) -> None:
        """Nobody widened it to make the failure go away."""
        self.assertEqual((WORD_CEILING, TRIM_TARGET, MAX_TRIM_PASSES), (1400, 1300, 3))


if __name__ == "__main__":
    unittest.main()
