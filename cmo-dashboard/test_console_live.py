"""The console keeps itself up to date — checked by running it, not reading it.

Seven of the eight invariants for "Sanchit never presses refresh" are about what
the page *does* over time, and none of them can be established from markup. So
this suite boots ceo_script.py under `console_live_harness.js`, whose DOM has node
identity, a settable `document.hidden`, and a scripted `fetch` that can be made to
fail or to never answer at all.

Covered here:

  1. a slow action shows busy state before the request comes back
  2. a change made elsewhere is picked up by the poller, with no reload
  3. an open editor with unsaved text is never overwritten
  4. paging, sort, filter, search text and scroll survive a background update
  6. nothing is polled while the tab is hidden; focus resumes it immediately
  7. one mechanism — the failure ladder, and no blind 60-second reload

Invariant 5 lives in `test_ceo_version.py` (the endpoint's cost) and invariant 8
in `test_served_bytes.py` (the wire).

Skipped when node is unavailable; `run-tests` reports the skip rather than
passing quietly.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from ceo_script import SCRIPT

HERE = Path(__file__).resolve().parent
NODE = shutil.which("node")
HARNESS = HERE / "console_live_harness.js"


def _proposal(number: int, title: str = "", status: str = "proposed") -> dict:
    return {
        "id": number,
        "title": title or f"Candidate topic {number}",
        "subject": "battery data",
        "outline": "An outline that is long enough to look like one.",
        "keywords": ["battery", "range"],
        "status": status,
        "round": 1,
        "source_kind": "search_console",
        "source_refs": [f"gsc:battery {number}"],
        "history": [],
    }


def _state_block(state: str, label: str, **overrides: object) -> dict:
    return {
        "state": state,
        "label": label,
        "reason": "",
        "retryable": False,
        "started_at": "",
        "url": "",
        **overrides,
    }


def _unwritten(task_id: str, title: str, blog: dict) -> dict:
    """A content card with no article yet — the state that used to be invisible."""
    return {
        "id": task_id,
        "title": title,
        "decision_status": "awaiting decision",
        "decision_approved": False,
        "change_status": "",
        "revision_round": "0",
        "approval_thread": [],
        "publishing_pipeline": None,
        "article": None,
        "blog": blog,
    }


def _blog(task_id: str, title: str, text: str = "First draft.", blog: dict | None = None) -> dict:
    return {
        "id": task_id,
        "title": title,
        "decision_status": "awaiting decision",
        "decision_approved": False,
        "change_status": "",
        "revision_round": "0",
        "approval_thread": [],
        "publishing_pipeline": None,
        "blog": blog or _state_block("awaiting_you", "Awaiting you"),
        "article": {
            "text": text,
            "html": f"<p>{text}</p>",
            "metadata": {"slug": "slug"},
            "word_count": 120,
            "read_minutes": 1,
            "files": [],
            "revisions": [],
            "image_slots": [],
            "review_notes_html": "",
            "review_note_titles": [],
        },
    }


def _state(proposals: list[dict], blogs: list[dict]) -> dict:
    return {
        "topics": {"proposals": proposals, "rejected": [], "carded": [], "budget": {}},
        "blogs": blogs,
        "trending": [],
        "trending_messages": [],
        "watchlist": [],
        "research_queue": [],
        "analytics": {
            "search": {"status": "none", "message": "not connected"},
            "search_console": {},
            "ga4": {"status": "none"},
            "competitor": {"status": "none"},
        },
        "controls": {"range": "28", "range_days": 28, "device": "all"},
    }


BASE = _state([_proposal(n) for n in range(1, 4)], [_blog("TASK-1", "First article")])


@unittest.skipIf(NODE is None, "node is unavailable")
@unittest.skipIf(not HARNESS.exists(), f"{HARNESS.name} was not deployed alongside the suite")
class ConsoleStaysCurrent(unittest.TestCase):
    """Nothing here reads the script as text. Everything is executed."""

    def drive(self, plan: dict) -> dict:
        plan.setdefault("state", BASE)
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / "console.js"
            script.write_text(SCRIPT, encoding="utf-8")
            spec = Path(folder) / "plan.json"
            spec.write_text(json.dumps(plan), encoding="utf-8")
            result = subprocess.run(
                [NODE, str(HARNESS), str(script), str(spec)],
                capture_output=True, text=True, timeout=60,
            )
        if result.returncode != 0:
            self.fail(f"the console failed to run:\n{result.stderr}")
        return json.loads(result.stdout)

    def steps(self, plan: dict) -> list[dict]:
        return self.drive(plan)["steps"]

    # ---- invariant 1: a slow action shows itself immediately ---------------

    def test_a_slow_action_goes_busy_before_the_request_answers(self) -> None:
        # The propose call never resolves, so everything observed here is what is
        # on screen while the run is still going.
        step = self.steps({
            "steps": [{
                "do": "research", "subject": "battery data",
                "hang": "/ceo/api/propose",
            }],
        })[0]

        self.assertTrue(step["immediate"]["disabled"], "the button stayed clickable")
        self.assertTrue(step["immediate"]["label"].startswith("Researching…"))
        self.assertRegex(step["immediate"]["label"], r"Researching… \d+s", "no elapsed seconds")
        self.assertTrue(step["immediate"]["busy"])

    def test_a_slow_action_holds_the_space_its_results_will_fill(self) -> None:
        step = self.steps({
            "steps": [{
                "do": "research", "subject": "battery data",
                "hang": "/ceo/api/propose",
            }],
        })[0]

        self.assertFalse(step["immediate"]["skeletonHidden"], "no skeleton while it runs")
        self.assertIn('class="skeleton card-h"', step["immediate"]["skeleton"],
                      "the skeleton is not at candidate-card height")

    def test_a_failed_action_leaves_the_reason_where_the_results_would_be(self) -> None:
        step = self.steps({
            "steps": [{
                "do": "research", "subject": "battery data",
                "fail": {"path": "/ceo/api/propose", "status": 402,
                         "error": "Firecrawl returned 402: monthly credits exhausted"},
            }],
        })[0]

        self.assertFalse(step["topicsPendingHidden"], "the failure was taken off screen")
        self.assertIn("Firecrawl returned 402: monthly credits exhausted", step["topicsPending"])
        self.assertIn('class="failure"', step["topicsPending"])
        self.assertIn("Firecrawl returned 402", step["proposeResult"])

    def test_a_finished_action_never_asks_for_a_reload(self) -> None:
        step = self.steps({"steps": [{"do": "research", "subject": "battery data"}]})[0]

        self.assertIn("/ceo/api/propose", " ".join(step["requests"]))
        self.assertIn("/ceo/api/state", " ".join(step["requests"]),
                      "results have to arrive without a page load")
        self.assertTrue(step["topicsPendingHidden"], "the skeleton outlived the results")

    # ---- invariant 2: a change made elsewhere arrives -----------------------

    def test_a_board_change_is_picked_up_when_the_token_moves(self) -> None:
        arrived = _state(
            [_proposal(n) for n in range(1, 4)],
            [_blog("TASK-1", "First article"), _blog("TASK-2", "Written elsewhere")],
        )
        steps = self.steps({
            "steps": [
                {"name": "same token", "do": "poll"},
                {"name": "moved token", "do": "poll", "version": "v2", "state": arrived},
            ],
        })

        self.assertNotIn("/ceo/api/state", " ".join(steps[0]["requests"]),
                         "an unchanged token still refetched everything")
        self.assertIn("/ceo/api/state", " ".join(steps[1]["requests"]))
        self.assertIn("Written elsewhere", steps[1]["blogsHtml"])

    def test_the_poll_interval_starts_at_three_seconds(self) -> None:
        step = self.steps({"steps": [{"do": "poll"}]})[0]

        self.assertEqual(step["pollDelay"], 3000)
        self.assertTrue(step["pollActive"], "the poller did not schedule its next check")

    # ---- the blog chain, watched from the page -----------------------------

    def test_a_card_walks_from_queued_to_awaiting_him_with_no_reload(self) -> None:
        """Invariants 1, 2 and 6, from the seat they matter in.

        He approves a topic and looks at Blogs. Nobody reloads anything: three
        moves of the version token, and the row says something different each
        time. Before this, the row was not on the tab at all until the article
        existed, so the whole run happened behind a blank screen.
        """
        queued = _state([], [_unwritten("TASK-9", "Battery repair costs",
                                        _state_block("queued", "Queued to be written"))])
        researching = _state([], [_unwritten("TASK-9", "Battery repair costs",
                                             _state_block("researching", "Researching…",
                                                          started_at="2026-08-12T07:00:00Z"))])
        writing = _state([], [_unwritten("TASK-9", "Battery repair costs",
                                         _state_block("writing", "Writing…",
                                                      started_at="2026-08-12T07:00:00Z"))])
        ready = _state([], [_blog("TASK-9", "Battery repair costs",
                                  blog=_state_block("awaiting_you", "Awaiting you"))])
        steps = self.steps({
            "state": queued,
            "ui": {"blogs": {"page": 1, "size": 10, "search": "", "filter": "all"}},
            "steps": [
                {"name": "queued", "do": "showView", "view": "blogs"},
                {"name": "researching", "do": "poll", "version": "v2", "state": researching},
                {"name": "writing", "do": "poll", "version": "v3", "state": writing},
                {"name": "ready", "do": "poll", "version": "v4", "state": ready},
            ],
        })

        self.assertIn("Queued to be written", steps[0]["blogsHtml"])
        self.assertIn("Researching…", steps[1]["blogsHtml"])
        self.assertIn("Writing…", steps[2]["blogsHtml"])
        self.assertIn("Awaiting you", steps[3]["blogsHtml"])
        # Each move came from the token, not from a page load.
        for step in steps[1:]:
            self.assertIn("/ceo/api/state", " ".join(step["requests"]))
        # And it is the same row throughout, patched rather than rebuilt.
        self.assertEqual([row["key"] for row in steps[3]["rowsAfter"]["blogs"]], ["TASK-9"])

    def test_a_running_write_carries_a_clock_that_is_not_re_rendered(self) -> None:
        running = _state([], [_unwritten("TASK-9", "Battery repair costs",
                                         _state_block("writing", "Writing…",
                                                      started_at="2026-08-12T07:00:00Z"))])
        step = self.steps({
            "state": running,
            "steps": [{"do": "showView", "view": "blogs"}],
        })[0]

        self.assertIn('data-elapsed="2026-08-12T07:00:00Z"', step["blogsHtml"])

    def test_a_failed_card_shows_its_reason_and_a_retry_button(self) -> None:
        failed = _state([], [_unwritten(
            "TASK-9", "Battery repair costs",
            _state_block("failed", "Could not be written", retryable=True,
                         reason="writer article has 1742 words; WRITER_CONTRACT requires 900-1,400"),
        )])
        step = self.steps({"state": failed, "steps": [{"do": "showView", "view": "blogs"}]})[0]

        self.assertIn("Could not be written", step["blogsHtml"])
        self.assertIn("1742 words", step["blogsHtml"])
        self.assertIn('data-retry="TASK-9"', step["blogsHtml"])

    def test_a_held_card_shows_its_reason_but_no_retry(self) -> None:
        held = _state([], [_unwritten(
            "TASK-9", "Battery repair costs",
            _state_block("held", "On hold", reason="Held behind another card by CEO instruction"),
        )])
        step = self.steps({"state": held, "steps": [{"do": "showView", "view": "blogs"}]})[0]

        self.assertIn("On hold", step["blogsHtml"])
        self.assertIn("CEO instruction", step["blogsHtml"])
        self.assertNotIn("data-retry=", step["blogsHtml"], "a held card offered a retry")

    def test_a_published_card_links_its_preview(self) -> None:
        live = _state([], [_blog(
            "TASK-9", "Battery repair costs",
            blog=_state_block("published", "Live on the site",
                              url="https://itarangwebsite.vercel.app/blog/battery-repair"),
        )])
        step = self.steps({"state": live, "steps": [{"do": "showView", "view": "blogs"}]})[0]

        self.assertIn("Live on the site", step["blogsHtml"])
        self.assertIn('href="https://itarangwebsite.vercel.app/blog/battery-repair"', step["blogsHtml"])

    def test_a_status_change_does_not_disturb_an_open_editor(self) -> None:
        """The chain moving underneath him must not cost him a typed sentence."""
        theirs = _state([_proposal(1)], [_blog("TASK-1", "First article", "Their newer text.",
                                               blog=_state_block("rewriting", "Being rewritten"))])
        step = self.steps({
            "state": _state([_proposal(1)], [_blog("TASK-1", "First article", "First draft.")]),
            "steps": [{
                "do": "poll", "version": "v2", "state": theirs,
                "editing": {"task": "TASK-1", "base": "First draft.", "text": "My unsaved sentence."},
            }],
        })[0]

        self.assertIn("Being rewritten", step["blogsHtml"])
        self.assertEqual(step["editorText"], "My unsaved sentence.")

    # The Process tab and its renderer are gone. What the pipeline records is
    # unchanged and still reaches the page — `tests/test_pipeline_stages.py` and
    # `test_served_bytes.py` prove the rows over a real socket. There is simply no
    # longer a renderer here to test.

    # ---- the decision controls appear only where a decision can be recorded --

    def decidable_card(self, section: str, state: str, label: str) -> dict:
        card = _blog("TASK-9", "Battery repair costs", blog=_state_block(state, label))
        card["board_section"] = section
        card["status"] = section
        return card

    def read_tab(self, card: dict) -> str:
        """The whole Read tab: the article, the change request and the publish block.

        There is nowhere else left to look. A control that is not in this string
        is not on the console.
        """
        return self.steps({
            "state": _state([], [card]),
            "steps": [{"do": "detail", "task": "TASK-9", "tab": "read"}],
        })[0]["detailBody"]

    def test_a_card_in_human_approval_offers_ask_for_changes_and_publish_on_read(self) -> None:
        """Both things a human does, on the tab holding the thing they are doing it to.

        This used to be a three-tab errand: read on Read, approve on Discussion,
        publish on Impact. One screen now, and no Approve button in front of the
        publish — pressing Publish is the approval.
        """
        body = self.read_tab(self.decidable_card("Human Approval", "awaiting_you", "Awaiting you"))

        self.assertIn("article-sheet", body, "the article is not on the tab the controls are on")
        self.assertIn('data-revision="1"', body)
        self.assertIn("revision-comment", body)
        self.assertIn('data-blog-publish="1"', body)
        self.assertNotIn('data-decision="approve"', body, "the Approve step is back")

    def test_no_lane_offers_an_approve_button_any_more(self) -> None:
        """The one control that was removed outright, checked in every state it had."""
        lanes = [
            ("Human Approval", "awaiting_you", "Awaiting you"),
            ("Human Approval", "approved", "Approved"),
            ("CMO Review", "checking", "Being checked"),
            ("Backlog", "queued", "Queued to be written"),
            ("In Progress", "writing", "Writing…"),
        ]
        for section, state, label in lanes:
            with self.subTest(state=state):
                card = self.decidable_card(section, state, label)
                if state == "approved":
                    card["decision_approved"] = True
                    card["decision_stale"] = True
                    card["decision_change"] = ["the article changed"]

                self.assertNotIn('data-decision="approve"', self.read_tab(card))

    def test_a_lane_that_cannot_publish_is_not_offered_a_publish_button(self) -> None:
        """A button whose only possible outcome is a refusal is not a courtesy.

        `preflight` and `DecisionStore.decide` both refuse a card outside Human
        Approval; drawing the control anyway would be the same lie the Approve
        button used to tell on the Discussion tab.
        """
        for section, state, label in (("CMO Review", "checking", "Being checked"),
                                      ("Backlog", "queued", "Queued to be written")):
            with self.subTest(state=state):
                body = self.read_tab(self.decidable_card(section, state, label))

                self.assertNotIn('data-blog-publish="1"', body, f"{state} offered Publish")
                self.assertNotIn("blog-publish-block", body)

    def test_a_card_in_cmo_review_offers_neither_and_says_why(self) -> None:
        """Approve there is a button whose only outcome is "not recorded".

        Ask for changes there is worse: it did not fail, it succeeded — setting
        `revision requested` on a card its reader had never seen, which the
        content worker would then pick up and rewrite.
        """
        body = self.read_tab(self.decidable_card("CMO Review", "checking", "Being checked"))

        self.assertNotIn('data-decision="approve"', body)
        self.assertNotIn('data-revision="1"', body)
        self.assertNotIn("revision-comment", body)
        self.assertIn("Being checked. It will come to you when review finishes.", body)

    def test_every_lane_that_cannot_decide_says_when_it_will_come_to_him(self) -> None:
        lanes = [
            ("Backlog", "queued", "Queued to be written", "once the article exists"),
            ("In Progress", "writing", "Writing…", "when it is finished"),
            ("Backlog", "failed", "Could not be written", "nothing to decide yet"),
            ("Backlog", "held", "On hold", "once it is released"),
            ("CMO Review", "rewriting", "Being rewritten", "when it is done"),
        ]
        for section, state, label, promise in lanes:
            with self.subTest(state=state):
                body = self.read_tab(self.decidable_card(section, state, label))

                self.assertNotIn('data-decision="approve"', body, f"{state} offered Approve")
                self.assertNotIn('data-revision="1"', body, f"{state} offered Ask for changes")
                self.assertIn(promise, body, f"{state} does not say when it will come to him")

    def test_a_stale_approval_says_what_moved_and_publishes_over_it(self) -> None:
        """The deadlock, from the seat it deadlocked in.

        Approved, then the article changed. There is no Approve again button any
        more because there is nothing to unblock: publishing records a fresh
        decision over the article as it stands. He is still told the old approval
        does not describe what he is reading.
        """
        card = self.decidable_card("Human Approval", "approved", "Approved")
        card["decision_approved"] = True
        card["decision_stale"] = True
        card["decision_status"] = "approval out of date"
        card["decision_summary"] = {"approver_id": "ceo@itarang.com", "timestamp": "2026-08-12T09:58:01Z"}
        card["decision_change"] = ["the article changed"]

        body = self.read_tab(card)

        self.assertIn("the article has changed since", body)
        self.assertIn("the article changed", body)
        self.assertIn("keeps the old one", body)
        self.assertIn('data-blog-publish="1"', body, "there is no click that resolves this")
        self.assertNotIn('data-decision="approve"', body)

    def test_a_stale_approval_also_offers_ask_for_changes(self) -> None:
        """Approve-only would be a trap: find a fault, and the only button approves."""
        card = self.decidable_card("Human Approval", "approved", "Approved")
        card["decision_approved"] = True
        card["decision_stale"] = True
        card["decision_summary"] = {"approver_id": "ceo@itarang.com", "timestamp": "2026-08-12T09:58:01Z"}
        card["decision_change"] = ["the category changed from financing to safety"]

        body = self.read_tab(card)

        self.assertIn('data-revision="1"', body)
        self.assertIn("revision-comment", body)
        self.assertIn("the category changed from financing to safety", body)

    def test_an_already_approved_card_shows_the_decision_not_the_buttons(self) -> None:
        card = self.decidable_card("Human Approval", "approved", "Approved")
        card["decision_approved"] = True
        card["decision_status"] = "approved"
        card["decision_summary"] = {"approver_id": "ceo@itarang.com", "timestamp": "2026-08-12T09:00:00Z"}

        body = self.read_tab(card)

        self.assertNotIn('data-decision="approve"', body)
        self.assertNotIn('data-revision="1"', body)
        self.assertIn("Approved by ceo@itarang.com", body)

    def test_the_error_surfaces_survive_in_every_lane(self) -> None:
        """`runAction` writes failures into these nodes; losing them loses the reason."""
        for section, state, label in (("Human Approval", "awaiting_you", "Awaiting you"),
                                      ("CMO Review", "checking", "Being checked")):
            with self.subTest(section=section):
                body = self.read_tab(self.decidable_card(section, state, label))

                self.assertIn('id="detail-pending"', body)
                self.assertIn('id="detail-error"', body)

    # ---- a check that cannot answer says so --------------------------------

    def publish_block(self, task: dict, **step: object) -> dict:
        """What the publish block itself says, not what the pane was painted with."""
        return self.steps({
            "state": _state([], [task]),
            "steps": [{"do": "detail", "task": "TASK-9", "tab": "read", **step}],
        })[0]["blogPublish"]

    def approved_blog(self) -> dict:
        card = _blog("TASK-9", "Battery repair costs", blog=_state_block("approved", "Approved"))
        card["board_section"] = "Human Approval"
        card["decision_approved"] = True
        return card

    def test_a_check_that_never_answers_gives_up_out_loud(self) -> None:
        """The bug: "Checking whether this article can be published…" with no end.

        A spinner that never resolves is indistinguishable from a broken console —
        there is nothing on screen to say whether to wait, retry, or give up.
        """
        block = self.publish_block(self.approved_blog(),
                            hang="/ceo/blog-publish-check", checkTimeout=30)

        self.assertNotIn("Checking whether this article can be published", block["state"])
        self.assertIn("Could not check whether this can be published", block["state"])
        self.assertIn("did not answer in time", block["state"])
        self.assertEqual(block["checked"], "1", "the block still claims a check is running")

    def test_a_check_that_gave_up_offers_a_way_to_try_again(self) -> None:
        block = self.publish_block(self.approved_blog(),
                            hang="/ceo/blog-publish-check", checkTimeout=30)

        self.assertIn('data-recheck="1"', block["state"])
        self.assertIn("Check again", block["state"])

    def test_a_check_that_fails_says_why_rather_than_spinning(self) -> None:
        block = self.publish_block(self.approved_blog(), fail={
            "path": "/ceo/blog-publish-check", "status": 500,
            "error": "the git remote could not be reached",
        })

        self.assertNotIn("Checking whether this article can be published", block["state"])
        self.assertIn("the git remote could not be reached", block["state"])

    def test_a_refused_check_lists_the_blockers_instead_of_spinning(self) -> None:
        block = self.publish_block(self.approved_blog())

        self.assertNotIn("Checking whether this article can be published", block["state"])
        self.assertIn("Cannot publish yet", block["state"])

    def test_an_eligible_check_enables_the_button_and_names_the_slug(self) -> None:
        block = self.publish_block(self.approved_blog(), publishCheck={
            "eligible": True, "blockers": [], "slug": "battery-repair-costs",
            "category": "battery-selection", "files": ["src/data/blog-posts.ts"],
            "request_id": "single-use-token",
        })

        self.assertIn("Ready to publish as /blog/battery-repair-costs", block["state"])
        self.assertFalse(block["disabled"])

    def test_an_answer_the_console_cannot_read_is_still_an_answer(self) -> None:
        """Malformed is a failure with a reason, not a spinner that never ends."""
        block = self.publish_block(self.approved_blog(), publishCheck={"ok": True})

        self.assertNotIn("Checking whether this article can be published", block["state"])
        self.assertIn("Could not check whether this can be published", block["state"])
        self.assertEqual(block["checked"], "1")

    def test_the_button_is_never_left_enabled_when_the_check_failed(self) -> None:
        for step in ({"hang": "/ceo/blog-publish-check", "checkTimeout": 30},
                     {"fail": {"path": "/ceo/blog-publish-check", "status": 500, "error": "boom"}}):
            with self.subTest(step=sorted(step)):
                block = self.publish_block(self.approved_blog(), **step)

                self.assertTrue(block["disabled"], "publish was clickable after a failed check")

    # ---- invariant 3: an open editor is sacred -----------------------------

    def test_an_editor_with_unsaved_text_is_not_overwritten(self) -> None:
        theirs = _state([_proposal(1)], [_blog("TASK-1", "First article", "Their newer text.")])
        step = self.steps({
            "state": _state([_proposal(1)], [_blog("TASK-1", "First article", "First draft.")]),
            "steps": [{
                "do": "poll", "version": "v2", "state": theirs,
                "editing": {"task": "TASK-1", "base": "First draft.", "text": "My unsaved sentence."},
            }],
        })[0]

        self.assertEqual(step["editorText"], "My unsaved sentence.", "typed work was destroyed")
        self.assertFalse(step["editorConflictHidden"], "he was never told theirs changed")
        self.assertEqual(
            step["editorConflict"],
            "This article changed elsewhere. Save yours, or reload to see theirs.",
        )

    def test_an_untouched_editor_quietly_takes_the_newer_version(self) -> None:
        theirs = _state([_proposal(1)], [_blog("TASK-1", "First article", "Their newer text.")])
        step = self.steps({
            "state": _state([_proposal(1)], [_blog("TASK-1", "First article", "First draft.")]),
            "steps": [{
                "do": "poll", "version": "v2", "state": theirs,
                "editing": {"task": "TASK-1", "base": "First draft.", "text": "First draft."},
            }],
        })[0]

        self.assertEqual(step["editorText"], "Their newer text.")
        self.assertTrue(step["editorConflictHidden"], "nothing was at risk, so nothing to warn about")

    # ---- invariant 4: his place on the page survives ------------------------

    def test_paging_filter_and_search_survive_a_background_update(self) -> None:
        many = _state([_proposal(n) for n in range(1, 30)], [_blog("TASK-1", "First article")])
        grown = _state([_proposal(n) for n in range(1, 31)], [_blog("TASK-1", "First article")])
        step = self.steps({
            "state": many,
            "ui": {"topics": {"page": 2, "size": 10, "search": "candidate", "filter": "proposed"}},
            "steps": [{
                "do": "poll", "version": "v2", "state": grown,
                "searchBox": {"view": "topics", "text": "candidate"},
            }],
        })[0]

        self.assertEqual(step["ui"]["topics"]["page"], 2, "he was thrown back to page one")
        self.assertEqual(step["ui"]["topics"]["size"], 10)
        self.assertEqual(step["ui"]["topics"]["filter"], "proposed")
        self.assertEqual(step["ui"]["topics"]["search"], "candidate")
        self.assertEqual(step["searchBoxes"]["topics"], "candidate", "the search box was cleared")

    def test_a_background_update_puts_the_scroll_position_back(self) -> None:
        grown = _state([_proposal(n) for n in range(1, 5)], [_blog("TASK-1", "First article")])
        step = self.steps({"steps": [{"do": "poll", "version": "v2", "state": grown}]})[0]

        self.assertTrue(step["scrolls"], "a background update never restored the scroll")

    def test_only_the_rows_that_changed_are_replaced(self) -> None:
        changed = _state(
            [_proposal(1), _proposal(2, title="Candidate topic 2 — reworded"), _proposal(3)],
            [_blog("TASK-1", "First article")],
        )
        step = self.steps({"steps": [{"do": "poll", "version": "v2", "state": changed}]})[0]

        before = {row["key"]: row["uid"] for row in step["rowsBefore"]["proposals"]}
        after = {row["key"]: row["uid"] for row in step["rowsAfter"]["proposals"]}

        self.assertEqual(sorted(before), ["1", "2", "3"], "the list was not rendered as keyed rows")
        self.assertEqual(before["1"], after["1"], "an unchanged row was rebuilt")
        self.assertEqual(before["3"], after["3"], "an unchanged row was rebuilt")
        self.assertNotEqual(before["2"], after["2"], "the changed row was not replaced")
        self.assertIn("reworded", step["proposalsHtml"])

    def test_a_removed_row_goes_and_a_new_row_arrives_in_order(self) -> None:
        changed = _state([_proposal(1), _proposal(4)], [_blog("TASK-1", "First article")])
        step = self.steps({"steps": [{"do": "poll", "version": "v2", "state": changed}]})[0]

        self.assertEqual([row["key"] for row in step["rowsAfter"]["proposals"]], ["1", "4"])

    # ---- work that arrived somewhere he is not looking ----------------------

    def test_a_card_on_another_tab_is_counted_not_jumped_to(self) -> None:
        arrived = _state(
            [_proposal(n) for n in range(1, 4)],
            [_blog("TASK-1", "First article"), _blog("TASK-2", "Written elsewhere")],
        )
        step = self.steps({"steps": [{"do": "poll", "version": "v2", "state": arrived}]})[0]

        badge = {item["view"]: item for item in step["badges"]}["blogs"]
        self.assertFalse(badge["hidden"], "a new article on another tab said nothing")
        self.assertEqual(badge["text"], "1")
        self.assertEqual(step["ui"]["blogs"]["page"], 1)

    def test_the_badge_clears_once_he_opens_that_tab(self) -> None:
        arrived = _state(
            [_proposal(n) for n in range(1, 4)],
            [_blog("TASK-1", "First article"), _blog("TASK-2", "Written elsewhere")],
        )
        steps = self.steps({
            "steps": [
                {"do": "poll", "version": "v2", "state": arrived},
                {"do": "showView", "view": "blogs"},
            ],
        })

        badge = {item["view"]: item for item in steps[1]["badges"]}["blogs"]
        self.assertTrue(badge["hidden"], "the count stayed up after he read it")

    def test_a_card_hidden_by_the_current_filter_is_offered_not_forced(self) -> None:
        many = _state([_proposal(n) for n in range(1, 30)], [_blog("TASK-1", "First article")])
        grown = _state([_proposal(n) for n in range(1, 31)], [_blog("TASK-1", "First article")])
        step = self.steps({
            "state": many,
            "ui": {"topics": {"page": 1, "size": 10, "search": "", "filter": "all"}},
            "steps": [{"do": "poll", "version": "v2", "state": grown}],
        })[0]

        self.assertFalse(step["topicsNewHidden"], "a candidate on page three arrived silently")
        self.assertIn("1 new", step["topicsNew"])
        self.assertIn('data-arrivals="topics"', step["topicsNew"])
        self.assertEqual(step["ui"]["topics"]["page"], 1, "he was moved to where the new one is")

    # ---- invariant 6: restraint --------------------------------------------

    def test_a_hidden_tab_is_not_polled(self) -> None:
        step = self.steps({"steps": [{"do": "poll", "hidden": True, "version": "v2"}]})[0]

        self.assertNotIn("/ceo/api/version", " ".join(step["requests"]),
                         "a tab nobody is looking at was still polled")
        self.assertFalse(step["pollActive"], "the poller kept a timer alive while hidden")

    def test_coming_back_to_the_tab_checks_at_once(self) -> None:
        steps = self.steps({
            "steps": [
                {"do": "poll", "hidden": True},
                {"do": "fire", "event": "visibilitychange", "hidden": False},
            ],
        })

        self.assertFalse(steps[0]["pollActive"])
        self.assertTrue(steps[1]["pollActive"], "returning to the tab did not restart the poller")
        self.assertEqual(steps[1]["pollDelay"], 3000)

    # ---- invariant 7: one mechanism, and it backs off ----------------------

    def test_the_interval_climbs_on_failure_and_resets_on_the_first_success(self) -> None:
        steps = self.steps({
            "steps": [
                {"name": "fail 1", "do": "poll", "fail": {"path": "/ceo/api/version", "status": 502,
                                                          "error": "gateway"}},
                {"name": "fail 2", "do": "poll"},
                {"name": "fail 3", "do": "poll"},
                {"name": "fail 4", "do": "poll"},
                {"name": "recover", "do": "poll", "fail": None},
            ],
        })

        self.assertEqual([step["pollDelay"] for step in steps], [6000, 12000, 30000, 30000, 3000])

    def test_a_failing_poll_never_disturbs_what_is_on_screen(self) -> None:
        steps = self.steps({
            "steps": [
                {"do": "poll"},
                {"do": "poll", "fail": {"path": "/ceo/api/version", "status": 502, "error": "gateway"}},
            ],
        })

        self.assertEqual(steps[0]["rowsAfter"]["proposals"], steps[1]["rowsAfter"]["proposals"])

    def test_an_action_in_flight_is_never_interrupted_by_a_poll(self) -> None:
        # The propose call hangs; the poll that lands on top of it must stand down
        # rather than refetch state underneath a running action.
        steps = self.steps({
            "steps": [
                {"do": "research", "subject": "battery data", "hang": "/ceo/api/propose"},
                {"do": "poll", "version": "v2"},
            ],
        })

        self.assertNotIn("/ceo/api/version", " ".join(steps[1]["requests"]))
        self.assertNotIn("/ceo/api/state", " ".join(steps[1]["requests"]))

    def test_boot_reads_the_token_before_the_state_and_then_polls(self) -> None:
        requests = self.drive({"steps": []})["requests"]

        self.assertEqual(requests[0], "/api/session")
        self.assertEqual(requests[1], "/ceo/api/version")
        self.assertTrue(requests[2].startswith("/ceo/api/state"))
        self.assertEqual(len(requests), 3, f"boot made an extra request: {requests}")


if __name__ == "__main__":
    unittest.main()
