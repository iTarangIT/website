"""Console-level guarantees for the topic flow.

Replaces test_content_workflow.py, which asserted the superseded rule that
submitting a topic *is* the writing instruction and that the topic screen carries no
approve or decline control. Apoorv reversed both: a rough subject is now researched
into candidates, and Sanchit approves, suggests changes or rejects each one.

Covers invariants 4 (exactly three tabs), 6 (reads come from the database or the
board), 7 (no external request at page load, no service-role key) and 8 (preview mode
forbids every writable route).
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

import dashboard_server  # noqa: F401 — initializes the profile import path
import ceo_actions
import ceo_console
from ceo_markup import MARKUP
from ceo_page import render_page
from ceo_script import SCRIPT
from ceo_style import CSS
from cmo_runtime import topic_proposals
from cmo_runtime.console_db import ConsoleDB


class ThreeTabsAndNoFourth(unittest.TestCase):
    """Invariant 4."""

    def test_exactly_three_primary_tabs_render(self) -> None:
        tabs = re.findall(r'data-view="([a-z-]+)"', MARKUP)
        self.assertEqual(tabs, ["analytics", "topics", "blogs"])

    def test_every_tab_has_a_panel_and_every_panel_has_a_tab(self) -> None:
        tabs = set(re.findall(r'data-view="([a-z-]+)"', MARKUP))
        panels = set(re.findall(r'id="panel-([a-z-]+)"', MARKUP))
        self.assertEqual(tabs, panels)

    def test_trending_is_no_longer_a_tab_of_its_own(self) -> None:
        self.assertNotIn('data-view="trending"', MARKUP)
        self.assertNotIn('id="panel-trending"', MARKUP)
        # It still exists — inside Topics & Research, where a trend is an input to a
        # proposal rather than a destination.
        topics_panel = MARKUP.split('id="panel-topics"', 1)[1].split("<section", 1)[0]
        self.assertIn('id="trend-list"', topics_panel)
        self.assertIn('id="watchlist"', topics_panel)

    def test_the_keyboard_map_covers_three_tabs_only(self) -> None:
        self.assertIn("const VIEWS=['analytics','topics','blogs']", SCRIPT)
        self.assertIn("/^[1-3]$/", SCRIPT)
        self.assertNotIn("/^[1-4]$/", SCRIPT)

    def test_the_rendered_page_exposes_no_fourth_view(self) -> None:
        page = render_page().decode("utf-8")
        nav = page.split('<nav class="primary"', 1)[1].split("</nav>", 1)[0]
        self.assertEqual(re.findall(r'data-view="([a-z-]+)"', nav), ["analytics", "topics", "blogs"])
        # Nothing anywhere on the page — nav, script or empty-state action — may
        # target a view outside the three.
        self.assertEqual(
            set(re.findall(r'data-view="([a-z-]+)"', page)), {"analytics", "topics", "blogs"}
        )


class TopicSubmissionIsNoLongerAWritingInstruction(unittest.TestCase):
    def test_the_console_offers_three_controls_per_candidate(self) -> None:
        for control in ("data-approve=", "data-suggest-open=", "data-reject-open="):
            self.assertIn(control, SCRIPT)

    def test_the_direct_topic_route_is_gone(self) -> None:
        self.assertNotIn("/ceo/api/topics", SCRIPT)
        self.assertNotIn('"/ceo/api/topics"', Path("ceo_console.py").read_text(encoding="utf-8"))

    def test_the_screen_says_researching_creates_no_card(self) -> None:
        self.assertIn("creates no board card", MARKUP)
        self.assertIn("Only a topic you approve becomes one.", MARKUP)

    def test_suppressed_candidates_are_reported_not_hidden(self) -> None:
        self.assertIn("suppressed as previously rejected", SCRIPT)

    def test_a_candidate_without_a_source_says_so(self) -> None:
        self.assertIn("This candidate names no source.", SCRIPT)


class ReadsComeFromTheDatabaseOrTheBoard(unittest.TestCase):
    """Invariant 6."""

    def test_state_payload_does_not_research_at_page_load(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()

        class ExplodingResearcher:
            connected = True

            def credit_state(self):
                raise AssertionError("a page load must never call Firecrawl")

            def discover(self, *_args, **_kwargs):
                raise AssertionError("a page load must never call Firecrawl")

            def retrieve(self, *_args, **_kwargs):
                raise AssertionError("a page load must never call Firecrawl")

        class ExplodingProposer:
            def propose(self, **_kwargs):
                raise AssertionError("a page load must never call the proposer")

        service = topic_proposals.TopicProposalService(
            root,
            researcher=ExplodingResearcher(),
            proposer=ExplodingProposer(),
            search_console=type("R", (), {"demand": lambda self, subject: ([], "")})(),
        )
        self.addCleanup(service.database.close)

        state = service.state()

        self.assertEqual(state["proposals"], [])
        self.assertEqual(state["rejected"], [])
        # The credit meter reads the last measured balance out of the database rather
        # than firing a live call; with no run recorded it says so.
        self.assertEqual(state["budget"]["status"], "unknown")
        self.assertIsNone(state["budget"]["remaining"])

    def test_an_unconfigured_budget_renders_as_not_connected_never_as_zero(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()

        class Disconnected:
            connected = False

        service = topic_proposals.TopicProposalService(
            root,
            researcher=Disconnected(),
            proposer=object(),
            search_console=type("R", (), {"demand": lambda self, subject: ([], "")})(),
        )
        self.addCleanup(service.database.close)

        budget = service.budget()

        self.assertEqual(budget["status"], "not_connected")
        self.assertIsNone(budget["used"])
        self.assertIsNone(budget["remaining"])
        self.assertIn("not connected", budget["message"])


class PageMakesNoExternalRequest(unittest.TestCase):
    """Invariant 7."""

    def test_the_rendered_page_names_no_external_host(self) -> None:
        page = render_page().decode("utf-8")
        for marker in ("http://", "https://", "//cdn", "<link", "@import"):
            self.assertNotIn(marker, page, f"page must not reference {marker}")

    # The privileged-key scan lives in test_console_auth and test_console_stages_cde,
    # which walk every module in the tree — including the two added here. Repeating it
    # would mean spelling the key in a source file, which is what those scans forbid.

    def test_the_store_is_a_local_file_under_the_profile(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        with ConsoleDB(root) as database:
            self.assertEqual(database.path, root / "state" / "console.db")
            self.assertTrue(database.path.is_file())


class ProductFinish(unittest.TestCase):
    """Section 6: the craft, checked rather than asserted."""

    def test_one_card_grammar_covers_proposals_blogs_and_competitor_findings(self) -> None:
        for builder in ("function proposalCard(", "function gapRow(", "function renderBlogs("):
            body = SCRIPT.split(builder, 1)[1][:1200]
            self.assertIn('class="card"', body, builder)

    def test_status_is_never_colour_alone(self) -> None:
        # Every pill renders a glyph and a word; the tone class only tints them.
        self.assertIn("data-glyph=", SCRIPT)
        self.assertIn(".pill::before{content:attr(data-glyph)}", CSS)
        for key in ("proposed", "revising", "rejected", "uncontested", "weak_position"):
            self.assertIn(f"{key}:" if ":" in key else key, SCRIPT)
        for tone in ("tone-wait", "tone-stop", "tone-mute"):
            self.assertIn(f".pill.{tone}", CSS)

    def test_the_status_vocabulary_covers_the_whole_lifecycle(self) -> None:
        vocabulary = SCRIPT.split("const STATUS={", 1)[1].split("};", 1)[0]
        for state in ("proposed", "revising", "approved", "carded", "rejected"):
            self.assertIn(state, vocabulary)

    def test_empty_states_name_the_next_action(self) -> None:
        self.assertIn("function emptyState(", SCRIPT)
        self.assertIn("A topic has to be approved in Topics & Research", SCRIPT)
        self.assertIn("'Go to Topics & Research','data-view=\"topics\"'", SCRIPT)
        self.assertIn("'Enter a subject','data-focus=\"subject\"'", SCRIPT)

    def test_loading_is_skeletal_and_not_a_spinner(self) -> None:
        self.assertIn("function skeleton(", SCRIPT)
        self.assertIn("renderSkeletons();", SCRIPT)
        self.assertIn(".skeleton{height:104px", CSS, "skeletons must occupy the real row height")
        self.assertNotIn("spinner", SCRIPT.lower())

    def test_actions_are_optimistic_and_roll_back_visibly(self) -> None:
        approve = SCRIPT.split("async function approveProposal(", 1)[1].split("\n}", 1)[0]
        self.assertIn("classList.add('is-pending')", approve)
        self.assertIn("toast(", approve)
        self.assertIn("classList.remove('is-pending')", approve, "a failure must restore the card")
        self.assertIn(".card.is-pending", CSS)

    def test_every_documented_shortcut_is_bound_and_shown(self) -> None:
        for binding in ("event.key==='j'", "event.key==='k'", "event.key==='Enter'", "event.key==='/'"):
            self.assertIn(binding, SCRIPT)
        self.assertIn("/^[1-3]$/", SCRIPT)
        self.assertIn("event.key==='Escape'", SCRIPT)
        for label in ("tabs", "search", "move", "open", "close"):
            self.assertIn(label, MARKUP.split('<footer class="shortcuts">', 1)[1])

    def test_typing_in_a_field_does_not_trigger_shortcuts(self) -> None:
        handler = SCRIPT.split("document.addEventListener('keydown'", 1)[1]
        self.assertIn("if(typing||event.ctrlKey||event.metaKey||event.altKey)return;", handler)

    def test_motion_is_disabled_under_reduced_motion(self) -> None:
        self.assertIn("@media(prefers-reduced-motion:reduce)", CSS)
        reduced = CSS.split("@media(prefers-reduced-motion:reduce)", 1)[1]
        self.assertIn("animation-duration:.001ms!important", reduced)
        self.assertIn("transition-duration:.001ms!important", reduced)

    def test_the_layout_answers_a_phone(self) -> None:
        self.assertIn("@media(max-width:760px)", CSS)
        phone = CSS.split("@media(max-width:760px)", 1)[1]
        for rule in (".analytics-grid,.metrics{grid-template-columns:1fr}", "dialog{width:100%"):
            self.assertIn(rule, phone)
        self.assertIn("--tap:44px", CSS, "touch targets need a floor")
        self.assertIn("min-height:var(--tap)", CSS)

    def test_the_reader_stays_generous_while_lists_stay_tight(self) -> None:
        self.assertIn(".article-sheet{max-width:720px", CSS)
        self.assertIn("line-height:1.7", CSS.split(".article-sheet{", 1)[1][:200])
        self.assertIn(".rows{display:flex;flex-direction:column;gap:10px}", CSS)

    def test_focus_is_visible_for_keyboard_users(self) -> None:
        self.assertIn(":focus-visible", CSS)


class CompetitorPanelIsHonest(unittest.TestCase):
    """Invariant 5 at the console layer."""

    def test_an_unanalysed_competitor_renders_an_empty_state_not_zeroes(self) -> None:
        renderer = SCRIPT.split("function renderCompetitor(", 1)[1].split("\n}", 1)[0]
        self.assertIn("data.status==='none'", renderer)
        self.assertIn("emptyState(", renderer)

    def test_a_missing_position_says_so_rather_than_showing_zero(self) -> None:
        row = SCRIPT.split("function gapRow(", 1)[1].split("\n}", 1)[0]
        self.assertIn("finding.our_position==null", row)
        self.assertIn("no Search Console data for this topic", row)

    def test_the_volume_gap_is_surfaced_on_the_panel(self) -> None:
        self.assertIn("data.volume_message", SCRIPT)

    def test_the_panel_reports_what_the_analysis_cost(self) -> None:
        renderer = SCRIPT.split("function renderCompetitor(", 1)[1].split("\n}", 1)[0]
        self.assertIn("credits_used", renderer)
        self.assertIn("sitemap_url_count", renderer)
        self.assertIn("free", renderer)


class WatchlistStillNeverCreatesACard(unittest.TestCase):
    def test_watchlist_writes_no_board_card(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()

        ceo_actions.update_watchlist(root, "battery data", "add")

        self.assertFalse((root / "tasks.md").exists())
        self.assertEqual(ceo_actions.read_watchlist(root), ["battery data"])


if __name__ == "__main__":
    unittest.main()
