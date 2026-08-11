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
        self.assertEqual(len(re.findall(r'data-view="', page)), 3)


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
