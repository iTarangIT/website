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


def _social(articles: int = 2, *, drafts: bool = True, queued: bool = False) -> dict:
    def draft(task_id: str, platform: str) -> dict:
        return {
            "platform": platform,
            "body": f"{platform} copy for {task_id}",
            "link": f"https://www.itarang.com/blog/article-{task_id}",
            "thread": ["first post", "second post"] if platform == "x" else [],
            "image_alt": "A depot at dusk",
            "producer": "writer",
            "status": "queued" if queued else "draft",
            "buffer_post_id": "d" * 24 if queued else "",
            "scheduled_at": "2026-09-01T10:00:00Z" if queued else "",
            "sent_by": "it@itarang.com" if queued else "",
            "error": "",
        }

    return {
        "connected": True,
        "counts": {"draft": 3, "queued": 0, "failed": 0},
        "articles": [
            {
                "task_id": f"TASK-{800 + index}",
                "title": f"Published article {index}",
                "slug": f"published-article-{index}",
                "url": f"https://www.itarang.com/blog/published-article-{index}",
                "drafts": [draft(f"TASK-{800 + index}", platform)
                           for platform in ("linkedin", "x", "instagram")] if drafts else [],
            }
            for index in range(articles)
        ],
    }


def _audience(status: str = "ready") -> dict:
    return {
        "status": status,
        "message": "" if status == "ready" else "Google Analytics is not connected yet",
        "required_variables": ["GA4_PROPERTY_ID"],
        "range_days": 28,
        "device": "all",
        "traffic_sources": [
            {"source": "Google", "sessions": 60, "active_users": 55, "share": 54.5, "examples": ["google"]},
            {"source": "LinkedIn", "sessions": 40, "active_users": 37, "share": 36.4,
             "examples": ["lnkd.in", "linkedin"]},
            {"source": "Direct", "sessions": 10, "active_users": 9, "share": 9.1, "examples": ["(direct)"]},
        ],
        "previous_traffic_sources": [
            {"source": "Google", "sessions": 80, "active_users": 70, "share": 72.7, "examples": ["google"]},
            {"source": "LinkedIn", "sessions": 30, "active_users": 28, "share": 27.3, "examples": ["lnkd.in"]},
        ],
        "devices": [{"device": "mobile", "sessions": 70, "engagement_rate": 0.62}],
        "browsers": [{"browser": "Chrome", "operating_system": "Android", "sessions": 65}],
        "landing_pages": [
            {"page": "/blog/emi", "sessions": 30, "engagement_rate": 0.58, "bounces": 0.42}
        ],
    }


def _geography(status: str = "ready") -> dict:
    """One window of geography, shaped the way `ga4_geography` returns it.

    India carries the work and the Netherlands is the country nobody planned
    for -- the case the drill-down and the unexpected-geography rule were both
    built for, so the fixture is that case rather than a neutral one.
    """
    return {
        "status": status,
        "message": "" if status == "ready" else "Google Analytics is not connected yet",
        "required_variables": ["GA4_PROPERTY_ID"],
        "range_days": 28,
        "device": "all",
        "has_previous": True,
        "countries": [
            {
                "country": "India", "sessions": 90, "active_users": 80,
                "engagement_rate": 0.31, "share": 68.7, "expected": True,
                "previous_sessions": 70, "delta_sessions": 20, "tree_sessions": 90,
                "regions": [
                    {"region": "Haryana", "sessions": 60, "engagement_rate": 0.34, "share": 66.7,
                     "cities": [{"city": "Gurugram", "sessions": 40, "engagement_rate": 0.36, "share": 66.7},
                                {"city": "Faridabad", "sessions": 20, "engagement_rate": 0.30, "share": 33.3}]},
                    {"region": "Maharashtra", "sessions": 30, "engagement_rate": 0.25, "share": 33.3,
                     "cities": [{"city": "Pune", "sessions": 30, "engagement_rate": 0.25, "share": 100.0}]},
                ],
            },
            {
                "country": "Netherlands", "sessions": 41, "active_users": 39,
                "engagement_rate": 0.049, "share": 31.3, "expected": False,
                "previous_sessions": None, "delta_sessions": None, "tree_sessions": 41,
                "regions": [
                    {"region": "Not reported", "sessions": 41, "engagement_rate": 0.049, "share": 100.0,
                     "cities": [{"city": "Not reported", "sessions": 41,
                                 "engagement_rate": 0.049, "share": 100.0}]},
                ],
            },
        ],
        "country_sources": [
            {"country": "India", "sessions": 90, "channels": [
                {"source": "Google", "sessions": 60, "share": 66.7, "engagement_rate": 0.34},
                {"source": "LinkedIn", "sessions": 30, "share": 33.3, "engagement_rate": 0.41}]},
            {"country": "Netherlands", "sessions": 41, "channels": [
                {"source": "Direct", "sessions": 41, "share": 100.0, "engagement_rate": 0.049}]},
        ],
        "country_channels": [
            {"country": "India", "sessions": 90, "channels": [
                {"channel": "Organic Search", "sessions": 60, "share": 66.7, "engagement_rate": 0.34},
                {"channel": "Organic Social", "sessions": 30, "share": 33.3, "engagement_rate": 0.41}]},
            {"country": "Netherlands", "sessions": 41, "channels": [
                {"channel": "Referral", "sessions": 41, "share": 100.0, "engagement_rate": 0.049}]},
        ],
    }


def _insight(**overrides: object) -> dict:
    payload = {
        "kind": "unexpected_geography", "panel": "places", "subject": "Netherlands",
        "severity": "high",
        "headline": "Netherlands sent traffic we did not plan for",
        "what": "Netherlands sent 41 sessions, 31% of everything recorded in this window.",
        "why": "They engage at 4.9% against 20.7% across the site.",
        "action": "Open the country in GA4 and check the landing pages behind it.",
        "evidence": ["Netherlands: 41 sessions, new this window."],
        "confidence": "measured", "sample": 41, "caveat": "",
    }
    payload.update(overrides)
    return payload


def _ga4(**overrides: object) -> dict:
    """A connected property, as `ga4_technical_summary` returns it.

    The engagement rate is deliberately 0.207 — the exact value www.itarang.com
    reported when this panel was still printing raw ratios on screen.
    """
    metrics = {
        "active_users": 24, "sessions": 29, "screen_page_views": 46,
        "engagement_rate": 0.207, "new_users": 18, "engaged_sessions": 6,
        "average_session_duration": 72.4, "screen_page_views_per_session": 1.586,
        "bounce_rate": 0.793, "sessions_per_user": 1.208, "returning_users": 6,
    }
    payload = {
        "status": "ready", "message": "", "required_variables": ["GA4_PROPERTY_ID"],
        "range_days": 28, "device": "all",
        "metrics": metrics,
        "previous": metrics,
        "deltas": {"active_users": 4, "engagement_rate": 0.05,
                   "average_session_duration": 12.0, "engaged_sessions": 2,
                   "screen_page_views_per_session": 0.21},
        "pages": [{"page": "/how-it-works", "screen_page_views": 18,
                   "sessions": 12, "engagement_rate": 0.41, "active_users": 9}],
        "collection_start": "2026-08-04",
    }
    payload.update(overrides)
    return payload


def _events(**overrides: object) -> dict:
    payload = {
        "status": "ready", "message": "", "required_variables": ["GA4_PROPERTY_ID"],
        "range_days": 28, "device": "all",
        "events": [{"event": "page_view", "count": 46, "users": 24, "intent": False}],
        "funnel": [
            {"step": "Opened the calculator", "event": "calculator_start",
             "count": None, "instrumented": False, "retention": None},
            {"step": "Asked for an OTP", "event": "otp_requested",
             "count": None, "instrumented": False, "retention": None},
            {"step": "Verified the number", "event": "otp_verified",
             "count": None, "instrumented": False, "retention": None},
            {"step": "Became a lead", "event": "generate_lead",
             "count": None, "instrumented": False, "retention": None},
        ],
        "key_events": None, "session_key_event_rate": None,
        "key_event_message": "", "instrumented": False,
        "scroll_depth": [], "scroll_message": "",
    }
    payload.update(overrides)
    return payload


def _fixture(*, proposals: int = 28, blogs: int = 33, queries: int = 40, ui: dict | None = None,
             archived: list | None = None, radar: dict | None = None,
             social: dict | None = None, audience: dict | None = None,
             ga4: dict | None = None, ga4_events: dict | None = None,
             geography: dict | None = None, insights: list | None = None,
             summary: dict | None = None, pages: list | None = None) -> dict:
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
            "social": _social() if social is None else social,
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
                },
                "search_console": {"status": "collecting"},
                "ga4": {"status": "not_connected", "message": "Google Analytics is not connected yet",
                        "required_variables": ["GA4_PROPERTY_ID"]} if ga4 is None else ga4,
                "ga4_audience": _audience() if audience is None else audience,
                "ga4_geography": _geography() if geography is None else geography,
                "ga4_events": _events() if ga4_events is None else ga4_events,
                "pages": [
                    {"page": "/blog/emi", "screen_page_views": 300, "sessions": 250,
                     "active_users": 210, "engagement_rate": 0.19},
                    {"page": "/products", "screen_page_views": 60, "sessions": 50,
                     "active_users": 45, "engagement_rate": 0.62},
                ] if pages is None else pages,
                "insights": [_insight()] if insights is None else insights,
                "summary": {
                    "what": ["341 sessions from 268 visitors over 28 days."],
                    "why": ["Netherlands sent traffic we did not plan for."],
                    "actions": [{"action": "Open the country in GA4.",
                                 "kind": "unexpected_geography", "panel": "places"}],
                    "caveats": [],
                } if summary is None else summary,
                "campaigns": {
                    "rows": [{"channel": "LinkedIn", "posts_sent": 2, "sessions": 40,
                              "active_users": 37, "engagement_rate": 0.41,
                              "views_per_session": 3.1, "impressions": None,
                              "clicks": None, "ctr": None, "engagements": None}],
                    "measured": "Google Analytics, on arrival",
                    "unavailable": ["impressions", "clicks", "ctr", "engagements"],
                    "unavailable_reason": "LinkedIn needs an app with organization access "
                                          "and a LINKEDIN_ACCESS_TOKEN.",
                },
                "posts": {
                    "posts": [
                        {"slug": "emi", "title": "What an EMI actually costs", "url": "https://itarang.com/blog/emi",
                         "views": 230, "sessions": 180, "engagement_rate": 0.62,
                         "impressions": 90, "clicks": 4, "ctr": 4.4, "position": 15.5,
                         "sources": ["search_console", "ga4"]},
                        {"slug": "only-shared", "title": "Shared, never found", "url": "",
                         "views": 95, "sessions": 80, "engagement_rate": 0.5,
                         "impressions": None, "clicks": None, "ctr": None, "position": None,
                         "sources": ["ga4"]},
                    ],
                    "measured": 2,
                    "totals": {"views": 325, "clicks": 4, "impressions": 90},
                },
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

    def test_no_list_renders_unbounded(self) -> None:
        for name in ("proposals", "blogs"):
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

    def test_a_rotating_vertical_is_named_rather_than_shown_as_a_slug(self) -> None:
        """The roster beats are new; an unnamed one would print `inverter-batteries`
        at the reader, which is true but is not a beat name."""
        out = self.run_console(_fixture(radar={
            "started_at": "2026-09-02T01:30:00Z", "mode": "due", "status": "completed",
            "message": "2 candidate(s) proposed from 1 subject(s); 12 credits used.",
            "beats": ["ev-industry", "policy", "competitors", "solar", "inverter-batteries"],
            "empty_beats": ["inverter-batteries"],
        }))

        for name in ("Solar", "Inverter batteries"):
            self.assertIn(name, out["radarStatus"], f"the {name} beat is not named")
        self.assertIn("nothing new from Inverter batteries", out["radarStatus"])

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


class SocialTabRenders(unittest.TestCase):
    """The Social tab, executed rather than grepped.

    A renderer that ships beside its markup and never paints is the failure this
    file exists to catch, so these assertions are on rendered HTML.
    """

    maxDiff = None

    @classmethod
    def render(cls, fixture: dict) -> dict:
        return ConsoleRenders.run_console(fixture)

    def test_each_published_article_becomes_a_card_with_three_drafts(self):
        report = self.render(_fixture())
        html = report["social"]

        self.assertIn("Published article 0", html)
        for label in ("LinkedIn", "X", "Instagram"):
            self.assertIn(f">{label}</span>", html)
        self.assertEqual(html.count('data-draft="'), 6, "two articles, three platforms each")

    def test_a_thread_is_edited_as_one_box_with_a_separator(self):
        """One box per item would be a nicer form and a worse edit: reordering is
        the commonest change, and moving a line beats dragging boxes."""
        html = self.render(_fixture())["social"]
        self.assertIn("first post\n---\nsecond post", html)
        self.assertIn("Separate thread posts with a line containing only ---", html)

    def test_every_draft_carries_a_live_character_count_against_its_own_limit(self):
        html = self.render(_fixture())["social"]
        self.assertIn("/ 3,000", html, "LinkedIn's limit")
        self.assertIn("/ 280", html, "X's limit")
        self.assertIn("/ 2,200", html, "Instagram's limit")

    def test_the_send_button_appears_only_after_a_plan_is_prepared(self):
        html = self.render(_fixture())["social"]
        self.assertIn("data-social-prepare=", html)
        self.assertNotIn("data-social-send=", html)

    def test_a_queued_post_is_read_only_and_says_where_to_edit_it(self):
        html = self.render(_fixture(social=_social(articles=1, queued=True)))["social"]
        self.assertIn("queued in Buffer", html)
        self.assertIn("Edit it in Buffer, not here.", html)
        self.assertNotIn("data-draft-body=", html)
        self.assertNotIn("data-social-prepare=", html, "nothing is left to send")

    def test_an_article_with_no_copy_offers_to_write_it_and_nothing_else(self):
        html = self.render(_fixture(social=_social(articles=1, drafts=False)))["social"]
        self.assertIn("no copy written yet", html)
        self.assertIn("data-social-generate=", html)
        self.assertNotIn("data-social-prepare=", html)

    def test_no_live_article_is_an_empty_state_that_explains_the_gate(self):
        report = self.render(_fixture(social={"connected": True, "counts": {}, "articles": []}))
        html = report["social"]
        self.assertIn("No article is live yet", html)
        self.assertIn("Gate 2", html)

    def test_the_tab_says_when_buffer_is_not_connected(self):
        report = self.render(_fixture(social={"connected": False, "counts": {}, "articles": []}))
        self.assertIn("BUFFER_ACCESS_TOKEN", report["bufferState"])

    def test_the_filter_chips_count_what_is_in_each_state(self):
        html = self.render(_fixture())["socialFilter"]
        for label in ("All", "No copy yet", "Ready to send", "Queued", "Refused"):
            self.assertIn(f">{label}<", html)


@unittest.skipUnless(NODE, "node is required to execute the console script")
class AudiencePanelsRender(unittest.TestCase):
    """Traffic sources, locations, devices and landing pages, executed."""

    maxDiff = None

    @classmethod
    def render(cls, fixture: dict) -> dict:
        return ConsoleRenders.run_console(fixture)

    def test_traffic_sources_render_as_named_channels_not_raw_referrers(self):
        """"LinkedIn sent 40" is the answer; "lnkd.in 22, linkedin.com 18" is not."""
        html = self.render(_fixture())["sources"]
        self.assertIn(">LinkedIn</td>", html)
        self.assertIn("36.4%", html)
        self.assertIn("lnkd.in, linkedin", html, "what matched must stay visible")

    def test_a_share_is_drawn_as_a_bar_and_still_printed_as_a_number(self):
        html = self.render(_fixture())["sources"]
        self.assertIn('class="share-bar"', html)
        self.assertIn("width:54.5%", html)
        self.assertIn("54.5%", html)

    def test_a_country_opens_onto_the_regions_and_cities_inside_it(self):
        """Three levels, and the lower two behind a disclosure.

        A flat city list cannot answer "where in India", and a reader who does
        not have that question should not have to scroll past the answer.
        """
        html = self.render(_fixture())["places"]
        self.assertIn("India", html)
        self.assertIn(">Haryana</td>", html)
        self.assertIn(">Gurugram</td>", html)
        self.assertIn("Share of country", html)

    def test_a_country_outside_our_markets_is_marked_on_its_own_row(self):
        html = self.render(_fixture())["places"]
        self.assertIn("outside our markets", html)
        # It has no previous window, which is what makes it new rather than grown.
        self.assertIn("new this window", html)

    def test_the_two_cross_tabs_are_rendered_apart_and_say_why(self):
        """Merging them would hide the finding.

        A country that is Direct under our naming and Referral under Google's
        arrived without a tag we set, and only the two side by side show it.
        """
        html = self.render(_fixture())["geoCross"]
        self.assertIn("By the channel that sent the session", html)
        self.assertIn("By Google&#39;s own channel group", html)
        self.assertIn(">Organic Search</td>", html)
        self.assertIn("arrived without a tag we set", html)

    def test_a_panel_carries_the_finding_that_belongs_to_it(self):
        """Every chart leads to an action, in the place the chart is."""
        html = self.render(_fixture())["places"]
        self.assertIn("Netherlands sent traffic we did not plan for", html)
        self.assertIn("Open the country in GA4", html)

    def test_a_watched_finding_shows_its_caveat_where_the_action_would_be(self):
        """A recommendation and a thing to watch must not look alike."""
        watched = _insight(action="", confidence="too_small", sample=12,
                           caveat="A sample of 12 is too small to act on.")
        html = self.render(_fixture(insights=[watched]))["places"]
        self.assertIn("too small to act on", html)
        self.assertIn('class="insight tone-high watch"', html)

    def test_the_summary_answers_what_then_why_then_what_to_do(self):
        html = self.render(_fixture())["insights"]
        self.assertIn("What happened", html)
        self.assertIn("Why", html)
        self.assertIn("What to do", html)
        # The action names the panel it was read from rather than restating it.
        self.assertIn("Where visitors are", html)

    def test_page_performance_reports_views_sessions_and_visitors(self):
        html = self.render(_fixture(ga4=_ga4()))["pagesPerformance"]
        self.assertIn(">/products</td>", html)
        self.assertIn(">300<", html)
        self.assertIn("62.0%", html)

    def test_a_campaign_column_nobody_can_measure_says_so_rather_than_showing_zero(self):
        """A zero in this column would read as a post that reached nobody."""
        html = self.render(_fixture())["campaign"]
        self.assertIn(">LinkedIn</td>", html)
        self.assertIn("not measured", html)
        self.assertNotIn(">0<", html)
        self.assertIn("LINKEDIN_ACCESS_TOKEN", html)

    def test_devices_render_with_their_browsers(self):
        html = self.render(_fixture())["devices"]
        self.assertIn(">mobile</td>", html)
        self.assertIn(">Chrome</td>", html)
        self.assertIn("62.0%", html, "engagement rate reads as a percentage")

    def test_landing_pages_say_they_are_the_entry_point_and_not_a_journey(self):
        """Claiming a full user journey from a landing-page report would be a lie."""
        html = self.render(_fixture())["journey"]
        self.assertIn("/blog/emi", html)
        self.assertIn("not a full path", html)

    def test_every_panel_reports_the_same_missing_tag_rather_than_several_stories(self):
        report = self.render(_fixture(
            audience=_audience(status="not_connected"),
            geography=_geography(status="not_connected"),
        ))
        for key in ("sources", "places", "geoCross", "devices", "journey"):
            self.assertIn("GA4_PROPERTY_ID", report[key], key)


@unittest.skipUnless(NODE, "node is required to execute the console script")
class PerPostTableRenders(unittest.TestCase):
    maxDiff = None

    def test_each_article_is_a_row_carrying_views_beside_the_search_numbers(self):
        report = ConsoleRenders.run_console(_fixture())
        body = report["postsBody"]
        self.assertIn("What an EMI actually costs", body)
        self.assertIn(">230<", body, "views")
        self.assertIn(">90<", body, "impressions")

    def test_an_article_only_one_system_saw_says_which_one(self):
        body = ConsoleRenders.run_console(_fixture())["postsBody"]
        self.assertIn("analytics only", body)

    def test_an_unmeasured_column_renders_as_a_dash_and_never_as_zero(self):
        body = ConsoleRenders.run_console(_fixture())["postsBody"]
        row = body.split("Shared, never found", 1)[1]
        self.assertIn("—", row)
        self.assertNotIn(">0<", row)


class Ga4TieringRenders(unittest.TestCase):
    """The tiered Google Analytics panel, executed rather than grepped.

    The reported defect was not a missing feature: it was four tiles printing a
    number nobody could read. So the first test here is the number.
    """

    maxDiff = None

    @classmethod
    def render(cls, fixture: dict) -> dict:
        return ConsoleRenders.run_console(fixture)

    def test_an_engagement_rate_reads_as_a_percentage_not_a_ratio(self) -> None:
        """Google Analytics reports engagement as a ratio between 0 and 1.

        Printed through the default branch of `figure` it rendered as "0.207",
        which is what www.itarang.com's console showed. It is a percentage, and
        a CMO reading a percentage should not have to move a decimal point.
        """
        html = self.render(_fixture(ga4=_ga4()))["ga4"]

        self.assertIn("20.7%", html)
        self.assertNotIn("0.207", html)

    def test_a_rate_delta_is_percentage_points_not_a_bare_decimal(self) -> None:
        """0.05 between two ratios is five points, not five percent."""
        html = self.render(_fixture(ga4=_ga4()))["ga4"]

        self.assertIn("+5.0 pts", html)

    def test_engagement_time_reads_in_minutes_and_seconds(self) -> None:
        html = self.render(_fixture(ga4=_ga4()))["ga4"]

        self.assertIn("1m 12s", html, "72.4 seconds is a minute and twelve")

    def test_the_strip_leads_with_quality_and_puts_volume_one_click_down(self) -> None:
        """Sessions and page views say how much arrived, not whether it was the
        right traffic. They stay reachable, but they are not the glance."""
        html = self.render(_fixture(ga4=_ga4()))["ga4"]
        strip, drill = html.split("<details", 1)

        for label in ("Active users", "Engaged sessions", "Engagement rate",
                      "Avg engagement time", "Pages per session", "Key events"):
            self.assertIn(label, strip, f"{label} belongs in the executive strip")
        for label in ("Sessions", "Page views", "Sessions per user", "Bounce rate"):
            self.assertIn(label, drill, f"{label} belongs in the drill-down")
        self.assertEqual(strip.count('class="tile"'), 6)

    def test_a_rate_is_shown_with_the_sample_it_was_computed_over(self) -> None:
        """20.7% of 29 sessions is six sessions. A percentage that hides a
        sample that small invites a trend reading it cannot support."""
        html = self.render(_fixture(ga4=_ga4()))["ga4"]

        self.assertIn("of 29 sessions", html)

    def test_new_and_returning_are_separated_rather_than_summed(self) -> None:
        html = self.render(_fixture(ga4=_ga4()))["ga4"]

        self.assertIn("class=\"split-bar\"", html)
        self.assertIn("New", html)
        self.assertIn("Returning", html)

    def test_an_uninstrumented_conversion_says_so_instead_of_showing_zero(self) -> None:
        """"Nobody converted" and "nothing reports a conversion" are opposite
        findings, and only the first is a marketing problem."""
        panel = self.render(_fixture(ga4=_ga4()))["ga4Events"]

        self.assertIn("not instrumented", panel)
        self.assertNotIn(">0<", panel)
        self.assertIn("Opened the calculator", panel)
        self.assertIn("Became a lead", panel)

    def test_a_measured_funnel_shows_where_it_loses_people(self) -> None:
        events = _events(
            instrumented=True,
            events=[{"event": "generate_lead", "count": 27, "users": 25, "intent": True}],
            funnel=[
                {"step": "Opened the calculator", "event": "calculator_start",
                 "count": 100, "instrumented": True, "retention": None},
                {"step": "Asked for an OTP", "event": "otp_requested",
                 "count": 40, "instrumented": True, "retention": 40.0},
                {"step": "Verified the number", "event": "otp_verified",
                 "count": 30, "instrumented": True, "retention": 75.0},
                {"step": "Became a lead", "event": "generate_lead",
                 "count": 27, "instrumented": True, "retention": 90.0},
            ],
            key_events=27,
            session_key_event_rate=0.31,
        )
        out = self.render(_fixture(ga4=_ga4(), ga4_events=events))

        self.assertIn("40.0% of the step above", out["ga4Events"])
        self.assertNotIn("not instrumented", out["ga4Events"])
        # The key-event tile is the one number on the tab tied to revenue intent.
        self.assertIn("Key events", out["ga4"])
        self.assertIn("31.0% of sessions", out["ga4"])

    def test_reading_depth_separates_a_page_opened_from_a_page_read(self) -> None:
        events = _events(scroll_depth=[
            {"page": "/blog/emi", "views": 40, "reached_end": 10, "share": 25.0},
            {"page": "/products", "views": 25, "reached_end": 0, "share": 0.0},
        ])
        html = self.render(_fixture(ga4=_ga4(), ga4_events=events))["ga4Events"]

        self.assertIn("How far people read", html)
        self.assertIn("/blog/emi", html)
        self.assertIn("25.0%", html)

    def test_a_channel_is_weighed_by_engagement_and_not_only_by_volume(self) -> None:
        audience = _audience()
        audience["traffic_sources"][1].update(
            {"engagement_rate": 0.11, "views_per_session": 1.02})
        html = self.render(_fixture(audience=audience))["sources"]

        self.assertIn("11.0%", html, "a channel that sends volume and no attention")
        self.assertIn("1.02", html)

    def test_first_touch_sits_behind_a_disclosure_beside_session_source(self) -> None:
        audience = _audience()
        audience["first_user_sources"] = [
            {"source": "LinkedIn", "sessions": 22, "active_users": 20, "share": 40.0,
             "engagement_rate": 0.5, "views_per_session": 2.0, "examples": ["lnkd.in"]},
        ]
        html = self.render(_fixture(audience=audience))["sources"]

        self.assertIn("Which channel found them first", html)

    def test_every_new_panel_names_the_missing_variable_when_disconnected(self) -> None:
        """Three states, not two.

        A property that is *not connected* must name the variable that would
        connect it. A property that is connected and has simply recorded no
        conversion is a different answer, and it is covered above -- conflating
        them would send someone to check an environment variable that is fine.
        """
        disconnected = _events(status="not_connected",
                               message="Google Analytics is not connected yet")
        out = self.render(_fixture(ga4_events=disconnected))

        for panel in ("ga4", "ga4Events"):
            self.assertIn("GA4_PROPERTY_ID", out[panel], panel)
