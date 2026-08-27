"""Invariants 1, 4, 5 and 6 — checked by executing the console, not by grepping it.

`console_harness.js` boots ceo_script.py's SCRIPT against a small DOM and a fixture
state, then reports what each panel rendered. That is the check that was missing:
the old reader lived in a JavaScript string nothing ever ran, so every suite stayed
green while it printed table pipes on screen.

Skipped when node is unavailable; `run-tests` reports the skip rather than passing
quietly.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import ceo_reader
from ceo_script import SCRIPT

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")

ARTICLE = """---
title: Battery replacement, city by city
slug: battery-replacement
---

# Battery replacement, city by city

A rider asking about **replacement cost** wants one number, not a *survey*.

| City | Price band | Wait |
|---|---:|:---:|
| Delhi | **12,000–18,000** | 2 days |
| Jaipur | **11,500–17,000** | 3 days |

## Decision bullets:

- **Measure first.** Check Search Console before commissioning more pages.
"""


def _slots() -> list[dict[str, object]]:
    return []


def _task(task_id: str = "TASK-901", title: str = "Battery replacement, city by city") -> dict:
    rendered = ceo_reader.render_article(ARTICLE, _slots())
    _metadata, body = ceo_reader.strip_front_matter(ARTICLE)
    return {
        "id": task_id,
        "title": title,
        "decision_status": "awaiting decision",
        "decision_approved": False,
        "change_status": "awaiting gate 1",
        "revision_round": "0",
        "approval_thread": [],
        "publishing_pipeline": None,
        "article": {
            "text": body,
            "metadata": {"slug": "battery-replacement"},
            "html": rendered["html"],
            "review_notes_html": rendered["review_notes_html"],
            "review_note_titles": rendered["review_note_titles"],
            "word_count": 120,
            "read_minutes": 1,
            "image_slots": [],
            "files": [],
            "revisions": [{"round": 1, "name": "TASK-901-content.r1.md", "bytes": 900}],
        },
    }


def _proposal(index: int) -> dict:
    return {
        "id": index,
        "title": f"Candidate topic {index}",
        "subject": "battery replacement",
        "outline": "An outline for candidate topic.",
        "keywords": ["battery", f"keyword{index}"],
        "status": "proposed" if index % 3 else "revising",
        "round": 1,
        "source_kind": "search_console",
        "source_refs": [f"gsc:query {index}"],
        "history": [],
    }


def _archived(index: int, subject_id: int) -> dict:
    return {
        "id": 1000 + index,
        "title": f"Archived candidate {index}",
        "subject_id": subject_id,
        "subject": f"archived subject {subject_id}",
        "outline": "An outline for an archived candidate.",
        "keywords": ["battery"],
        "status": "archived",
        "round": 1,
        "source_kind": "firecrawl",
        "source_refs": [f"https://source.test/{index}"],
        "created_at": "2026-08-20T00:00:00Z",
        "updated_at": "2026-08-26T00:00:00Z",
        "history": [],
    }


def _fixture(*, proposals: int = 28, blogs: int = 33, queries: int = 40, ui: dict | None = None,
             archived: list | None = None, radar: dict | None = None) -> dict:
    series = [
        {"date": f"2026-08-{day:02d}", "impressions": day * 12, "clicks": day % 4, "ctr": 1.4, "position": 12.5}
        for day in range(1, 15)
    ]
    query_rows = [
        {
            "query": f"battery query {index}",
            "impressions": 200 - index * 3,
            "clicks": 0 if index < 3 else index,
            "ctr": 0.0 if index < 3 else 1.2,
            "position": 18.4,
        }
        for index in range(queries)
    ]
    return {
        "ui": ui,
        "state": {
            "topics": {
                "proposals": [_proposal(index) for index in range(1, proposals + 1)],
                "archived": [] if archived is None else archived,
                "rejected": [],
                "carded": [],
                "radar": radar,
                "budget": {"status": "not_connected", "message": ""},
            },
            "blogs": [_task(f"TASK-{900 + index}", f"Article {index}") for index in range(blogs)],
            "trending": [],
            "trending_messages": [],
            "watchlist": [],
            "research_queue": [{"subject": "battery query 0", "reason": "Queued from Analytics.", "queued_by": "x"}],
            "analytics": {
                "search": {
                    "status": "ready",
                    "message": "",
                    "range": {"key": "28", "label": "28 days", "start": "2026-08-01", "end": "2026-08-14", "days": 14},
                    "device": "all",
                    "collection_start": "2026-08-04",
                    "reporting_delay_days": 2,
                    "totals": {"impressions": 5400, "clicks": 42, "ctr": 0.78, "position": 14.2, "indexed_pages": None},
                    "previous": {"impressions": 4100, "clicks": 51, "ctr": 1.24, "position": 15.9},
                    "deltas": {"impressions": 1300, "clicks": -9, "ctr": -0.46, "position": -1.7},
                    "series": series,
                    "queries": query_rows,
                    "pages": [
                        {"page": "https://itarang.com/blog/emi", "impressions": 90, "clicks": 4, "ctr": 4.4, "position": 15.5}
                    ],
                    "opportunities": [
                        {
                            "kind": "unclicked",
                            "subject": f"battery query {index}",
                            "source": "query",
                            "reason": "Seen 140 times in search and clicked none.",
                            "impressions": 140 - index,
                            "clicks": 0,
                            "position": 18.4,
                        }
                        for index in range(14)
                    ],
                },
                "search_console": {"status": "collecting"},
                "ga4": {"status": "not_connected", "message": "Google Analytics is not connected yet",
                        "required_variables": ["GA4_PROPERTY_ID"]},
                "competitor": {"status": "none"},
            },
            "controls": {"range": "28", "device": "all"},
        },
    }


@unittest.skipUnless(NODE, "node is required to execute the console script")
class ConsoleRenders(unittest.TestCase):
    maxDiff = None

    @classmethod
    def run_console(cls, fixture: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "console.js").write_text(SCRIPT, encoding="utf-8")
            (root / "fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
            result = subprocess.run(
                [NODE, str(HERE / "console_harness.js"), str(root / "console.js"), str(root / "fixture.json")],
                capture_output=True, text=True, timeout=60, check=False,
            )
        if result.returncode != 0:
            raise AssertionError(f"the console script failed to run:\n{result.stderr}")
        return json.loads(result.stdout)

    @classmethod
    def setUpClass(cls) -> None:
        cls.out = cls.run_console(_fixture())

    # ---- invariant 4: tab order and default ------------------------------

    def test_the_console_opens_on_topics_and_research(self) -> None:
        self.assertEqual(self.out["activeView"], ["topics"])
        self.assertEqual(self.out["visiblePanels"], ["panel-topics"])

    def test_a_stored_preference_does_not_move_the_opening_tab(self) -> None:
        out = self.run_console(_fixture(ui={"analytics": {"range": "7", "device": "mobile", "metric": "ctr"}}))

        self.assertEqual(out["activeView"], ["topics"])
        self.assertIn("range=7", out["requests"][-1])
        self.assertIn("device=mobile", out["requests"][-1])

    # ---- invariant 1: the reader ----------------------------------------

    def test_the_read_tab_shows_rendered_html_not_markdown(self) -> None:
        read = self.out["read"]

        self.assertIn("<table", read)
        self.assertIn("<strong>12,000–18,000</strong>", read)
        self.assertNotIn("**", read)
        self.assertNotIn("| City |", read)
        self.assertNotIn("slug:", read)

    def test_review_scaffolding_is_collapsed_below_the_article(self) -> None:
        read = self.out["read"]

        self.assertIn('<details class="review-notes">', read)
        self.assertIn("Review notes — not part of the article", read)
        self.assertLess(read.index('class="article-sheet"'), read.index('class="review-notes"'))
        prose = read[read.index('class="article-sheet"'):read.index('class="review-notes"')]
        self.assertNotIn("Decision bullets", prose)

    def test_the_editor_opens_on_the_markdown_source_with_a_preview(self) -> None:
        editor = self.out["editor"]

        self.assertIn("<textarea id=\"editor-input\"", editor)
        self.assertIn("# Battery replacement, city by city", editor)
        self.assertIn('id="editor-preview"', editor)
        self.assertIn('data-editor="save"', editor)
        self.assertIn('data-editor="cancel"', editor)
        self.assertIn("does not approve anything", editor)

    def test_the_reader_offers_edit_download_and_print(self) -> None:
        for control in ('data-reader="edit"', 'data-reader="download"', 'data-reader="print"'):
            self.assertIn(control, self.out["read"])

    # ---- invariant 6: every long list paginates --------------------------

    def test_twenty_eight_proposals_render_one_page_of_ten(self) -> None:
        self.assertEqual(self.out["proposals"].count('class="card"'), 10)
        self.assertIn("1–10 of 28 candidates", self.out["topicsPager"])
        self.assertIn("28 candidates", self.out["topicsCount"])

    def test_thirty_three_blogs_render_one_page_of_ten(self) -> None:
        self.assertEqual(self.out["blogs"].count('class="card"'), 10)
        self.assertIn("1–10 of 33 articles", self.out["blogsPager"])

    def test_forty_query_rows_render_one_page_of_twenty_five(self) -> None:
        self.assertEqual(self.out["queriesBody"].count("<tr>"), 25)
        self.assertIn("1–25 of 40 queries", self.out["queriesPager"])

    def test_fourteen_opportunities_render_one_page_of_ten(self) -> None:
        self.assertEqual(self.out["opportunities"].count('class="opportunity'), 10)

    def test_no_list_renders_unbounded(self) -> None:
        for name in ("proposals", "blogs", "opportunities"):
            with self.subTest(list=name):
                self.assertLessEqual(self.out[name].count('role="listitem"'), 25)

    # ---- invariant 5: stored sort, filter and paging ---------------------

    def test_a_stored_page_and_size_survive_the_reload(self) -> None:
        out = self.run_console(_fixture(ui={"topics": {"page": 3, "size": 10, "search": "", "filter": "all"}}))

        self.assertIn("21–28 of 28 candidates", out["topicsPager"])

    def test_a_stored_filter_survives_the_reload(self) -> None:
        out = self.run_console(_fixture(ui={"topics": {"page": 1, "size": 10, "search": "", "filter": "revising"}}))

        self.assertIn("of 28", out["topicsCount"])
        self.assertIn('data-topics-filter="revising" aria-pressed="true"', out["topicsFilter"])

    def test_a_stored_search_survives_the_reload(self) -> None:
        out = self.run_console(_fixture(ui={"topics": {"page": 1, "size": 10, "search": "topic 7", "filter": "all"}}))

        self.assertIn("Candidate topic 7", out["proposals"])
        self.assertNotIn("Candidate topic 8<", out["proposals"])

    def test_a_stored_table_sort_survives_the_reload(self) -> None:
        out = self.run_console(
            _fixture(ui={"queries": {"page": 1, "size": 25, "sort": "position", "dir": "asc"}})
        )

        self.assertIn("<tr>", out["queriesBody"])
        self.assertIn("1–25 of 40 queries", out["queriesPager"])

    # ---- the analytics screen -------------------------------------------

    def test_five_stat_tiles_render_with_deltas(self) -> None:
        tiles = self.out["tiles"]

        self.assertEqual(tiles.count('class="tile"'), 5)
        for label in ("Impressions", "Clicks", "CTR", "Average position", "Indexed pages"):
            self.assertIn(label, tiles)
        self.assertIn("5,400", tiles)
        self.assertIn("vs previous window", tiles)

    def test_a_missing_figure_reads_not_yet_and_never_zero(self) -> None:
        tiles = self.out["tiles"]

        self.assertIn("not yet", tiles)
        self.assertIn('class="tile-figure absent"', tiles)

    def test_a_position_improvement_reads_as_an_improvement(self) -> None:
        # Average position falling is good news, so -1.7 must not render as a loss.
        self.assertIn('<span class="delta up">-1.7 vs previous window</span>', self.out["tiles"])
        self.assertIn('<span class="delta down">-9 vs previous window</span>', self.out["tiles"])

    def test_the_chart_draws_bars_with_a_tooltip_target_per_day(self) -> None:
        chart = self.out["chart"]

        self.assertIn("<svg", chart)
        self.assertEqual(chart.count('class="bar"'), 14)
        self.assertEqual(chart.count('class="hit" tabindex="0"'), 14)
        self.assertIn("2026-08-01: 12 impressions", chart)
        self.assertIn('class="line"', chart, "clicks ride alongside impressions")

    def test_the_chart_switches_to_a_line_when_days_lose_their_own_mark(self) -> None:
        fixture = _fixture()
        fixture["state"]["analytics"]["search"]["series"] = [
            {"date": f"2026-0{1 + day // 28}-{1 + day % 28:02d}", "impressions": day, "clicks": 1, "ctr": 1.0, "position": 12.0}
            for day in range(300)
        ]
        out = self.run_console(fixture)

        self.assertNotIn('class="bar"', out["chart"])
        self.assertIn('class="line"', out["chart"])

    def test_the_opportunity_row_carries_the_button_that_queues_it(self) -> None:
        panel = self.out["opportunities"]

        self.assertIn('data-queue="battery query 1"', panel)
        self.assertIn("Research this", panel)
        self.assertIn("Queued ✓", panel, "an already-queued subject says so")
        self.assertIn("is-queued", panel)

    def test_the_footer_names_the_collection_start_and_the_reporting_delay(self) -> None:
        footnote = self.out["footnote"]

        self.assertIn("Collection started 2026-08-04", footnote)
        self.assertIn("2 days later", footnote)
        self.assertIn("2026-08-01 to 2026-08-14", footnote)

    def test_ga4_still_renders_not_connected_alongside(self) -> None:
        self.assertIn("Google Analytics is not connected", self.out["ga4"])
        self.assertIn("GA4_PROPERTY_ID", self.out["ga4"])

    def test_tables_right_align_their_numerals(self) -> None:
        self.assertIn('<td class="n">', self.out["queriesBody"])
        self.assertIn('<td class="n">', self.out["pagesBody"])

    # ---- empty states -----------------------------------------------------

    def test_an_unmeasured_credit_balance_is_neutral_not_an_error(self) -> None:
        self.assertFalse(self.out["creditMeterError"], "an unmeasured balance must not read as a failure")
        self.assertIn("no credit balance has been measured", self.out["creditMeter"])

    def test_an_empty_console_states_the_next_action_rather_than_a_failure(self) -> None:
        out = self.run_console(_fixture(proposals=0, blogs=0, queries=0))

        self.assertIn("No candidates yet", out["proposals"])
        self.assertIn("Enter a subject", out["proposals"])
        self.assertIn("No article yet", out["blogs"])
        self.assertIn("Go to Topics &amp; Research", out["blogs"])
        self.assertNotIn("error", out["proposals"].lower())

    # ---- the archived shelf ----------------------------------------------

    def test_the_archived_shelf_groups_candidates_under_their_subject(self) -> None:
        """Six candidates from one subject are one decision already made.

        Grouped, the shelf reads as "these lost to that"; ungrouped it reads as a
        second undecided pile, which is the thing the sweep exists to end.
        """
        shelved = [_archived(1, 7), _archived(2, 7), _archived(3, 9)]
        out = self.run_console(_fixture(archived=shelved))

        # One heading per subject, not one per card.
        self.assertEqual(out["archived"].count('<h3 class="rule"'), 2)
        self.assertEqual(out["archived"].count("<article"), 3)
        for index in (1, 2, 3):
            self.assertIn(f"Archived candidate {index}", out["archived"])
        self.assertIn("archived subject 7", out["archived"])
        self.assertIn("archived subject 9", out["archived"])
        self.assertIn("3 archived topics", out["archivedCount"])

    def test_every_archived_card_offers_restore_and_says_it_is_not_rejected(self) -> None:
        out = self.run_console(_fixture(archived=[_archived(1, 7)]))

        self.assertIn("data-restore=", out["archived"])
        self.assertIn("data-reject-open=", out["archived"])
        self.assertNotIn("data-approve=", out["archived"])

    def test_an_empty_shelf_explains_what_puts_things_there(self) -> None:
        out = self.run_console(_fixture(archived=[]))

        self.assertIn("Nothing is archived", out["archived"])
        self.assertIn("not rejected", out["archived"])

    def test_the_radar_line_says_when_it_last_ran_or_that_it_has_not(self) -> None:
        never = self.run_console(_fixture())
        self.assertIn("has not run yet", never["radarStatus"])

        ran = self.run_console(_fixture(radar={
            "started_at": "2026-08-27T01:30:00Z", "mode": "due", "status": "completed",
            "message": "4 candidate(s) proposed from 2 subject(s); 9 credits used.",
        }))
        self.assertIn("2026-08-27T01:30:00Z", ran["radarStatus"])
        self.assertIn("9 credits used", ran["radarStatus"])

    def test_the_sweep_names_the_beats_it_covered(self) -> None:
        """"Nothing new today" and "that beat was never searched" look identical
        in a candidate list, and only one is a reason to change a query."""
        out = self.run_console(_fixture(radar={
            "started_at": "2026-08-27T01:30:00Z", "mode": "due", "status": "completed",
            "message": "4 candidate(s) proposed from 2 subject(s); 9 credits used.",
            "beats": ["ev-industry", "policy", "battery-tech", "market", "competitors"],
            "empty_beats": ["battery-tech"],
        }))

        for name in ("EV industry", "Government policy", "Market trends", "Competitors"):
            self.assertIn(name, out["radarStatus"], f"the {name} beat is not named")
        self.assertIn("nothing new from Battery technology", out["radarStatus"])

    def test_a_sweep_with_no_recorded_beats_claims_nothing(self) -> None:
        """Runs from before beats were recorded must not read as full coverage."""
        out = self.run_console(_fixture(radar={
            "started_at": "2026-08-27T01:30:00Z", "mode": "due", "status": "completed",
            "message": "4 candidate(s) proposed.",
        }))

        self.assertIn("2026-08-27T01:30:00Z", out["radarStatus"])
        self.assertNotIn("Beats swept", out["radarStatus"])

    def test_the_console_makes_no_request_to_another_host(self) -> None:
        for request in self.out["requests"]:
            self.assertTrue(request.startswith("/"), f"{request} leaves this host")


if __name__ == "__main__":
    unittest.main()
