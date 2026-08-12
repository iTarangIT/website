from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cmo_runtime.agent_runtime import BoardStore, decision_bullets
from cmo_runtime.cmo_agent import parser
from cmo_runtime.content_flow import (
    ArticlePackage,
    ContentRuntime,
    HermesContentWriter,
    _normalise_package_slot,
)
from cmo_runtime.review_worker import decide
from tests.test_content_flow import FakeWriter, RecordingSkillLoader, RecordingTaskFile, package


BOARD = """# CMO Task Board

## Backlog

### TASK-200 — Explain local EV battery page decisions
- Owner: content
- Priority: high
- Objective: Explain when a city-specific EV battery page is useful.
- Status: Backlog
- Research brief: artifacts/TASK-200-research.md
- Change status: queued

## In Progress

_No tasks._

## CMO Review

_No tasks._

## Human Approval

_No tasks._

## Completed

_No tasks._
"""


RESEARCH = """# Research brief — TASK-200

- Topic: Explain when a city-specific EV battery page is useful.
- Research completed: 2026-08-10
- Firecrawl pages fetched: 3/8
- Source-fetch success rate: 37.5%
- Firecrawl credits used for this article: 9 (measured API delta)
- Firecrawl credits remaining: 700 (measured API value)

## Retained source pages

### 1. Source one

- URL: https://example.org/source-one
- Published date: 2026-07-01
- Accessed date: 2026-08-10

Evidence one.

### 2. Source two

- URL: https://example.org/source-two
- Published date: 2026-07-02
- Accessed date: 2026-08-10

Evidence two.

### 3. Source three

- URL: https://example.org/source-three
- Published date: 2026-07-03
- Accessed date: 2026-08-10

Evidence three.

## Verification boundary

Only retained pages are evidence.
"""


class FailingResearcher:
    def __init__(self) -> None:
        self.called = False

    def research(self, task_id: str, topic: str):
        self.called = True
        raise AssertionError("Firecrawl must not be called when a retained research brief exists")


class ExistingResearchResumeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "artifacts").mkdir()
        (self.root / "state").mkdir()
        (self.root / "cmo_skills").mkdir()
        (self.root / "tasks.md").write_text(BOARD, encoding="utf-8")
        (self.root / "artifacts" / "TASK-200-research.md").write_text(RESEARCH, encoding="utf-8")
        (self.root / "WRITER_CONTRACT.md").write_text("Writer contract for tests.\n", encoding="utf-8")
        self.task_file = RecordingTaskFile(self.root / "tasks.md")
        self.loader = RecordingSkillLoader()
        self.researcher = FailingResearcher()

    def test_execute_reuses_retained_research_without_firecrawl(self) -> None:
        runtime = ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=self.researcher,
            writer=FakeWriter(package()),
        )

        result = runtime.execute()

        self.assertFalse(self.researcher.called)
        self.assertEqual(result.research.credits_used, 0)
        self.assertEqual(result.research.pages_fetched, 3)
        self.assertEqual(self.loader.loaded, ["content"])
        card = BoardStore(self.root).get("TASK-200")
        self.assertEqual(card.section, "CMO Review")
        self.assertEqual(card.fields["Attachment"], "artifacts/TASK-200-content.md")


class WriterLengthPromptTest(unittest.TestCase):
    def test_the_writing_prompt_gives_a_shape_not_a_word_target(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
            captured["command"] = command
            return SimpleNamespace(
                returncode=0,
                stderr="",
                stdout=(
                    "<<<BEGIN_ARTICLE>>>\narticle\n<<<END_ARTICLE>>>\n"
                    "<<<BEGIN_SLOT_ID>>>\nflow\n<<<END_SLOT_ID>>>\n"
                    "<<<BEGIN_SLOT_CAPTION>>>\nFlow\n<<<END_SLOT_CAPTION>>>\n"
                    "<<<BEGIN_SVG>>>\n<svg viewBox=\"0 0 10 10\"><title>T</title><desc>D</desc></svg>\n<<<END_SVG>>>\n"
                ),
            )

        with tempfile.TemporaryDirectory() as directory, patch(
            "cmo_runtime.content_flow.subprocess.run",
            side_effect=fake_run,
        ):
            HermesContentWriter(directory).write(
                task_id="TASK-200",
                topic="Topic",
                research_markdown="Research",
                skill_text="Skill",
                writer_contract="Contract",
            )

        prompt = str(captured["command"][-1])
        # This used to assert the writer was told "Aim for 1,050-1,250 words".
        # Thirteen attempts across three scopings were told exactly that and landed
        # 1,442-1,806, because a model cannot count words while producing them. The
        # instruction is now the article's shape, which it can follow while writing,
        # and the band is enforced afterwards in Python by measuring and trimming.
        self.assertNotIn("Aim for 1,050", prompt, "a word target is back in the writing prompt")
        self.assertIn("4–6 sections, each with a `##` heading and 2–4 paragraphs", prompt)
        self.assertIn("60–90 words", prompt, "no paragraph budget for the writer to hold to")

    def test_correction_prompt_preserves_the_review_heading_contract(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
            captured["command"] = command
            return SimpleNamespace(
                returncode=0,
                stderr="",
                stdout=(
                    "<<<BEGIN_ARTICLE>>>\narticle\n<<<END_ARTICLE>>>\n"
                    "<<<BEGIN_SLOT_ID>>>\nflow\n<<<END_SLOT_ID>>>\n"
                    "<<<BEGIN_SLOT_CAPTION>>>\nFlow\n<<<END_SLOT_CAPTION>>>\n"
                    "<<<BEGIN_SVG>>>\n<svg viewBox=\"0 0 10 10\"><title>T</title><desc>D</desc></svg>\n<<<END_SVG>>>\n"
                ),
            )

        with tempfile.TemporaryDirectory() as directory, patch(
            "cmo_runtime.content_flow.subprocess.run",
            side_effect=fake_run,
        ):
            HermesContentWriter(directory).correct(
                task_id="TASK-200",
                topic="Topic",
                research_markdown="Research",
                skill_text="Skill",
                writer_contract="Contract",
                rejected=package(),
                validation_error="writer article is missing the Decision bullets section",
                revision_context="Remove the unused YouTube source.",
            )

        prompt = str(captured["command"][-1])
        self.assertIn("`## Decision bullets:` with 3–5", prompt)
        self.assertIn("Remove the unused YouTube source.", prompt)


class ReviewHeadingCompatibilityTest(unittest.TestCase):
    def test_markdown_decision_heading_with_colon_is_reviewable(self) -> None:
        artifact = """# Article

## Decision bullets:

- Pilot a small set of useful city pages.
- Require verified local operating evidence.
- Measure each page in Search Console.
"""

        self.assertEqual(len(decision_bullets(artifact)), 3)


class ImageSlotNormalisationTest(unittest.TestCase):
    def test_article_marker_is_the_source_of_truth_for_redundant_slot_fields(self) -> None:
        original = package()
        mismatched = ArticlePackage(
            markdown=original.markdown,
            slot_id="different-slot",
            slot_caption="Different caption",
            svg=original.svg,
            usage=original.usage,
        )

        normalised = _normalise_package_slot(mismatched)

        self.assertEqual(normalised.slot_id, "heat-flow")
        self.assertEqual(
            normalised.slot_caption,
            "How heat, usage and battery controls affect usable range",
        )


class RevisionRequirementReviewTest(unittest.TestCase):
    def test_cold_review_sends_back_an_artifact_that_retains_a_source_marked_for_removal(self) -> None:
        artifact = package().markdown + "\nhttps://www.youtube.com/watch?v=unused\n"
        payload = {
            "card": {
                "task_id": "TASK-200",
                "fields": {
                    "Metric": "Search impressions over 28 complete days.",
                    "Revision round": "1",
                    "Approval thread 1 rejection": "ceo@example.com: Remove the unused YouTube source.",
                },
            },
            "artifact": artifact,
        }

        result = decide(payload)

        self.assertEqual(result["outcome"], "send-back")
        self.assertIn("YouTube source", str(result["reason"]))


class CorrectingWriter:
    def __init__(self) -> None:
        self.feedback = ""

    def write(self, **kwargs: str) -> ArticlePackage:
        original = package()
        return ArticlePackage(
            markdown=original.markdown.replace(
                "https://example.org/source-three",
                "https://outside.example/unsupported",
            ),
            slot_id=original.slot_id,
            slot_caption=original.slot_caption,
            svg=original.svg,
            usage={"total_tokens": 100},
        )

    def correct(
        self,
        *,
        rejected: ArticlePackage,
        validation_error: str,
        **kwargs: str,
    ) -> ArticlePackage:
        self.feedback = validation_error
        corrected = package()
        return ArticlePackage(
            markdown=corrected.markdown,
            slot_id=corrected.slot_id,
            slot_caption=corrected.slot_caption,
            svg=corrected.svg,
            usage={"total_tokens": 200},
        )


class WriterCorrectionTest(ExistingResearchResumeTest):
    def test_one_bounded_correction_can_repair_a_rejected_package(self) -> None:
        writer = CorrectingWriter()
        runtime = ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=self.researcher,
            writer=writer,
        )

        result = runtime.execute()

        self.assertIn("URLs absent from the research brief", writer.feedback)
        self.assertEqual(result.usage["total_tokens"], 300)
        self.assertEqual(BoardStore(self.root).get("TASK-200").section, "CMO Review")


REVISION_BOARD = """# CMO Task Board

## Backlog

_No tasks._

## In Progress

_No tasks._

## CMO Review

_No tasks._

## Human Approval

### TASK-200 — Explain local EV battery page decisions
- Owner: content
- Priority: high
- Objective: Explain when a city-specific EV battery page is useful.
- Status: Human Approval
- Research brief: artifacts/TASK-200-research.md
- Attachment: artifacts/TASK-200-content.md
- Image slot flow: artifacts/uploads/TASK-200-flow.png
- Revision round: 1
- Approval thread 1 rejection: ceo@example.com: Add a city-to-intent matrix; use https://example.org/brief as the structural reference.
- Change status: revision requested

## Completed

_No tasks._
"""


class FakeRevisionWriter:
    def __init__(self) -> None:
        self.context = ""

    def revise(self, **kwargs: object) -> ArticlePackage:
        self.context = str(kwargs["revision_context"])
        revised = package()
        return ArticlePackage(
            markdown=revised.markdown.replace(
                "Why electric-vehicle range changes in hot weather",
                "A useful revised title",
            ),
            slot_id=revised.slot_id,
            slot_caption=revised.slot_caption,
            svg=revised.svg,
            usage={"total_tokens": 250, "api_calls": 1},
        )


class RevisionCorrectionWriter(FakeRevisionWriter):
    def __init__(self) -> None:
        super().__init__()
        self.correct_context = ""

    def revise(self, **kwargs: object) -> ArticlePackage:
        self.context = str(kwargs["revision_context"])
        rejected = package()
        return ArticlePackage(
            markdown=rejected.markdown.replace("## Decision bullets:", "## Recommendations"),
            slot_id=rejected.slot_id,
            slot_caption=rejected.slot_caption,
            svg=rejected.svg,
            usage={"total_tokens": 100, "api_calls": 1},
        )

    def correct(self, *, revision_context: str, **kwargs: object) -> ArticlePackage:
        self.correct_context = revision_context
        corrected = package()
        return ArticlePackage(
            markdown=corrected.markdown,
            slot_id=corrected.slot_id,
            slot_caption=corrected.slot_caption,
            svg=corrected.svg,
            usage={"total_tokens": 200, "api_calls": 1},
        )


class HumanCommentRevisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "artifacts" / "uploads").mkdir(parents=True)
        (self.root / "state").mkdir()
        (self.root / "cmo_skills").mkdir()
        (self.root / "tasks.md").write_text(REVISION_BOARD, encoding="utf-8")
        (self.root / "artifacts" / "TASK-200-research.md").write_text(RESEARCH, encoding="utf-8")
        (self.root / "artifacts" / "TASK-200-content.md").write_text(package().markdown, encoding="utf-8")
        (self.root / "artifacts" / "uploads" / "TASK-200-flow.png").write_bytes(b"uploaded-image")
        (self.root / "WRITER_CONTRACT.md").write_text("Writer contract for tests.\n", encoding="utf-8")
        self.task_file = RecordingTaskFile(self.root / "tasks.md")
        self.loader = RecordingSkillLoader()
        self.researcher = FailingResearcher()
        self.writer = FakeRevisionWriter()

    def test_revision_archives_previous_version_and_uses_human_inputs(self) -> None:
        runtime = ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=self.researcher,
            writer=self.writer,
        )

        result = runtime.revise("TASK-200")

        self.assertFalse(self.researcher.called)
        self.assertEqual(self.loader.loaded, ["content"])
        self.assertIn("Add a city-to-intent matrix", self.writer.context)
        self.assertIn("https://example.org/brief", self.writer.context)
        self.assertIn("artifacts/uploads/TASK-200-flow.png", self.writer.context)
        self.assertEqual(result.archive_path.name, "TASK-200-content.r1.md")
        self.assertEqual(
            result.archive_path.read_text(encoding="utf-8"),
            package().markdown,
        )
        self.assertIn(
            "A useful revised title",
            (self.root / "artifacts" / "TASK-200-content.md").read_text(encoding="utf-8"),
        )
        card = BoardStore(self.root).get("TASK-200")
        self.assertEqual(card.section, "CMO Review")
        self.assertEqual(card.fields["Revision round"], "1")
        self.assertEqual(card.fields["Change status"], "pending CMO review")
        self.assertEqual(
            card.fields["Approval thread 1 rejection"],
            "ceo@example.com: Add a city-to-intent matrix; use https://example.org/brief as the structural reference.",
        )

    def test_revision_correction_retains_the_human_comment(self) -> None:
        writer = RevisionCorrectionWriter()
        runtime = ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=self.researcher,
            writer=writer,
        )

        result = runtime.revise("TASK-200")

        self.assertEqual(result.usage["total_tokens"], 300)
        self.assertIn("Add a city-to-intent matrix", writer.correct_context)

    def test_retry_keeps_the_original_round_archive(self) -> None:
        first_runtime = ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=self.loader,
            researcher=self.researcher,
            writer=self.writer,
        )
        first = first_runtime.revise("TASK-200")
        original_archive = first.archive_path.read_text(encoding="utf-8")
        self.task_file.move(
            "TASK-200",
            "Backlog",
            change_status="revision requested",
            tag="action to be taken by: content",
        )
        second_runtime = ContentRuntime(
            self.root,
            task_file=self.task_file,
            skill_loader=RecordingSkillLoader(),
            researcher=FailingResearcher(),
            writer=FakeRevisionWriter(),
        )

        second = second_runtime.revise("TASK-200")

        self.assertEqual(second.archive_path, first.archive_path)
        self.assertEqual(second.archive_path.read_text(encoding="utf-8"), original_archive)


class RevisionCommandTest(unittest.TestCase):
    def test_cli_accepts_an_optional_revision_task_id(self) -> None:
        arguments = parser().parse_args(["content-revise", "TASK-200"])

        self.assertEqual(arguments.command, "content-revise")
        self.assertEqual(arguments.task_id, "TASK-200")


if __name__ == "__main__":
    unittest.main()
