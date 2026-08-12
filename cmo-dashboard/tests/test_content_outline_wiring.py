"""The approved scope has to reach the writer, and a scope that does not fit has to
reach the board.

Every card minted from an approved topic proposal carries `Topic outline` and
`Topic keywords`, and carries the acceptance criterion "Cover the approved outline
recorded on this card". Until now `ContentRuntime` passed neither field to the
writer: the criterion could not be satisfied by construction, and what the CEO
approved could diverge from what was written with nothing anywhere to show it.

The second half is the failure that made this visible. Nine consecutive TASK-084
generations overran the 900–1,400-word ceiling and were rejected after the fact,
and the board only ever learned "writer article has N words". The outline that did
not fit was never the thing named. `OUTLINE TOO BROAD:` is that outcome made
distinct, and `correct()` is deliberately not offered a chance to fix it — a scope
too wide for the ceiling is not a defect a correction pass can repair, and the
retry costs a full generation to produce the same answer.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cmo_runtime.content_flow import (
    ArticlePackage,
    ContentRunRefused,
    ContentRuntime,
    HermesContentWriter,
    ResearchBundle,
    ResearchSource,
    _approved_topic_block,
    _outline_refusal,
)
from cmo_runtime.task_file import TaskFile

OUTLINE = (
    "A practical decision guide for e-rickshaw drivers who are unsure whether to "
    "repair a weak battery or replace it, using a simple rule-of-thumb comparison."
)
KEYWORDS = "e rickshaw battery replacement cost, three wheeler battery repair or replace"


def board(*, outline: str = OUTLINE, keywords: str = KEYWORDS) -> str:
    scope = ""
    if outline:
        scope += f"- Topic outline: {outline}\n"
    if keywords:
        scope += f"- Topic keywords: {keywords}\n"
    return f"""# CMO Task Board

## Backlog

### TASK-100 — Repair or replace an e-rickshaw battery
- Owner: content
- Priority: high
- Objective: Write the approved article.
- Status: Backlog
{scope}
## In Progress

_No tasks._

## CMO Review

_No tasks._

## Human Approval

_No tasks._

## Completed

_No tasks._
"""


ARTICLE = """---
title: Repair or replace an e-rickshaw battery
meta_title: Repair or replace, judged on cost
meta_description: A plain-language guide to judging repair against replacement.
slug: repair-or-replace
category: financing
audience: E-rickshaw drivers
source_urls: https://example.org/source-one
---

# Repair or replace an e-rickshaw battery

{body}

{{{{image:cost-flow|How repair cost compares with replacement cost}}}}

## Decision bullets:

- Compare the quoted repair against the remaining life it buys.
- A pack failing one cell at a time is rarely worth a second repair.
- Replacement is the safer choice once faults repeat within a season.
"""

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 420" role="img">'
    "<title>Cost flow</title><desc>A comparison flow.</desc>"
    '<rect width="900" height="420" fill="#fff"/><text x="50" y="80">Repair</text></svg>'
)


def article_markdown() -> str:
    sentence = (
        "A driver deciding between a repair and a replacement wants one comparable "
        "number, and the honest answer depends on what remaining life the repair buys. "
    )
    return ARTICLE.replace("{body}", (sentence * 6 + "\n\n") * 7)


def package(markdown: str | None = None) -> ArticlePackage:
    return ArticlePackage(
        markdown=article_markdown() if markdown is None else markdown,
        slot_id="cost-flow",
        slot_caption="How repair cost compares with replacement cost",
        svg=SVG,
        usage={"total_tokens": 1234},
    )


def bundle() -> ResearchBundle:
    return ResearchBundle(
        sources=(
            ResearchSource(
                "Source one", "https://example.org/source-one", "2026-07-01", "2026-08-10", "Evidence."
            ),
        ),
        pages_requested=1,
        pages_fetched=1,
        credits_before=100,
        credits_after=101,
        credits_used=1,
        credits_remaining=899,
    )


class FakeResearcher:
    def research(self, task_id: str, topic: str) -> ResearchBundle:
        return bundle()


class RecordingWriter:
    """Records every keyword argument, so a dropped one fails rather than defaults."""

    def __init__(self, package: ArticlePackage, corrected: ArticlePackage | None = None) -> None:
        self.package = package
        self.corrected = corrected
        self.calls: list[dict[str, object]] = []
        self.corrections: list[dict[str, object]] = []

    def write(self, **kwargs: object) -> ArticlePackage:
        self.calls.append(dict(kwargs))
        return self.package

    def correct(self, **kwargs: object) -> ArticlePackage:
        self.corrections.append(dict(kwargs))
        if self.corrected is None:
            raise AssertionError("correct() was called when the run should not have retried")
        return self.corrected


class StubSkillLoader:
    def load(self, name: str) -> str:
        return "SKILL: content\n"


class ScopeReachesTheWriter(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("artifacts", "logs", "state", "cmo_skills"):
            (self.root / name).mkdir()
        (self.root / "WRITER_CONTRACT.md").write_text("Contract.\n", encoding="utf-8")

    def runtime(self, writer: RecordingWriter, *, text: str | None = None) -> ContentRuntime:
        (self.root / "tasks.md").write_text(board() if text is None else text, encoding="utf-8")
        return ContentRuntime(
            self.root,
            task_file=TaskFile(self.root / "tasks.md"),
            skill_loader=StubSkillLoader(),
            researcher=FakeResearcher(),
            writer=writer,
        )

    def test_execute_passes_the_approved_outline_and_keywords_to_the_writer(self) -> None:
        writer = RecordingWriter(package())
        self.runtime(writer).execute()

        self.assertEqual(len(writer.calls), 1)
        # Byte-for-byte: a reworded outline must not be able to reach the writer as
        # anything but what is recorded on the card.
        self.assertEqual(writer.calls[0]["topic_outline"], OUTLINE)
        self.assertEqual(writer.calls[0]["topic_keywords"], KEYWORDS)

    def test_a_card_with_no_recorded_scope_reaches_the_writer_with_empty_fields(self) -> None:
        # Cards held from before the topic flow have neither field.
        writer = RecordingWriter(package())
        self.runtime(writer, text=board(outline="", keywords="")).execute()

        self.assertEqual(writer.calls[0]["topic_outline"], "")
        self.assertEqual(writer.calls[0]["topic_keywords"], "")

    def test_a_correction_is_given_the_same_approved_scope(self) -> None:
        # The drift risk: a retry fixing a word count while blind to the approved
        # scope can walk straight out of what the CEO agreed to.
        rejected = package(markdown=article_markdown().replace("## Decision bullets:", "## Bullets"))
        writer = RecordingWriter(rejected, corrected=package())
        self.runtime(writer).execute()

        self.assertEqual(len(writer.corrections), 1)
        self.assertEqual(writer.corrections[0]["topic_outline"], OUTLINE)
        self.assertEqual(writer.corrections[0]["topic_keywords"], KEYWORDS)


class ScopeReachesThePrompt(unittest.TestCase):
    """The served prompt, not the parameter list — the argument has to be used."""

    def capture(self, method: str, **kwargs: object) -> str:
        captured: dict[str, object] = {}

        def fake_run(command: list[str], **_: object) -> SimpleNamespace:
            captured["command"] = command
            return SimpleNamespace(
                returncode=0,
                stderr="",
                stdout=(
                    "<<<BEGIN_ARTICLE>>>\narticle\n<<<END_ARTICLE>>>\n"
                    "<<<BEGIN_SLOT_ID>>>\nflow\n<<<END_SLOT_ID>>>\n"
                    "<<<BEGIN_SLOT_CAPTION>>>\nFlow\n<<<END_SLOT_CAPTION>>>\n"
                    '<<<BEGIN_SVG>>>\n<svg viewBox="0 0 10 10"><title>T</title><desc>D</desc></svg>\n'
                    "<<<END_SVG>>>\n"
                ),
            )

        base: dict[str, object] = {
            "task_id": "TASK-200",
            "topic": "Topic",
            "research_markdown": "Research",
            "skill_text": "Skill",
            "writer_contract": "Contract",
        }
        base.update(kwargs)
        with tempfile.TemporaryDirectory() as directory, patch(
            "cmo_runtime.content_flow.subprocess.run", side_effect=fake_run
        ):
            getattr(HermesContentWriter(directory), method)(**base)
        return str(captured["command"][-1])

    def test_the_write_prompt_carries_the_outline_and_keywords(self) -> None:
        prompt = self.capture("write", topic_outline=OUTLINE, topic_keywords=KEYWORDS)

        self.assertIn(OUTLINE, prompt)
        self.assertIn(KEYWORDS, prompt)

    def test_the_write_prompt_places_the_scope_above_the_research_brief(self) -> None:
        # The brief is evidence for the scope, not a source of extra scope. Order
        # is how that reads to a model.
        prompt = self.capture("write", topic_outline=OUTLINE, topic_keywords=KEYWORDS)

        self.assertLess(prompt.index("APPROVED TOPIC SCOPE"), prompt.index("RESEARCH BRIEF:"))

    def test_the_write_prompt_asks_the_writer_to_report_a_scope_that_will_not_fit(self) -> None:
        prompt = self.capture("write", topic_outline=OUTLINE, topic_keywords=KEYWORDS)

        self.assertIn("OUTLINE TOO BROAD:", prompt)
        self.assertIn("do not overrun the ceiling", prompt)

    def test_the_correction_prompt_carries_the_outline(self) -> None:
        prompt = self.capture(
            "correct",
            rejected=package(),
            validation_error="writer article has 1626 words; WRITER_CONTRACT requires 900–1,400",
            topic_outline=OUTLINE,
            topic_keywords=KEYWORDS,
        )

        self.assertIn(OUTLINE, prompt)
        self.assertIn(KEYWORDS, prompt)

    def test_the_revision_prompt_carries_the_outline(self) -> None:
        prompt = self.capture(
            "revise",
            existing_article="Existing",
            existing_svg=SVG,
            revision_context="Tighten the opening.",
            topic_outline=OUTLINE,
            topic_keywords=KEYWORDS,
        )

        self.assertIn(OUTLINE, prompt)
        self.assertIn(KEYWORDS, prompt)

    def test_a_card_with_no_scope_produces_no_scope_block_at_all(self) -> None:
        # Not an empty `OUTLINE:` line: to a model that reads as "no constraints"
        # rather than "not recorded".
        prompt = self.capture("write", topic_outline="", topic_keywords="")

        self.assertNotIn("APPROVED TOPIC SCOPE", prompt)
        self.assertNotIn("OUTLINE:", prompt)

    def test_the_block_is_empty_only_when_both_fields_are_empty(self) -> None:
        self.assertEqual(_approved_topic_block("", ""), "")
        self.assertEqual(_approved_topic_block("   ", "\n"), "")
        self.assertIn("OUTLINE: x", _approved_topic_block("x", ""))
        self.assertIn("KEYWORDS: y", _approved_topic_block("", "y"))


class AnOutlineThatDoesNotFit(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("artifacts", "logs", "state", "cmo_skills"):
            (self.root / name).mkdir()
        (self.root / "WRITER_CONTRACT.md").write_text("Contract.\n", encoding="utf-8")
        (self.root / "tasks.md").write_text(board(), encoding="utf-8")

    def runtime(self, writer: RecordingWriter) -> ContentRuntime:
        return ContentRuntime(
            self.root,
            task_file=TaskFile(self.root / "tasks.md"),
            skill_loader=StubSkillLoader(),
            researcher=FakeResearcher(),
            writer=writer,
        )

    def refusal(self) -> ArticlePackage:
        return package(
            markdown=(
                "OUTLINE TOO BROAD: duty cycle, downtime and recurring faults need a "
                "separate article.\n"
            )
        )

    def test_the_run_refuses_and_names_what_did_not_fit(self) -> None:
        writer = RecordingWriter(self.refusal())

        with self.assertRaises(ContentRunRefused) as caught:
            self.runtime(writer).execute()

        message = str(caught.exception)
        self.assertIn("does not fit one 900–1,400-word article", message)
        self.assertIn("duty cycle, downtime and recurring faults", message)

    def test_the_refusal_is_never_sent_to_the_correction_pass(self) -> None:
        # RecordingWriter.correct() raises AssertionError when no correction was
        # configured, so a retry here fails loudly rather than costing a generation.
        writer = RecordingWriter(self.refusal())

        with self.assertRaises(ContentRunRefused):
            self.runtime(writer).execute()

        self.assertEqual(writer.corrections, [])

    def test_the_reason_reaches_the_board_and_the_card_leaves_in_progress(self) -> None:
        # Nine generations died with nothing on the card naming the conflict.
        writer = RecordingWriter(self.refusal())
        with self.assertRaises(ContentRunRefused):
            self.runtime(writer).execute()

        text = (self.root / "tasks.md").read_text(encoding="utf-8")
        backlog = text.split("## Backlog", 1)[1].split("## In Progress", 1)[0]
        self.assertIn("TASK-100", backlog)
        self.assertIn("does not fit one 900–1,400-word article", text)

    def test_no_article_artifact_is_written_when_the_scope_is_refused(self) -> None:
        writer = RecordingWriter(self.refusal())
        with self.assertRaises(ContentRunRefused):
            self.runtime(writer).execute()

        self.assertEqual(sorted(p.name for p in (self.root / "artifacts").iterdir()),
                         ["TASK-100-research.md"])

    def test_a_real_article_is_not_mistaken_for_a_refusal(self) -> None:
        self.assertEqual(_outline_refusal(article_markdown()), "")
        self.assertEqual(_outline_refusal(""), "")

    def test_the_marker_is_read_only_from_the_first_line(self) -> None:
        # An article that happens to quote the marker further down is an article.
        body = article_markdown().replace(
            "## Decision bullets:",
            "The writer may report OUTLINE TOO BROAD: when a scope will not fit.\n\n## Decision bullets:",
        )

        self.assertEqual(_outline_refusal(body), "")


if __name__ == "__main__":
    unittest.main()
