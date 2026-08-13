"""What the Process tab is allowed to say, and what it must survive.

These are behaviour tests, not presence tests. Each one puts the system into a
state and asserts on what comes back out — a killed process, a stage nobody
recorded, an article citing a URL nothing ever fetched. The regression this
codebase keeps having is a test that checks a name exists while the thing the
name refers to quietly does the wrong thing, so none of these check for a name.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from cmo_runtime.console_db import ConsoleDB, ConsoleDBError  # noqa: E402
from cmo_runtime.pipeline_stages import NullRecorder, StageRecorder  # noqa: E402

PYTHON = os.getenv("CMO_TEST_PYTHON", sys.executable)

#: The board parser requires an em dash in the card heading; a hyphen silently
#: yields zero tasks and every assertion below would pass against nothing.
BOARD = """# iTarang CMO Board

## Backlog

## In Progress

## CMO Review

## Human Approval

### TASK-777 — Battery replacement, city by city
- ID: TASK-777
- Title: Battery replacement, city by city
- Owner: content
- Skill: content
- Priority: high
- Status: Human Approval
- Attachment: artifacts/TASK-777-content.md
- Metric: Organic sessions to the article
- Tag: action to be taken by: human
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

## Completed
"""

#: Cites a source deliberately absent from the fetch ledger. An article can name
#: any URL it likes; that is precisely the claim the Process tab must refuse.
ARTICLE = """---
title: Battery replacement, city by city
slug: battery-replacement
category: financing
source_urls: https://fabricated.invalid/never-fetched
---

# Battery replacement, city by city

A rider asking about replacement cost wants one number, not a survey. See
https://fabricated.invalid/never-fetched for the figures.

## Decision bullets:

- Measure first.
"""


def make_profile(tmp: str) -> Path:
    root = Path(tmp)
    (root / "state").mkdir()
    (root / "artifacts").mkdir()
    (root / "logs").mkdir()
    (root / "tasks.md").write_text(BOARD, encoding="utf-8")
    (root / "artifacts" / "TASK-777-content.md").write_text(ARTICLE, encoding="utf-8")
    return root


class StageRowsSurviveACrashMidRun(unittest.TestCase):
    """Invariant 1: a stage completed is a stage recorded."""

    def test_a_killed_process_leaves_finished_stages_and_the_interrupted_one_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            script = root / "run.py"
            script.write_text(
                textwrap.dedent(
                    f"""
                    import os, signal, sys
                    sys.path.insert(0, {str(HERE)!r})
                    from cmo_runtime.console_db import ConsoleDB
                    from cmo_runtime.pipeline_stages import StageRecorder

                    database = ConsoleDB({str(root)!r})
                    recorder = StageRecorder(database, task_id="TASK-777")
                    with recorder.stage("research") as stage:
                        stage.record_fetch(
                            kind="scrape", outcome="fetched",
                            url="https://example.test/one", title="One",
                        )
                        stage.finish(summary="1/1 pages")
                    # Open the next stage and die inside it. No finally, no flush,
                    # no chance to tidy up — this is SIGKILL, not an exception.
                    database.start_stage("writing", task_id="TASK-777")
                    os.kill(os.getpid(), signal.SIGKILL)
                    """
                ),
                encoding="utf-8",
            )
            completed = subprocess.run([PYTHON, str(script)], capture_output=True)

            self.assertEqual(
                completed.returncode,
                -signal.SIGKILL,
                f"the run did not die as intended: {completed.stderr.decode(errors='replace')}",
            )

            database = ConsoleDB(root)
            self.addCleanup(database.close)
            stages = {stage["stage"]: stage for stage in database.stages_for_task("TASK-777")}

            self.assertEqual(
                stages["research"]["status"],
                "completed",
                "a stage that finished before the crash was lost with the process",
            )
            self.assertEqual(len(stages["research"]["fetches"]), 1)
            self.assertEqual(
                stages["writing"]["status"],
                "running",
                "the interrupted stage does not say it was interrupted",
            )
            self.assertIsNone(stages["writing"]["ended_at"])
            self.assertTrue(
                stages["writing"]["started_at"],
                "a running stage with no start time cannot show elapsed time",
            )


class AFailedStageIsARowNotSilence(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = ConsoleDB(Path(self.temp.name))
        self.addCleanup(self.database.close)
        self.recorder = StageRecorder(self.database, task_id="TASK-777")

    def test_an_exception_closes_the_stage_failed_and_still_raises(self) -> None:
        with self.assertRaises(RuntimeError):
            with self.recorder.stage("writing"):
                raise RuntimeError("OUTLINE TOO BROAD: the cost comparison needs its own article")

        stage = self.database.stages_for_task("TASK-777")[0]
        self.assertEqual(stage["status"], "failed")
        self.assertIn("OUTLINE TOO BROAD", stage["summary"])

    def test_a_retry_adds_a_row_rather_than_overwriting_the_failure(self) -> None:
        for _ in range(3):
            with self.assertRaises(RuntimeError):
                with self.recorder.stage("writing"):
                    raise RuntimeError("writer article has 1806 words")
        with self.recorder.stage("writing") as stage:
            stage.finish(summary="1,180 words")

        rows = [item for item in self.database.stages_for_task("TASK-777") if item["stage"] == "writing"]

        self.assertEqual(
            [(row["attempt"], row["status"]) for row in rows],
            [(1, "failed"), (2, "failed"), (3, "failed"), (4, "completed")],
            "three failed generations were collapsed into a success",
        )

    def test_a_fetch_that_failed_is_recorded_as_failed(self) -> None:
        with self.recorder.stage("research") as stage:
            stage.record_sources(
                [
                    {"url": "https://example.test/one", "title": "One"},
                    {"url": "https://example.test/two", "outcome": "failed", "message": "HTTP 502"},
                ]
            )
            stage.finish(summary="1/2 pages")

        stage = self.database.stages_for_task("TASK-777")[0]

        self.assertEqual(
            [(item["url"], item["outcome"]) for item in stage["fetches"]],
            [
                ("https://example.test/one", "fetched"),
                ("https://example.test/two", "failed"),
            ],
        )

    def test_a_fetch_naming_neither_a_url_nor_a_query_is_refused(self) -> None:
        with self.recorder.stage("research") as stage:
            with self.assertRaises(ConsoleDBError):
                stage.record_fetch(kind="scrape", outcome="fetched")
            stage.finish(summary="nothing read")

    def test_the_null_recorder_writes_no_rows(self) -> None:
        with NullRecorder().stage("writing") as stage:
            stage.record_fetch(kind="scrape", outcome="fetched", url="https://example.test/one")
            stage.finish(summary="ignored")

        self.assertEqual(self.database.stages_for_task("TASK-777"), [])


class TheProcessTabShowsOnlyWhatRan(unittest.TestCase):
    """Invariants 2 and 3, against the read model the console actually serves."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = make_profile(self.temp.name)
        import console_board

        self.console_board = console_board

    def read(self) -> dict:
        board = self.console_board.read_board(self.root / "tasks.md", self.root)
        return {task["id"]: task for task in board["blogs"]}

    def seed(self) -> ConsoleDB:
        database = ConsoleDB(self.root)
        self.addCleanup(database.close)
        recorder = StageRecorder(database, task_id="TASK-777")
        with recorder.stage("topic") as stage:
            stage.finish(summary="Chose the replacement-cost angle", why="Search Console demand")
        with recorder.stage("research") as stage:
            stage.record_sources(
                [
                    {
                        "url": "https://really-fetched.test/one",
                        "title": "One",
                        "published_date": "2026-07-01",
                        "accessed_date": "2026-08-11",
                    }
                ]
            )
            stage.finish(summary="1/2 pages")
        with recorder.stage("writing") as stage:
            stage.finish(summary="1,180 words")
        return database

    def test_a_card_with_no_recorded_stages_serves_an_empty_process_list(self) -> None:
        served = self.read()["TASK-777"]

        self.assertEqual(
            served["process"],
            [],
            "a card whose stages were never recorded invented some anyway",
        )

    def test_only_the_stages_that_ran_are_served_in_reading_order(self) -> None:
        self.seed()

        stages = self.read()["TASK-777"]["process"]

        self.assertEqual(
            [(stage["ordinal"], stage["stage"]) for stage in stages],
            [(1, "topic"), (5, "research"), (6, "writing")],
            "the served stage list is not the recorded one",
        )
        self.assertNotIn(
            "keywords",
            [stage["stage"] for stage in stages],
            "a stage that never ran was filled in",
        )

    def test_the_source_list_comes_from_the_fetch_ledger_not_the_article(self) -> None:
        """Invariant 3.

        The article cites `fabricated.invalid`, which nothing ever fetched. The
        research stage is built from `stage_fetches`, so the citation must not be
        able to walk onto the page by being written down.
        """
        self.seed()
        served = self.read()["TASK-777"]
        research = [stage for stage in served["process"] if stage["stage"] == "research"][0]
        urls = [item["url"] for item in research["fetches"]]

        self.assertIn("https://fabricated.invalid/never-fetched", served["article"]["text"])
        self.assertEqual(urls, ["https://really-fetched.test/one"])
        self.assertNotIn(
            "https://fabricated.invalid/never-fetched",
            urls,
            "a URL the article merely cites was listed as a source that was fetched",
        )

    def test_a_stage_counts_its_retrievals_and_its_failures_separately(self) -> None:
        database = ConsoleDB(self.root)
        self.addCleanup(database.close)
        recorder = StageRecorder(database, task_id="TASK-777")
        with recorder.stage("research") as stage:
            stage.record_sources(
                [
                    {"url": "https://a.test/1"},
                    {"url": "https://a.test/2"},
                    {"url": "https://a.test/3", "outcome": "failed", "message": "HTTP 502"},
                ]
            )
            stage.finish(summary="2/3 pages")

        research = self.read()["TASK-777"]["process"][0]

        self.assertEqual((research["fetched"], research["failed"]), (2, 1))


class TopicStagesFindTheirCardWhenOneIsMinted(unittest.TestCase):
    def test_carding_a_proposal_claims_the_stages_recorded_against_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database = ConsoleDB(Path(tmp))
            self.addCleanup(database.close)
            subject = database.subject_for("battery data sheets", "ceo@itarang.com")
            from cmo_runtime.console_db import ProposalCandidate

            result = database.add_candidates(
                subject_id=int(subject["id"]),
                research_run_id=None,
                candidates=[
                    ProposalCandidate(
                        title="Reading cycle life claims",
                        keywords=("cycle life",),
                        outline="Explain cycle-life numbers.",
                        source_kind="firecrawl",
                        source_refs=("https://example.test/one",),
                    )
                ],
            )
            proposal_id = int(result["added"][0]["id"])
            recorder = StageRecorder(database, proposal_id=proposal_id)
            with recorder.replay("topic", started_at="2026-08-13T05:00:00Z", duration_ms=4200) as stage:
                stage.finish(summary="Chose the cycle-life angle")

            self.assertEqual(
                database.stages_for_task("TASK-001"),
                [],
                "a stage reached a card that had not been minted yet",
            )

            database.attach_task(proposal_id, "TASK-001")
            stages = database.stages_for_task("TASK-001")

            self.assertEqual([stage["stage"] for stage in stages], ["topic"])
            self.assertEqual(
                stages[0]["duration_ms"],
                4200,
                "the measured duration of the shared pass was not kept",
            )


if __name__ == "__main__":
    unittest.main()
