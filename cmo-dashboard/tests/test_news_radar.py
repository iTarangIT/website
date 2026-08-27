"""The EV news radar: what it refuses, what it costs, and what it hands on.

Nothing here touches the network or Hermes. The researcher and the triager are
both stood in for, the same way the proposal suite stands in for Firecrawl, so a
failing test means the radar's own logic moved and never means the beat was quiet.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmo_runtime import news_radar  # noqa: E402
from cmo_runtime.news_radar import NewsRadar, RadarRefused  # noqa: E402
from cmo_runtime.topic_proposals import ProposalRefused, SourcePage  # noqa: E402

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

BEATS = (("policy", "India EV policy"), ("battery-tech", "sodium ion battery"))


class FakeSearchConsole:
    def demand(self, subject: str):
        return [], ""


class FakeResearcher:
    """Counts what it was asked for, so the sweep's spend stays measurable."""

    def __init__(self, *, remaining=900, used=100, fail_beats=()) -> None:
        self.remaining = remaining
        self.used = used
        self.connected = True
        self.fail_beats = set(fail_beats)
        self.searches: list[tuple[str, int, str]] = []
        self.retrieved: list[str] = []

    def credit_state(self):
        return self.used, self.remaining

    def search(self, query: str, limit: int, *, tbs: str = ""):
        self.searches.append((query, limit, tbs))
        if query in self.fail_beats:
            raise ProposalRefused(f"Firecrawl /v2/search failed for {query}")
        return [
            {
                "url": f"https://news.test/{abs(hash(query)) % 1000}/{index}",
                "title": f"{query} headline {index}",
                "description": "A development in the EV ecosystem.",
            }
            for index in range(limit)
        ]

    def discover(self, subject: str, limit: int, *, tbs: str = ""):
        return [row["url"] for row in self.search(subject, limit, tbs=tbs)]

    def retrieve(self, urls):
        pages = []
        for url in list(urls)[:2]:
            self.retrieved.append(url)
            pages.append(SourcePage(title=f"Page {url}", url=url, markdown="evidence body"))
        self.used += len(pages)
        self.remaining -= len(pages)
        return pages


class FakeTriager:
    def __init__(self, rows=None, error: Exception | None = None) -> None:
        self.rows = rows if rows is not None else [
            {"subject": "CAQM bans new non-electric light goods vehicles from 2027"},
            {"subject": "Sodium-ion cells enter Indian three-wheeler packs"},
        ]
        self.error = error
        self.calls: list[dict] = []

    def triage(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return list(self.rows)


class FakeProposer:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def propose(self, **kwargs):
        self.calls.append(kwargs)
        return [
            {
                "title": f"Candidate from {kwargs['subject'][:40]}",
                "keywords": ["ev"],
                "outline": "An outline grounded in the evidence.",
            }
        ]


class RadarTestCase(unittest.TestCase):
    def make_radar(self, *, researcher=None, triager=None, beats=BEATS):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()
        (root / "tasks.md").write_text(EMPTY_BOARD, encoding="utf-8")
        from cmo_runtime.topic_proposals import TopicProposalService

        self.researcher = researcher or FakeResearcher()
        self.proposer = FakeProposer()
        service = TopicProposalService(
            root,
            researcher=self.researcher,
            search_console=FakeSearchConsole(),
            proposer=self.proposer,
        )
        radar = NewsRadar(
            root,
            service=service,
            database=service.database,
            triager=triager or FakeTriager(),
            beats=beats,
        )
        self.addCleanup(service.database.close)
        return radar, root


class TheSweepRefusesBeforeItSpends(RadarTestCase):
    def test_a_low_balance_stops_the_sweep_before_any_search(self) -> None:
        """The daily job must never be why a manual subject cannot be researched."""
        researcher = FakeResearcher(remaining=news_radar.RADAR_CREDIT_FLOOR - 1)
        radar, _root = self.make_radar(researcher=researcher)

        sweep = radar.scan("news-radar", mode="due")

        self.assertEqual(sweep.status, "refused")
        self.assertIn("floor", sweep.message)
        self.assertEqual(researcher.searches, [])
        self.assertEqual(self.proposer.calls, [])

    def test_a_refusal_is_still_recorded(self) -> None:
        """A sweep that left no trace reads as a sweep that never ran."""
        radar, _root = self.make_radar(
            researcher=FakeResearcher(remaining=news_radar.RADAR_CREDIT_FLOOR - 1)
        )
        radar.scan("news-radar", mode="due")

        run = radar.database.latest_radar_run()
        self.assertEqual(run["status"], "refused")
        self.assertEqual(run["mode"], "due")

    def test_a_disconnected_firecrawl_refuses_rather_than_degrades(self) -> None:
        researcher = FakeResearcher()
        researcher.connected = False
        radar, _root = self.make_radar(researcher=researcher)

        sweep = radar.scan("news-radar")

        self.assertEqual(sweep.status, "refused")
        self.assertEqual(researcher.searches, [])


class DiscoveryIsFreeAndRecent(RadarTestCase):
    def test_every_beat_is_searched_within_the_recency_window(self) -> None:
        radar, _root = self.make_radar()

        radar.scan("news-radar")

        beat_queries = {query for _slug, query in BEATS}
        beat_searches = [row for row in self.researcher.searches if row[0] in beat_queries]
        self.assertEqual({query for query, _limit, _tbs in beat_searches}, beat_queries)
        self.assertEqual({tbs for _query, _limit, tbs in beat_searches}, {news_radar.RADAR_RECENCY})
        self.assertEqual(
            {limit for _query, limit, _tbs in beat_searches},
            {news_radar.RADAR_DISCOVERY_LIMIT},
        )

    def test_the_research_that_follows_is_not_narrowed_to_the_week(self) -> None:
        """Only the radar wants recency. The evidence behind a topic does not:
        a 2023 gazette notification is exactly the source a policy piece needs."""
        radar, _root = self.make_radar()

        sweep = radar.scan("news-radar")

        beat_queries = {query for _slug, query in BEATS}
        follow_ups = [row for row in self.researcher.searches if row[0] not in beat_queries]
        self.assertTrue(follow_ups, "the sweep researched nothing")
        self.assertEqual({tbs for _query, _limit, tbs in follow_ups}, {""})
        self.assertTrue(sweep.subjects)

    def test_one_dead_beat_does_not_end_the_sweep(self) -> None:
        radar, _root = self.make_radar(researcher=FakeResearcher(fail_beats=["India EV policy"]))

        sweep = radar.scan("news-radar")

        self.assertEqual(sweep.status, "completed")
        self.assertTrue(sweep.headlines)
        self.assertTrue(any("India EV policy" in message for message in sweep.messages))

    def test_social_hosts_never_reach_triage(self) -> None:
        radar, _root = self.make_radar()
        radar.scan("news-radar")

        triager = radar.triager
        headlines = triager.calls[0]["headlines"]
        self.assertTrue(headlines)
        for item in headlines:
            self.assertNotIn(news_radar._host(item.url), news_radar.BLOCKED_HOSTS)


class TheCapIsEnforcedHereNotInThePrompt(RadarTestCase):
    def test_more_subjects_than_asked_for_are_cut_to_the_cap(self) -> None:
        """A model that returns nine must cost three subjects, not nine."""
        rows = [{"subject": f"Distinct EV development number {index}"} for index in range(9)]
        radar, _root = self.make_radar(triager=FakeTriager(rows))

        sweep = radar.scan("news-radar")

        self.assertEqual(len(sweep.subjects), news_radar.RADAR_MAX_SUBJECTS)
        self.assertEqual(len(self.proposer.calls), news_radar.RADAR_MAX_SUBJECTS)

    def test_a_subject_already_researched_is_dropped(self) -> None:
        radar, _root = self.make_radar()
        radar.service.propose("Sodium-ion cells enter Indian three-wheeler packs", "ceo@test")
        before = len(self.proposer.calls)

        sweep = radar.scan("news-radar")

        self.assertNotIn("Sodium-ion cells enter Indian three-wheeler packs", sweep.subjects)
        self.assertEqual(len(self.proposer.calls) - before, len(sweep.subjects))

    def test_an_empty_triage_is_a_correct_answer(self) -> None:
        radar, _root = self.make_radar(triager=FakeTriager([]))

        sweep = radar.scan("news-radar")

        self.assertEqual(sweep.subjects, [])
        self.assertEqual(self.proposer.calls, [])
        self.assertIn("worth researching", sweep.message)


class DryRunSpendsNothing(RadarTestCase):
    def test_a_dry_run_names_the_subjects_and_retrieves_no_page(self) -> None:
        radar, _root = self.make_radar()

        sweep = radar.scan("news-radar", dry_run=True)

        self.assertEqual(sweep.status, "completed")
        self.assertTrue(sweep.subjects)
        self.assertEqual(self.researcher.retrieved, [])
        self.assertEqual(self.proposer.calls, [])
        self.assertEqual(sweep.credits_used, 0)
        self.assertEqual(radar.database.latest_radar_run()["mode"], "dry-run")


class TheSweepHandsOnToTheExistingPipeline(RadarTestCase):
    def test_each_subject_becomes_candidates_through_propose(self) -> None:
        radar, root = self.make_radar()

        sweep = radar.scan("news-radar")

        self.assertEqual(sweep.status, "completed")
        self.assertEqual(len(sweep.added), len(sweep.subjects))
        self.assertEqual(
            [call["subject"] for call in self.proposer.calls], sweep.subjects
        )
        # Proposing still writes no board card. The radar changed who starts the
        # pipeline, not what approving means.
        self.assertNotIn("### TASK-", (root / "tasks.md").read_text(encoding="utf-8"))

    def test_one_refused_subject_does_not_lose_the_others(self) -> None:
        radar, _root = self.make_radar()
        original = radar.service.propose
        calls: list[str] = []

        def flaky(subject, actor):
            calls.append(subject)
            if len(calls) == 1:
                raise ProposalRefused("research refused for this one")
            return original(subject, actor)

        radar.service.propose = flaky
        sweep = radar.scan("news-radar")

        self.assertEqual(sweep.status, "completed")
        self.assertEqual(len(calls), len(sweep.subjects))
        self.assertTrue(sweep.added)
        self.assertTrue(any("research refused" in message for message in sweep.messages))

    def test_a_broken_triager_refuses_rather_than_researching_nothing(self) -> None:
        radar, _root = self.make_radar(
            triager=FakeTriager(error=RadarRefused("triager exited 1: no output"))
        )

        sweep = radar.scan("news-radar")

        self.assertEqual(sweep.status, "refused")
        self.assertIn("Triage failed", sweep.message)
        self.assertEqual(self.proposer.calls, [])


class TheBeatIsSteerableWithoutARedeploy(RadarTestCase):
    def test_the_watchlist_adds_a_beat(self) -> None:
        radar, root = self.make_radar()
        (root / "state" / "ceo-watchlist.json").write_text(
            '["battery passport"]', encoding="utf-8"
        )

        beats = radar.beats()

        self.assertIn("watchlist", [slug for slug, _query in beats])
        self.assertTrue(any("battery passport" in query for _slug, query in beats))

    def test_an_unreadable_watchlist_is_not_a_broken_beat(self) -> None:
        radar, root = self.make_radar()
        (root / "state" / "ceo-watchlist.json").write_text("not json", encoding="utf-8")

        self.assertEqual([slug for slug, _query in radar.beats()], [slug for slug, _ in BEATS])


if __name__ == "__main__":
    unittest.main()
