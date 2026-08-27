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
from cmo_runtime.news_radar import IST, NewsRadar, RadarRefused, _due  # noqa: E402
from cmo_runtime.topic_proposals import ProposalRefused, SourcePage  # noqa: E402

import contextlib  # noqa: E402
import datetime as dt  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402

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
    """Counts what it was asked for, so the sweep's spend stays measurable.

    `cost_per_page` exists because a page is not a credit: a measured run billed
    17 credits for one page. The default of 1 keeps the cheap tests readable; the
    ceiling tests raise it to reproduce what actually happened.

    `cost_per_search` defaults to 4 because that is what a beat search measured
    at — roughly 3.7 credits. It is deliberately not 0: the first version of this
    fixture billed nothing for search, which is exactly the assumption that put
    "discovery is free" into the docs and the dry-run message.
    """

    def __init__(
        self, *, remaining=900, used=100, fail_beats=(), cost_per_page=1, cost_per_search=4
    ) -> None:
        self.remaining = remaining
        self.used = used
        self.cost_per_page = cost_per_page
        self.cost_per_search = cost_per_search
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
        self.used += self.cost_per_search
        self.remaining -= self.cost_per_search
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
        spend = len(pages) * self.cost_per_page
        self.used += spend
        self.remaining -= spend
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


class TheSweepIsBoundedByMeasuredSpend(RadarTestCase):
    """A page cap is not a credit cap.

    Measured 2026-08-27: one subject billed 85 credits for 5 pages while its two
    siblings billed 5 and 4. `PROPOSAL_PAGE_CAP` bounded the pages exactly as
    designed and bounded the money not at all, so an unattended daily job needs a
    ceiling it measures rather than one it assumes.
    """

    def test_an_expensive_subject_stops_the_sweep_before_the_next_one(self) -> None:
        rows = [{"subject": f"Distinct EV development number {index}"} for index in range(3)]
        radar, _root = self.make_radar(
            researcher=FakeResearcher(cost_per_page=30), triager=FakeTriager(rows)
        )

        sweep = radar.scan("news-radar")

        self.assertEqual(len(self.proposer.calls), 1, "a second subject was researched anyway")
        self.assertEqual(sweep.subjects, sweep.subjects[:1])
        self.assertTrue(any("not researched" in message for message in sweep.messages))
        self.assertTrue(any("ceiling" in message for message in sweep.messages))

    def test_what_was_dropped_is_named_not_silently_skipped(self) -> None:
        """A sweep that researched one of three and said nothing reads as a beat
        with nothing else worth having."""
        rows = [{"subject": f"Distinct EV development number {index}"} for index in range(3)]
        radar, _root = self.make_radar(
            researcher=FakeResearcher(cost_per_page=30), triager=FakeTriager(rows)
        )

        sweep = radar.scan("news-radar")

        self.assertTrue(any("2 subject(s) not researched" in m for m in sweep.messages))
        self.assertEqual(radar.database.latest_radar_run()["status"], "completed")

    def test_cheap_subjects_all_get_researched(self) -> None:
        # Cheap on both axes. `propose()` pays for its own discovery search as
        # well as its pages, so a sweep's bill is beats + subjects + pages, not
        # pages alone — which is why the realistic default overshoots the ceiling.
        rows = [{"subject": f"Distinct EV development number {index}"} for index in range(3)]
        radar, _root = self.make_radar(
            researcher=FakeResearcher(cost_per_page=1, cost_per_search=1),
            triager=FakeTriager(rows),
        )

        sweep = radar.scan("news-radar")

        self.assertEqual(len(self.proposer.calls), 3)
        self.assertLess(sweep.credits_used, news_radar.RADAR_SWEEP_CREDIT_CEILING)
        self.assertFalse(any("not researched" in m for m in sweep.messages))


class DiscoveryIsBilledAndSaysSo(RadarTestCase):
    """Searching is metered too. Measured: ~3.7 credits a beat search, which is a
    fifth of the daily budget for a sweep that has not researched anything yet."""

    def test_the_sweep_counts_what_discovery_cost(self) -> None:
        radar, _root = self.make_radar()

        sweep = radar.scan("news-radar")

        expected = len(BEATS) * self.researcher.cost_per_search
        self.assertEqual(sweep.discovery_credits, expected)
        self.assertGreaterEqual(sweep.credits_used, expected)

    def test_discovery_alone_can_reach_the_ceiling(self) -> None:
        """If it does, nothing is researched — and that has to be visible rather
        than looking like a beat with no news."""
        radar, _root = self.make_radar(
            researcher=FakeResearcher(cost_per_search=news_radar.RADAR_SWEEP_CREDIT_CEILING)
        )

        sweep = radar.scan("news-radar")

        self.assertEqual(self.proposer.calls, [])
        self.assertTrue(any("not researched" in message for message in sweep.messages))


class DryRunRetrievesNothingButStillPays(RadarTestCase):
    def test_a_dry_run_names_the_subjects_and_retrieves_no_page(self) -> None:
        radar, _root = self.make_radar()

        sweep = radar.scan("news-radar", dry_run=True)

        self.assertEqual(sweep.status, "completed")
        self.assertTrue(sweep.subjects)
        self.assertEqual(self.researcher.retrieved, [])
        self.assertEqual(self.proposer.calls, [])
        self.assertEqual(radar.database.latest_radar_run()["mode"], "dry-run")

    def test_a_dry_run_does_not_claim_to_be_free(self) -> None:
        """It is the thing people run in a loop while tuning the beats."""
        radar, _root = self.make_radar()

        sweep = radar.scan("news-radar", dry_run=True)

        self.assertGreater(sweep.discovery_credits, 0)
        self.assertNotIn("0 credits", sweep.message)
        self.assertIn(f"{sweep.discovery_credits} credits", sweep.message)


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

    def test_a_long_watchlist_cannot_outgrow_the_beat_budget(self) -> None:
        """A beat is a flat 2 credits, so the beat count *is* the discovery bill.
        Unbounded, a filled watchlist plus a competitor list put fifteen searches
        in front of a sweep that had not researched anything yet."""
        radar, root = self.make_radar(beats=news_radar.DEFAULT_BEATS)
        (root / "state" / "ceo-watchlist.json").write_text(
            json.dumps([f"keyword {index}" for index in range(20)]), encoding="utf-8"
        )

        beats = radar.beats()

        self.assertLessEqual(len(beats), news_radar.RADAR_MAX_BEATS)

    def test_the_standing_beat_is_never_crowded_out_by_the_watchlist(self) -> None:
        radar, root = self.make_radar(beats=news_radar.DEFAULT_BEATS)
        (root / "state" / "ceo-watchlist.json").write_text(
            json.dumps([f"keyword {index}" for index in range(20)]), encoding="utf-8"
        )

        slugs = [slug for slug, _query in radar.beats()]

        for slug, _query in news_radar.DEFAULT_BEATS:
            self.assertIn(slug, slugs, f"the {slug} beat was displaced by the watchlist")

    def test_three_typical_subjects_fit_under_the_ceiling(self) -> None:
        """The sizing this budget exists for: 4 default beats at 2 credits, then
        three subjects at a measured-typical 5 each, is 25 against a 28 ceiling.
        If this fails the radar silently starts researching two a day."""
        rows = [{"subject": f"Distinct EV development number {index}"} for index in range(3)]
        radar, _root = self.make_radar(
            beats=news_radar.DEFAULT_BEATS,
            # 2 a search and 3 pages a subject at ~1 a page reproduces the two
            # cheap runs measured on 2026-08-27 (5 and 4 credits).
            researcher=FakeResearcher(cost_per_search=2, cost_per_page=1),
            triager=FakeTriager(rows),
        )

        sweep = radar.scan("news-radar")

        self.assertEqual(len(sweep.added), 3, "a typical day must research three subjects")
        self.assertLessEqual(sweep.credits_used, news_radar.RADAR_SWEEP_CREDIT_CEILING)

    def test_an_unreadable_watchlist_is_not_a_broken_beat(self) -> None:
        radar, root = self.make_radar()
        (root / "state" / "ceo-watchlist.json").write_text("not json", encoding="utf-8")

        self.assertEqual([slug for slug, _query in radar.beats()], [slug for slug, _ in BEATS])


class TheLockSaysWhatWentWrong(unittest.TestCase):
    def test_a_lock_that_cannot_be_taken_names_the_cause_not_a_traceback(self) -> None:
        """This happened for real: a run as root left a root-owned
        state/news-radar.lock, and every hermes tick afterwards died on a
        PermissionError raised by `touch` — which reads as a missing file rather
        than as the wrong user, and cost a debugging round to recognise.

        The trigger here is an unusable `state` path rather than a mode bit,
        because a suite running as root ignores mode bits and would pass while
        the branch never ran. Same `except OSError`, same message, and it holds
        whoever the suite runs as."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").write_text("not a directory", encoding="utf-8")

        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            code = news_radar.main(["--profile", str(root), "--force"])

        self.assertEqual(code, 1)
        self.assertIn("cannot take the radar lock", errors.getvalue())
        self.assertIn("run this as hermes", errors.getvalue())


class TheDailyClock(unittest.TestCase):
    """`--due` is the whole schedule. There is no cron on this box: the loop that
    calls it ticks every half hour and this decides whether a tick is the day's
    sweep. Getting it wrong is either a silently skipped day or a sweep that pays
    for the same headlines twice."""

    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "state").mkdir()
        self.stamp = self.root / "state" / "news-radar-last-run"

    @staticmethod
    def at(day: int, hour: int, minute: int = 0) -> dt.datetime:
        return dt.datetime(2026, 8, day, hour, minute, tzinfo=IST)

    def test_before_the_window_is_not_due(self) -> None:
        due, reason = _due(self.root, self.at(27, 6, 59))
        self.assertFalse(due)
        self.assertIn("before the daily window", reason)

    def test_a_first_ever_run_is_due_once_the_window_opens(self) -> None:
        due, reason = _due(self.root, self.at(27, 7, 0))
        self.assertTrue(due)
        self.assertIn("no previous run", reason)

    def test_a_second_tick_the_same_day_is_not_due(self) -> None:
        self.stamp.write_text(self.at(27, 7, 2).isoformat(), encoding="utf-8")

        due, reason = _due(self.root, self.at(27, 7, 30))

        self.assertFalse(due)
        self.assertIn("already swept", reason)

    def test_the_next_morning_is_due_again(self) -> None:
        self.stamp.write_text(self.at(27, 7, 2).isoformat(), encoding="utf-8")

        self.assertFalse(_due(self.root, self.at(28, 6, 30))[0], "still yesterday's window")
        self.assertTrue(_due(self.root, self.at(28, 7, 1))[0], "a new day must sweep")

    def test_a_container_asleep_through_the_window_still_sweeps_and_says_it_was_late(self) -> None:
        """A skipped day is worse than a late one: nothing on the console says why
        no topics arrived."""
        self.stamp.write_text(self.at(26, 7, 0).isoformat(), encoding="utf-8")

        due, reason = _due(self.root, self.at(27, 14, 0))

        self.assertTrue(due)
        self.assertIn("late", reason)

    def test_an_unreadable_stamp_sweeps_rather_than_stalling_forever(self) -> None:
        self.stamp.write_text("not a timestamp", encoding="utf-8")

        self.assertTrue(_due(self.root, self.at(27, 8, 0))[0])

    def test_the_window_is_seven_in_the_morning_india_time(self) -> None:
        self.assertEqual(news_radar.RADAR_HOUR_IST, 7)
        self.assertEqual(str(IST), "Asia/Kolkata")


if __name__ == "__main__":
    unittest.main()
