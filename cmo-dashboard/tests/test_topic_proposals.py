"""Invariants 1, 2 and 3 for the topic proposal flow."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmo_runtime.agent_runtime import Runtime  # noqa: E402
from cmo_runtime.console_db import ConsoleDB, ConsoleDBError, ProposalCandidate, norm_key  # noqa: E402
from cmo_runtime.content_flow import ContentRunRefused, ContentRuntime  # noqa: E402
from cmo_runtime.task_file import TaskFileError  # noqa: E402
from cmo_runtime.topic_proposals import (  # noqa: E402
    ProposalRefused,
    ResearchPass,
    SourcePage,
    TopicProposalService,
    hold_legacy_cards,
)

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


class FakeSearchConsole:
    def __init__(self, rows=None, message="") -> None:
        self.rows = rows or []
        self.message = message

    def demand(self, subject: str):
        return list(self.rows), self.message


class FakeResearcher:
    """Stands in for Firecrawl. Counts pages so budget behaviour stays testable."""

    def __init__(self, *, used=100, remaining=900, pages=2) -> None:
        self.used = used
        self.remaining = remaining
        self.page_count = pages
        self.discovered: list[int] = []
        self.connected = True

    def credit_state(self):
        return self.used, self.remaining

    def discover(self, subject: str, limit: int):
        self.discovered.append(limit)
        return [f"https://example.test/{index}" for index in range(limit)]

    def retrieve(self, urls):
        pages = [
            SourcePage(title=f"Page {index}", url=url, markdown="evidence body")
            for index, url in enumerate(urls[: self.page_count])
        ]
        self.used += len(pages)
        self.remaining -= len(pages)
        return pages


class FakeProposer:
    def __init__(self, rows=None) -> None:
        self.rows = rows if rows is not None else [
            {"title": "What a three wheeler battery data sheet actually tells a driver",
             "keywords": ["three wheeler battery data"], "outline": "Explain the spec sheet."},
            {"title": "Reading cycle life claims on an e-rickshaw battery",
             "keywords": ["cycle life"], "outline": "Explain cycle-life numbers."},
        ]
        self.calls: list[dict] = []

    def propose(self, **kwargs):
        self.calls.append(kwargs)
        return list(self.rows)


class ProposalFlowTestCase(unittest.TestCase):
    def make_service(self, *, proposer=None, researcher=None, search_console=None):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()
        (root / "tasks.md").write_text(EMPTY_BOARD, encoding="utf-8")
        service = TopicProposalService(
            root,
            researcher=researcher or FakeResearcher(),
            search_console=search_console or FakeSearchConsole(),
            proposer=proposer or FakeProposer(),
        )
        self.addCleanup(service.database.close)
        return service, root


class UnapprovedProposalsNeverReachTheBoard(ProposalFlowTestCase):
    """Invariant 1."""

    def test_proposing_writes_no_board_card(self) -> None:
        service, root = self.make_service()
        run = service.propose("three wheeler battery data", "sanchit@example.test")

        self.assertEqual(len(run.added), 2)
        board = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertNotIn("three wheeler battery data sheet", board)
        self.assertNotIn("### TASK-", board)

    def test_neither_selector_can_pick_an_unapproved_proposal(self) -> None:
        service, root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposals = service.database.proposals()
        service.database.mark_revising(proposals[0]["id"], "narrow it", "sanchit@example.test")

        content = ContentRuntime(root, researcher=object(), writer=object())
        with self.assertRaises(ContentRunRefused):
            content._select()
        with self.assertRaises(TaskFileError):
            Runtime(root).execute()

    def test_rejected_and_revising_proposals_stay_off_the_board(self) -> None:
        service, root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        first, second = service.database.proposals()
        service.reject(first["id"], "too narrow", "sanchit@example.test")
        service.database.mark_revising(second["id"], "make it broader", "sanchit@example.test")

        board = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertNotIn("### TASK-", board)


class ThreeControlsProduceDistinctOutcomes(ProposalFlowTestCase):
    """Invariant 2."""

    def test_approve_mints_exactly_one_card_and_is_idempotent(self) -> None:
        service, root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]

        first = service.approve(proposal_id, "sanchit@example.test")
        second = service.approve(proposal_id, "sanchit@example.test")

        self.assertEqual(first["task_id"], second["task_id"])
        self.assertTrue(second["already_carded"])
        board = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertEqual(board.count("### TASK-"), 1)
        self.assertIn(f"- Proposal id: {proposal_id}", board)
        self.assertEqual(service.database.proposal(proposal_id)["status"], "carded")

    def test_approve_recovers_a_card_minted_before_a_crash(self) -> None:
        service, root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        # Simulate a crash between minting the card and recording the task id.
        service.database.mark_approved(proposal_id, "sanchit@example.test")
        version = service.database.proposal(proposal_id)["version"]
        minted = service._mint_card(proposal_id, version, "sanchit@example.test")

        result = service.approve(proposal_id, "sanchit@example.test")

        self.assertEqual(result["task_id"], minted)
        board = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertEqual(board.count("### TASK-"), 1)

    def test_suggest_changes_revises_in_place_without_a_card(self) -> None:
        proposer = FakeProposer()
        service, root = self.make_service(proposer=proposer)
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        proposer.rows = [
            {"title": "A narrower read of three wheeler battery data",
             "keywords": ["battery data"], "outline": "Narrowed to fleet buyers."}
        ]

        service.suggest_changes(proposal_id, "narrow it to fleet buyers", "sanchit@example.test")

        record = service.database.proposal(proposal_id)
        self.assertEqual(record["status"], "proposed")
        self.assertEqual(record["version"]["round"], 2)
        self.assertEqual(len(record["history"]), 2, "the earlier round must stay readable")
        self.assertEqual(record["history"][0]["round"], 1)
        self.assertNotIn("### TASK-", (root / "tasks.md").read_text(encoding="utf-8"))
        self.assertEqual(proposer.calls[-1]["revision_comment"], "narrow it to fleet buyers")

    def test_a_failed_revision_does_not_advance_the_round(self) -> None:
        proposer = FakeProposer()
        service, _root = self.make_service(proposer=proposer)
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        proposer.rows = []

        with self.assertRaises(ProposalRefused):
            service.suggest_changes(proposal_id, "narrow it", "sanchit@example.test")

        record = service.database.proposal(proposal_id)
        self.assertEqual(record["status"], "proposed")
        self.assertEqual(record["version"]["round"], 1)
        self.assertEqual(record["events"][-1]["action"], "revision-failed")

    def test_suggest_changes_requires_a_comment(self) -> None:
        service, _root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        with self.assertRaises(ConsoleDBError):
            service.suggest_changes(proposal_id, "   ", "sanchit@example.test")

    def test_reject_is_remembered_and_suppresses_a_reworded_re_proposal(self) -> None:
        proposer = FakeProposer()
        service, _root = self.make_service(proposer=proposer)
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[-1]["id"]
        rejected_title = service.database.proposal(proposal_id)["version"]["title"]

        service.reject(proposal_id, "we have covered this", "sanchit@example.test")

        # The same idea, reworded, comes back from a later run on another subject.
        proposer.rows = [
            {"title": "A three wheeler battery data sheet: what it actually tells drivers",
             "keywords": ["battery data"], "outline": "Same idea, different words."}
        ]
        run = service.propose("battery spec sheets for drivers", "sanchit@example.test")

        self.assertEqual(run.added, [])
        self.assertEqual(len(run.suppressed), 1)
        self.assertIn("previously rejected", run.suppressed[0]["reason"])
        self.assertIn(rejected_title, run.suppressed[0]["reason"])

    def test_rejection_is_reversible(self) -> None:
        service, _root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        service.reject(proposal_id, "not now", "sanchit@example.test")
        self.assertTrue(service.database.is_rejected(service.database.proposal(proposal_id)["norm_key"]))

        service.undo_rejection(proposal_id, "sanchit@example.test")

        self.assertFalse(service.database.is_rejected(service.database.proposal(proposal_id)["norm_key"]))

    def test_a_carded_proposal_cannot_be_rejected_here(self) -> None:
        service, _root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        service.approve(proposal_id, "sanchit@example.test")
        with self.assertRaises(ConsoleDBError):
            service.reject(proposal_id, "changed my mind", "sanchit@example.test")


class EveryProposalNamesItsSource(ProposalFlowTestCase):
    """Invariant 3."""

    def test_a_candidate_without_a_source_cannot_be_constructed(self) -> None:
        with self.assertRaises(ConsoleDBError):
            ProposalCandidate(
                title="A topic", keywords=(), outline="Body", source_kind="firecrawl", source_refs=()
            )

    def test_every_stored_proposal_carries_a_source(self) -> None:
        service, _root = self.make_service()
        service.propose("three wheeler battery data", "sanchit@example.test")
        for proposal in service.state()["proposals"]:
            self.assertTrue(proposal["source_kind"])
            self.assertTrue(proposal["source_refs"], proposal["title"])

    def test_a_run_with_no_evidence_at_all_proposes_nothing(self) -> None:
        service, _root = self.make_service(
            researcher=FakeResearcher(pages=0),
            search_console=FakeSearchConsole(message="Search Console is not connected."),
        )
        run = service.propose("three wheeler battery data", "sanchit@example.test")

        self.assertEqual(run.added, [])
        self.assertEqual(len(run.dropped), 2)
        self.assertEqual(run.dropped[0]["reason"], "no source could be named")

    def test_search_console_only_evidence_is_named_as_such(self) -> None:
        service, _root = self.make_service(
            researcher=FakeResearcher(pages=0),
            search_console=FakeSearchConsole(rows=[{"query": "e rickshaw battery data", "impressions": 40}]),
        )
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal = service.state()["proposals"][0]

        self.assertEqual(proposal["source_kind"], "search_console")
        self.assertEqual(proposal["source_refs"], ["gsc:e rickshaw battery data"])


class BudgetBehaviour(ProposalFlowTestCase):
    def test_research_is_refused_above_the_stop_threshold(self) -> None:
        service, _root = self.make_service(researcher=FakeResearcher(used=850, remaining=150))
        with self.assertRaises(ProposalRefused) as caught:
            service.propose("three wheeler battery data", "sanchit@example.test")
        self.assertIn("850", str(caught.exception))

    def test_the_same_subject_entered_twice_does_not_pay_twice(self) -> None:
        researcher = FakeResearcher()
        service, _root = self.make_service(researcher=researcher)
        first = service.propose("three wheeler battery data", "sanchit@example.test")
        spent = researcher.used

        second = service.propose("Data on three wheeler batteries", "sanchit@example.test")

        self.assertGreater(first.credits_used, 0)
        self.assertTrue(second.cache_hit)
        self.assertEqual(second.credits_used, 0)
        self.assertEqual(researcher.used, spent, "a cached subject must spend nothing")

    def test_a_proposal_run_never_requests_more_than_the_page_cap(self) -> None:
        researcher = FakeResearcher()
        service, _root = self.make_service(researcher=researcher)
        service.propose("three wheeler battery data", "sanchit@example.test")
        self.assertTrue(all(limit <= 5 for limit in researcher.discovered), researcher.discovered)

    def test_search_console_evidence_reduces_the_firecrawl_request(self) -> None:
        researcher = FakeResearcher()
        service, _root = self.make_service(
            researcher=researcher,
            search_console=FakeSearchConsole(rows=[{"query": "battery data", "impressions": 10}]),
        )
        service.propose("three wheeler battery data", "sanchit@example.test")
        self.assertEqual(researcher.discovered, [3], "free evidence must displace paid pages")

    def test_a_revision_reads_fewer_pages_than_a_first_pass(self) -> None:
        researcher = FakeResearcher()
        service, _root = self.make_service(researcher=researcher)
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposal_id = service.database.proposals()[0]["id"]
        researcher.discovered.clear()

        service.suggest_changes(proposal_id, "narrow it", "sanchit@example.test")

        self.assertTrue(all(limit <= 2 for limit in researcher.discovered), researcher.discovered)


class FingerprintTests(unittest.TestCase):
    def test_rewording_collapses_to_the_same_key(self) -> None:
        self.assertEqual(
            norm_key("Three wheeler battery data"), norm_key("Data on the three wheeler batteries")
        )

    def test_different_topics_do_not_collide(self) -> None:
        self.assertNotEqual(norm_key("Battery warranty terms"), norm_key("Charger safety standards"))


LEGACY_CARD = """### TASK-901 — What does it actually cost to replace an e-rickshaw battery

- ID: TASK-901
- Title: What does it actually cost to replace an e-rickshaw battery
- Owner: content
- Skill: content
- Priority: medium
- Status: Backlog
- Start date: not started
- Completed date: not completed
- Objective: Research and write a sourced article from this CEO-submitted topic.
- Acceptance criteria:
  - Preserve the CEO's topic wording as the writing instruction.
- Latest summary: Topic submitted from the CEO Console and queued for research-first writing.
- Description: CEO-submitted content topic queued for research and writing.
- Attachment: none
- Metric: Search impressions for the published blog page after publication.
- Tag: action to be taken by: cmo
- Topic stage: proposed
- Topic submitted by: ceo@itarang.com
- Change status: queued
- KPI gate: approved
- Last updated: 2026-08-04T10:00:00Z
- Updated: 2026-08-04T10:00:00Z"""


class LegacyCardHold(ProposalFlowTestCase):
    """Cards queued straight to the board before this flow existed."""

    def seed_legacy(self, service, root) -> str:
        service.task_file.add_board_cards([LEGACY_CARD], section="Backlog")
        return "TASK-901"

    def test_the_legacy_card_is_writable_until_it_is_held(self) -> None:
        service, root = self.make_service()
        task_id = self.seed_legacy(service, root)

        content = ContentRuntime(root, researcher=object(), writer=object())
        self.assertEqual(content._select().task_id, task_id, "this is the case Apoorv objected to")

    def test_a_held_card_becomes_a_proposal_and_stops_being_writable(self) -> None:
        service, root = self.make_service()
        task_id = self.seed_legacy(service, root)

        results = hold_legacy_cards(root, [task_id], database=service.database)

        self.assertTrue(results[0]["held"], results)
        board = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("- Change status: pending human decision", board)
        self.assertIn("- Topic stage: held for proposal review", board)
        self.assertIn(task_id, board, "the card must be set aside, never deleted")
        content = ContentRuntime(root, researcher=object(), writer=object())
        with self.assertRaises(ContentRunRefused):
            content._select()

    def test_a_held_card_is_named_as_the_source_of_its_proposal(self) -> None:
        service, root = self.make_service()
        task_id = self.seed_legacy(service, root)

        hold_legacy_cards(root, [task_id], database=service.database)

        proposal = service.database.proposals(statuses=["proposed"])[0]
        self.assertEqual(proposal["version"]["source_kind"], "legacy_board")
        self.assertEqual(proposal["version"]["source_refs"], [f"board:{task_id}"])
        self.assertIn("cost", proposal["version"]["title"])

    def test_holding_twice_is_a_no_op(self) -> None:
        service, root = self.make_service()
        task_id = self.seed_legacy(service, root)
        hold_legacy_cards(root, [task_id], database=service.database)

        second = hold_legacy_cards(root, [task_id], database=service.database)

        self.assertFalse(second[0]["held"])
        self.assertEqual(len(service.database.proposals(statuses=["proposed"])), 1)


class ResearchPassAccounting(unittest.TestCase):
    def test_credits_used_is_the_measured_delta(self) -> None:
        research = ResearchPass(
            subject="x", gsc_rows=(), gsc_message="", pages=(), pages_requested=5,
            credits_before=100, credits_after=105, credits_remaining=895,
        )
        self.assertEqual(research.credits_used, 5)

    def test_a_cache_hit_reports_no_spend(self) -> None:
        research = ResearchPass(
            subject="x", gsc_rows=(), gsc_message="", pages=(), pages_requested=0,
            credits_before=None, credits_after=None, credits_remaining=895, cache_hit_of=3,
        )
        self.assertEqual(research.credits_used, 0)
        self.assertEqual(research.source_kind(), "cache")


SIBLING_ROWS = [
    {"title": f"Sibling candidate {index}", "keywords": [f"keyword {index}"],
     "outline": f"Outline for sibling candidate {index}."}
    for index in (1, 2, 3, 4)
]


class ApprovingOneTopicSetsTheRestAside(ProposalFlowTestCase):
    """One subject is one decision, so the losing candidates leave the screen.

    They are set aside, not vetoed. That distinction is the whole design: a
    rejection is remembered by norm_key and suppresses the idea for good, while an
    archived candidate can be restored by hand and is resurfaced on its own when
    research finds it again.
    """

    def fan_out(self):
        service, root = self.make_service(proposer=FakeProposer(SIBLING_ROWS))
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposals = service.database.proposals(statuses=["proposed"])
        return service, root, proposals

    def test_approving_archives_the_siblings_and_nothing_else(self) -> None:
        service, _root, proposals = self.fan_out()
        chosen = proposals[0]["id"]
        siblings = sorted(item["id"] for item in proposals[1:])

        outcome = service.approve(chosen, "sanchit@example.test")

        self.assertEqual(sorted(item["id"] for item in outcome["archived"]), siblings)
        self.assertEqual(service.database.proposal(chosen)["status"], "carded")
        for sibling in siblings:
            self.assertEqual(service.database.proposal(sibling)["status"], "archived")

    def test_a_second_subject_is_untouched_by_the_first_ones_decision(self) -> None:
        service, _root, proposals = self.fan_out()
        service.proposer.rows = [
            {"title": "Unrelated candidate", "keywords": ["unrelated"],
             "outline": "An outline about something else entirely."}
        ]
        service.propose("charging habits", "sanchit@example.test")
        other = service.database.proposals(statuses=["proposed"])
        other_id = next(
            item["id"] for item in other
            if item["version"]["title"] == "Unrelated candidate"
        )

        service.approve(proposals[0]["id"], "sanchit@example.test")

        self.assertEqual(service.database.proposal(other_id)["status"], "proposed")

    def test_archiving_writes_nothing_to_the_rejection_memory(self) -> None:
        service, _root, proposals = self.fan_out()
        service.approve(proposals[0]["id"], "sanchit@example.test")

        self.assertEqual(service.database.rejected_topics(), [])

    def test_approving_twice_archives_once_and_mints_once(self) -> None:
        service, root = self.make_service(proposer=FakeProposer(SIBLING_ROWS))
        service.propose("three wheeler battery data", "sanchit@example.test")
        proposals = service.database.proposals(statuses=["proposed"])
        chosen = proposals[0]["id"]

        first = service.approve(chosen, "sanchit@example.test")
        second = service.approve(chosen, "sanchit@example.test")

        self.assertEqual(first["task_id"], second["task_id"])
        self.assertEqual(second["archived"], [])
        board = (root / "tasks.md").read_text(encoding="utf-8")
        self.assertEqual(board.count("### TASK-"), 1)

    def test_the_archived_stay_off_the_pool_and_show_on_the_shelf(self) -> None:
        service, _root, proposals = self.fan_out()
        siblings = {item["id"] for item in proposals[1:]}
        service.approve(proposals[0]["id"], "sanchit@example.test")

        state = service.state()

        self.assertEqual({item["id"] for item in state["proposals"]} & siblings, set())
        self.assertEqual({item["id"] for item in state["archived"]}, siblings)

    def test_restore_returns_one_to_the_pool_and_refuses_anything_else(self) -> None:
        service, _root, proposals = self.fan_out()
        chosen = proposals[0]["id"]
        sibling = proposals[1]["id"]
        service.approve(chosen, "sanchit@example.test")

        service.restore(sibling, "sanchit@example.test")

        self.assertEqual(service.database.proposal(sibling)["status"], "proposed")
        with self.assertRaisesRegex(ConsoleDBError, "not archived"):
            service.restore(chosen, "sanchit@example.test")

    def test_archiving_by_hand_takes_one_off_the_screen(self) -> None:
        service, _root, proposals = self.fan_out()
        target = proposals[0]["id"]

        service.archive(target, "sanchit@example.test")

        self.assertEqual(service.database.proposal(target)["status"], "archived")
        self.assertEqual(service.database.rejected_topics(), [])
        with self.assertRaisesRegex(ConsoleDBError, "nothing to archive"):
            service.archive(target, "sanchit@example.test")

    def test_research_resurfaces_an_archived_topic_rather_than_dropping_it(self) -> None:
        """An archived idea that becomes news again must come back.

        If the archive behaved like a live proposal, `add_candidates` would report
        the returning candidate as a duplicate and it would never be seen again —
        a silent veto with none of a rejection's deliberateness.
        """
        service, _root, proposals = self.fan_out()
        service.approve(proposals[0]["id"], "sanchit@example.test")
        shelved = proposals[1]["version"]["title"]

        service.proposer.rows = [
            {"title": shelved, "keywords": ["keyword 2"], "outline": "Outline for sibling candidate 2."}
        ]
        run = service.propose("three wheeler battery data again", "sanchit@example.test")

        self.assertEqual([item["title"] for item in run.resurfaced], [shelved])
        self.assertEqual(run.duplicates, [])
        self.assertEqual(service.database.proposal(proposals[1]["id"])["status"], "proposed")

    def test_a_rejected_topic_is_still_suppressed_not_resurfaced(self) -> None:
        service, _root, proposals = self.fan_out()
        rejected = proposals[1]
        service.reject(rejected["id"], "covered already", "sanchit@example.test")

        service.proposer.rows = [
            {"title": rejected["version"]["title"], "keywords": ["keyword 2"],
             "outline": "Outline for sibling candidate 2."}
        ]
        run = service.propose("three wheeler battery data again", "sanchit@example.test")

        self.assertEqual(run.resurfaced, [])
        self.assertEqual(len(run.suppressed), 1)


if __name__ == "__main__":
    unittest.main()
