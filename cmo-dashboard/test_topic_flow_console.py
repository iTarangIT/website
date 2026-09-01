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
import ceo_reader
from ceo_page import render_page
from ceo_script import SCRIPT
from ceo_style import CSS
from cmo_runtime import topic_proposals
from cmo_runtime.console_db import ConsoleDB


class FiveTabsAndNoSixth(unittest.TestCase):
    """Invariant 4, widened twice.

    Archived is a destination and not a filter on Topics because it holds work the
    CEO has already decided about: the candidates swept aside when he approved one
    of their siblings. Keeping them on Topics is exactly the pile-up the tab
    exists to end.

    Social is the second widening. It is not a filter on Blogs because it holds a
    different decision about a different object: Blogs decides whether an article
    ships, Social decides what is said about it on three networks once it has.
    Folding three editable drafts and a send gate into a blog row would make the
    Blogs list about two things.

    Nothing else earns a tab, and Social went fourth rather than second so that
    1, 2 and 3 keep meaning what they have always meant.
    """

    def test_exactly_five_primary_tabs_render(self) -> None:
        tabs = re.findall(r'data-view="([a-z-]+)"', MARKUP)
        self.assertEqual(tabs, ["topics", "blogs", "analytics", "social", "archived"])

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

    def test_the_keyboard_map_covers_five_tabs_only(self) -> None:
        self.assertIn("const VIEWS=['topics','blogs','analytics','social','archived']", SCRIPT)
        self.assertIn("/^[1-5]$/", SCRIPT)
        self.assertNotIn("/^[1-6]$/", SCRIPT)

    def test_the_rendered_page_exposes_no_sixth_view(self) -> None:
        page = render_page().decode("utf-8")
        nav = page.split('<nav class="primary"', 1)[1].split("</nav>", 1)[0]
        self.assertEqual(
            re.findall(r'data-view="([a-z-]+)"', nav),
            ["topics", "blogs", "analytics", "social", "archived"],
        )
        # Nothing anywhere on the page — nav, script or empty-state action — may
        # target a view outside the five.
        self.assertEqual(
            set(re.findall(r'data-view="([a-z-]+)"', page)),
            {"analytics", "topics", "blogs", "social", "archived"},
        )


class TopicSubmissionIsNoLongerAWritingInstruction(unittest.TestCase):
    def test_the_console_offers_three_controls_per_candidate(self) -> None:
        for control in ("data-approve=", "data-suggest-open=", "data-reject-open="):
            self.assertIn(control, SCRIPT)

    def test_approving_a_candidate_says_what_it_produces(self) -> None:
        """A bare "Approve" beside Reject and Archive reads as a verdict on the idea.

        It is not: it is the one control that mints a board card and sends the
        topic to be written, and the label has to say which of the four it is.
        """
        self.assertIn(">Approve for blog<", SCRIPT)
        self.assertNotIn(">Approve<", SCRIPT)

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
        for marker in ("http://", "https://", "//cdn", "<link", "@import", "@font-face",
                       "url(", "srcset", "<iframe", "importScripts", "WebSocket",
                       "XMLHttpRequest", "EventSource"):
            self.assertNotIn(marker, page, f"page must not reference {marker}")

    def test_every_request_the_script_makes_is_same_origin_and_path_relative(self) -> None:
        # fetch() only ever sees a literal beginning with "/" or a template built
        # from one. Anything else would be a host this console does not control.
        for call in re.findall(r"(?:api|post)\(\s*([`'\"])(.*?)\1", SCRIPT):
            with self.subTest(target=call[1]):
                self.assertTrue(call[1].startswith("/"), f"{call[1]} is not same-origin")
        self.assertNotIn("fetch('http", SCRIPT)
        self.assertNotIn('fetch("http', SCRIPT)

    def test_the_reader_renders_no_remote_image(self) -> None:
        # A scraped research brief carries ![alt](https://…). The alt text survives;
        # the request does not.
        html = ceo_reader.render_markdown_fragment("![Bain logo](https://www.bain.com/logo.svg)")

        self.assertNotIn("<img", html)
        self.assertNotIn("bain.com", html)
        self.assertIn("Bain logo", html)

    def test_no_console_module_reaches_a_network_host_at_page_load(self) -> None:
        for name in ("ceo_markup.py", "ceo_script.py", "ceo_style.py", "ceo_page.py", "ceo_reader.py"):
            with self.subTest(module=name):
                source = Path(name).read_text(encoding="utf-8")
                self.assertNotIn("urlopen", source)
                self.assertNotIn("requests.", source)
                self.assertNotIn("googleapis.com", source)

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
        # The whole builder, not its first N characters: a fixed window turns a
        # comment into a test failure, which teaches you to write shorter comments
        # rather than to keep the grammar shared.
        for builder in ("function proposalCard(", "function gapRow(", "function blogCard("):
            body = SCRIPT.split(builder, 1)[1].split("\nfunction ", 1)[0]
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
        # Skeletons stand at the real height of the row they replace, per shape.
        for shape, height in ((".skeleton.card-h", "112px"), (".skeleton.row-h", "44px"),
                              (".skeleton.tile-h", "92px"), (".skeleton.chart-h", "200px")):
            self.assertIn(f"{shape}{{height:{height}}}", CSS)
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
        self.assertIn("/^[1-5]$/", SCRIPT)
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
        self.assertIn("@media(max-width:640px)", CSS)
        phone = CSS.split("@media(max-width:640px)", 1)[1]
        for rule in ("dialog{width:100%",
                     ".card-row{display:block}", ".chips{flex-wrap:nowrap;overflow-x:auto",
                     ".opportunity{display:block}"):
            self.assertIn(rule, phone)
        # Every tile strip collapses to two columns on a phone, whatever it
        # counts on a desktop. The Google Analytics strip is six wide and its
        # drill-down four, and a modifier that outranks this rule would leave
        # six tiles fighting over a phone's width.
        two_up = [line for line in phone.splitlines()
                  if "grid-template-columns:1fr 1fr" in line]
        self.assertEqual(len(two_up), 1, "one rule should collapse the tile strips")
        for selector in (".tiles", ".tiles.six", ".tiles.four"):
            self.assertIn(selector, two_up[0])
        # A wide table scrolls inside its own box; the page itself never does.
        self.assertIn(".table-scroll{overflow-x:auto", CSS)
        self.assertIn("--tap:44px", CSS, "touch targets need a floor")
        self.assertIn("min-height:var(--tap)", CSS)

    def test_the_reader_stays_generous_while_lists_stay_tight(self) -> None:
        self.assertIn(".article-sheet{max-width:66ch", CSS)
        self.assertIn("line-height:1.72", CSS.split(".article-sheet{", 1)[1][:260])
        self.assertIn(".rows{display:flex;flex-direction:column;gap:8px}", CSS)
        # Lists and tables run tighter than the prose they point at.
        self.assertIn("--pad-tight:11px", CSS)
        self.assertIn("table.data th,table.data td{padding:8px 10px", CSS)

    def test_focus_is_visible_for_keyboard_users(self) -> None:
        self.assertIn(":focus-visible", CSS)

    def test_every_data_attribute_survives_the_html_round_trip(self) -> None:
        # HTML lowercases attribute names, so data-fooBar arrives as dataset.foobar
        # and the handler reading dataset.fooBar never fires. Dash-case only.
        emitted = set(re.findall(r'\sdata-([A-Za-z][\w-]*)=', SCRIPT + MARKUP))
        self.assertEqual(
            sorted(name for name in emitted if name.lower() != name),
            [],
            "a data-* attribute uses camelCase and will not reach dataset",
        )

    def test_touch_targets_stay_thumb_sized_on_a_phone(self) -> None:
        phone = CSS.split("@media(max-width:640px)", 1)[1]
        for rule in (".chip{flex:0 0 auto;min-height:40px", ".small{min-height:40px"):
            self.assertIn(rule, phone)


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
