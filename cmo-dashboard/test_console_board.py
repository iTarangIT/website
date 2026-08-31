"""What reaches the Blogs tab, and what must not.

The tab's contents come from one filter in `console_board.read_board()`, and until
now nothing tested it — the console render suites feed a synthetic `blogs` list, so
they would stay green no matter what the filter admitted. That is how a 61-word
internal board-state summary came to sit on the Blogs tab: it is written by the
content skill, it lands in artifacts/ like an article, and every other condition
passed. ContentRuntime._select() already refuses that work type; this suite pins
the two to the same answer.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import console_board

BOARD_HEAD = """# iTarang CMO Task Board

## Backlog

## In Progress

## CMO Review

## Human Approval

"""

BOARD_TAIL = "## Completed\n"


def _card(task_id: str, title: str, *, skill: str = "content", work_type: str = "",
          attachment: str = "", section: str = "Human Approval", change_status: str = "",
          topic_stage: str = "approved", research_brief: str = "", extra: str = "") -> str:
    lines = [
        f"### {task_id} — {title}",
        f"- ID: {task_id}",
        f"- Title: {title}",
        f"- Owner: {skill}",
        f"- Skill: {skill}",
        "- Priority: medium",
        f"- Status: {section}",
        f"- Attachment: {attachment or 'none'}",
        "- Metric: Organic sessions",
        "- Tag: action to be taken by: human",
        "- Revision round: 0",
        f"- Topic stage: {topic_stage}",
        "- Last updated: 2026-08-11T00:00:00Z",
        "- Updated: 2026-08-11T00:00:00Z",
    ]
    if change_status:
        lines.append(f"- Change status: {change_status}")
    if research_brief:
        lines.append(f"- Research brief: {research_brief}")
    if work_type:
        lines.append(f"- Work type: {work_type}")
    if extra:
        lines.append(extra)
    return "\n".join(lines) + "\n"


#: The card's own Status field names the section it belongs under, and `build`
#: files it there — otherwise every fixture card lands in whichever heading came
#: last, and "queued" and "being written" become indistinguishable.
SECTIONS = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")


ARTICLE = """---
title: Battery replacement, city by city
slug: battery-replacement
category: financing
---

# Battery replacement, city by city

A rider asking about replacement cost wants one number.

## Decision bullets:

- **Measure first.** Check Search Console before commissioning more pages.
"""


class BlogsTab(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "artifacts").mkdir()
        (self.root / "state").mkdir()

    def write_board(self, *cards: str) -> Path:
        grouped = {name: [] for name in SECTIONS}
        for text in cards:
            section = next(
                (line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("- Status: ")),
                "Human Approval",
            )
            grouped[section].append(text)
        body = "# iTarang CMO Task Board\n\n"
        for name in SECTIONS:
            body += f"## {name}\n\n" + "\n".join(grouped[name]) + "\n"
        board = self.root / "tasks.md"
        board.write_text(body, encoding="utf-8")
        return board

    def build(self, *cards: str) -> list[dict]:
        return console_board.read_board(self.write_board(*cards), self.root)["blogs"]

    def state(self, *cards: str, approved: str = "") -> dict:
        """`approved` records a Gate 1 approval the way `DecisionStore` would.

        Written straight to the file `decisions.decision_record` reads, because
        `DecisionStore.decide` also enforces the lane and the fingerprint -- rules
        of its own that these cases are not about.
        """
        if approved:
            state_dir = self.root / "state"
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "human-approvals.json").write_text(
                json.dumps({approved: {
                    "task_id": approved,
                    "decision": "approve",
                    "approver_id": "ceo@itarang.com",
                    "surface": "dashboard",
                    "timestamp": "2026-08-11T00:00:00Z",
                    "commit_sha": "",
                    "send_back_text": "",
                }}),
                encoding="utf-8",
            )
        blogs = self.build(*cards)
        return {task["id"]: task["blog"] for task in blogs}

    def article(self, task_id: str) -> str:
        name = f"{task_id}-content.md"
        (self.root / "artifacts" / name).write_text(ARTICLE, encoding="utf-8")
        return f"artifacts/{name}"

    def test_a_written_content_card_reaches_the_tab(self) -> None:
        blogs = self.build(_card("TASK-100", "A real article", attachment=self.article("TASK-100")))

        self.assertEqual([task["id"] for task in blogs], ["TASK-100"])

    def test_an_internal_board_summary_never_reaches_the_tab(self) -> None:
        # Content skill, real artifact, every other condition satisfied — and still
        # not a blog. This is the card that was actually on the tab.
        blogs = self.build(
            _card("TASK-069", "Produce a verified internal board-state summary",
                  work_type="internal-board-summary", attachment=self.article("TASK-069")),
            _card("TASK-100", "A real article", attachment=self.article("TASK-100")),
        )

        self.assertEqual([task["id"] for task in blogs], ["TASK-100"])

    def test_a_commissioning_card_never_reaches_the_tab(self) -> None:
        blogs = self.build(
            _card("TASK-066", "Commission task-file write",
                  work_type="commissioning", attachment=self.article("TASK-066")),
        )

        self.assertEqual(blogs, [])

    def test_an_unwritten_content_card_reaches_the_tab_with_a_status(self) -> None:
        """Invariant 5. This used to be the opposite assertion.

        A card with no artifact was kept off the tab on the grounds that it was a
        topic rather than an article. What that actually produced was a console
        that showed nothing for the several minutes between approving a topic and
        reading the result — and showed nothing at all for TASK-084, whose nine
        writer attempts all failed while the card sat looking untouched.
        """
        blogs = self.build(
            _card("TASK-084", "E-Rickshaw Battery Repair or Replacement", section="Backlog")
        )

        self.assertEqual([task["id"] for task in blogs], ["TASK-084"])
        self.assertEqual(blogs[0]["blog"]["state"], "queued")
        self.assertEqual(blogs[0]["blog"]["label"], "Draft — queued to be written")

    def test_a_card_from_another_skill_does_not_reach_the_tab(self) -> None:
        blogs = self.build(
            _card("TASK-082", "Install the GA4 measurement tag", skill="ops",
                  attachment=self.article("TASK-082")),
        )

        self.assertEqual(blogs, [])

    def test_the_tab_the_writer_and_the_worker_refuse_the_same_work_types(self) -> None:
        # This used to scrape the literal set out of _select()'s source, which drifted
        # the moment the set was named. There is now one object, and all three import
        # it — so the check is identity, and there is nothing left to keep in step.
        from cmo_runtime import content_flow, content_worker

        self.assertIs(console_board.NON_ARTICLE_WORK_TYPES, content_flow.NON_ARTICLE_WORK_TYPES)
        self.assertIs(content_worker.NON_ARTICLE_WORK_TYPES, content_flow.NON_ARTICLE_WORK_TYPES)
        self.assertTrue(content_flow.NON_ARTICLE_WORK_TYPES)


class WhatEachStateSays(BlogsTab):
    """One row per line of the status table Sanchit was promised.

    These assert the words, not the codes. "Could not be written" with the writer's
    own reason under it is the whole point of the failed row; a state name nobody
    reads would satisfy an enum test and tell him nothing.
    """

    def test_an_approved_topic_waiting_its_turn(self) -> None:
        blog = self.state(_card("TASK-088", "Queued behind another", section="Backlog"))["TASK-088"]

        self.assertEqual(blog["label"], "Draft — queued to be written")
        self.assertFalse(blog["retryable"])

    def test_a_run_that_is_still_gathering_sources(self) -> None:
        blog = self.state(
            _card("TASK-084", "Being researched", section="In Progress", change_status="executing")
        )["TASK-084"]

        self.assertEqual(blog["state"], "researching")
        self.assertEqual(blog["label"], "Draft — researching…")

    def test_a_run_that_has_its_sources_and_is_writing(self) -> None:
        (self.root / "artifacts" / "TASK-084-research.md").write_text("# brief\n", encoding="utf-8")
        blog = self.state(
            _card("TASK-084", "Being written", section="In Progress", change_status="executing",
                  research_brief="artifacts/TASK-084-research.md")
        )["TASK-084"]

        self.assertEqual(blog["state"], "writing")
        self.assertEqual(blog["label"], "Draft — writing…")

    def test_the_elapsed_clock_starts_from_the_worker_heartbeat(self) -> None:
        (self.root / "state" / "content-worker.json").write_text(
            '{"pid": 1, "task_id": "TASK-084", "kind": "write", '
            '"started_at": "2026-08-12T07:00:00Z", "updated_at": "2026-08-12T07:00:05Z"}',
            encoding="utf-8",
        )
        blog = self.state(
            _card("TASK-084", "Being researched", section="In Progress", change_status="executing")
        )["TASK-084"]

        self.assertEqual(blog["started_at"], "2026-08-12T07:00:00Z")

    def test_a_failed_write_says_so_and_carries_the_writers_reason(self) -> None:
        """Invariant 4. The reason is the writer's own sentence, verbatim."""
        blog = self.state(
            _card("TASK-084", "Failed nine times", section="Backlog", change_status="write failed",
                  extra="- Latest summary: writer article has 1742 words; WRITER_CONTRACT requires 900–1,400")
        )["TASK-084"]

        self.assertEqual(blog["state"], "failed")
        self.assertEqual(blog["label"], "Could not be written")
        self.assertIn("1742 words", blog["reason"])
        self.assertTrue(blog["retryable"])

    def test_queued_means_the_worker_will_actually_take_it(self) -> None:
        """A commissioning card read "Queued to be written" on the live board.

        The worker refuses it twice over — the change status is one it will not
        touch and there is no approved topic stage — so the row was promising a
        write that could never start. The tab and the worker now answer from the
        same rule.
        """
        blog = self.state(
            _card("TASK-066", "Commission task-file write", section="Backlog",
                  change_status="commissioning", topic_stage="",
                  extra="- Latest summary: Commissioning evidence card, not an article")
        )["TASK-066"]

        self.assertEqual(blog["state"], "held")
        self.assertNotEqual(blog["label"], "Draft — queued to be written")

    def test_a_backlog_card_with_no_approved_topic_is_not_queued(self) -> None:
        blog = self.state(
            _card("TASK-090", "A topic nobody approved", section="Backlog", topic_stage="proposed")
        )["TASK-090"]

        self.assertEqual(blog["state"], "held")

    def test_the_tab_and_the_worker_agree_on_what_is_queued(self) -> None:
        """Rule identity, not two copies of a rule that will drift apart."""
        from pathlib import Path

        from cmo_runtime.agent_runtime import BoardStore
        from cmo_runtime.content_worker import eligible_cards

        board = self.write_board(
            _card("TASK-100", "Genuinely queued", section="Backlog", change_status="queued"),
            _card("TASK-066", "Commissioning", section="Backlog", change_status="commissioning",
                  topic_stage=""),
            _card("TASK-085", "Held", section="Backlog", change_status="blocked"),
        )
        queued_on_tab = {
            task["id"] for task in console_board.read_board(board, self.root)["blogs"]
            if task["blog"]["state"] == "queued"
        }
        queued_for_worker = {card.task_id for card in eligible_cards(BoardStore(Path(self.root)).cards())}

        self.assertEqual(queued_on_tab, queued_for_worker)
        self.assertEqual(queued_on_tab, {"TASK-100"})

    def test_a_card_a_human_held_is_not_offered_a_retry(self) -> None:
        """`blocked` is somebody's decision. Only a failure nobody chose retries."""
        blog = self.state(
            _card("TASK-085", "Held behind TASK-084", section="Backlog", change_status="blocked",
                  extra="- Latest summary: Held behind TASK-084 by CEO instruction on 2026-08-12")
        )["TASK-085"]

        self.assertEqual(blog["state"], "held")
        self.assertEqual(blog["label"], "On hold")
        self.assertFalse(blog["retryable"])
        self.assertIn("CEO instruction", blog["reason"])

    def test_a_card_in_cmo_review_is_being_checked(self) -> None:
        blog = self.state(
            _card("TASK-084", "Written, under review", section="CMO Review",
                  attachment=self.article("TASK-084"), change_status="pending CMO review")
        )["TASK-084"]

        self.assertEqual(blog["label"], "Waiting for review")

    def test_a_card_in_human_approval_is_awaiting_him(self) -> None:
        blog = self.state(
            _card("TASK-084", "Ready to read", attachment=self.article("TASK-084"))
        )["TASK-084"]

        self.assertEqual(blog["label"], "Waiting for review")

    def test_a_card_he_asked_changes_on_is_being_rewritten(self) -> None:
        blog = self.state(
            _card("TASK-084", "Comment submitted", attachment=self.article("TASK-084"),
                  change_status="revision requested").replace(
                "- Revision round: 0", "- Revision round: 1")
        )["TASK-084"]

        self.assertEqual(blog["state"], "rewriting")
        self.assertEqual(blog["label"], "Being edited")

    def test_a_legacy_revision_marker_does_not_promise_a_rewrite(self) -> None:
        """`revision requested` with no round is the word for a request, not one.

        The worker refuses such a card — there is nothing recorded to rewrite
        towards — so saying "Being rewritten" would promise something that is
        never coming. The card reads as what it is: sitting in the lane it is in.
        """
        blog = self.state(
            _card("TASK-037", "A marker from before the revision flow", section="CMO Review",
                  attachment=self.article("TASK-037"), change_status="revision requested")
        )["TASK-037"]

        self.assertNotEqual(blog["state"], "rewriting")
        self.assertEqual(blog["label"], "Waiting for review")

    def test_a_running_revision_still_reads_as_being_rewritten(self) -> None:
        blog = self.state(
            _card("TASK-084", "Rewrite running", section="In Progress",
                  attachment=self.article("TASK-084"), change_status="executing revision")
        )["TASK-084"]

        self.assertEqual(blog["label"], "Being edited")

    def test_an_approved_card_with_a_future_date_is_scheduled(self) -> None:
        """A day a human wrote down. Nothing fires on it -- there is no scheduler
        on this box -- so the label is a plan, and Publish is still a press."""
        blog = self.state(
            _card("TASK-084", "Planned", attachment=self.article("TASK-084"),
                  extra="- Publish at: 2099-09-02"),
            approved="TASK-084",
        )["TASK-084"]

        self.assertEqual(blog["state"], "scheduled")
        self.assertEqual(blog["label"], "Scheduled — 2099-09-02")

    def test_a_date_that_has_passed_is_not_still_scheduled(self) -> None:
        """Nothing published it, because nothing publishes on its own. Saying
        "Scheduled" would claim a plan that is still running."""
        blog = self.state(
            _card("TASK-084", "Missed", attachment=self.article("TASK-084"),
                  extra="- Publish at: 2020-01-02"),
            approved="TASK-084",
        )["TASK-084"]

        self.assertEqual(blog["state"], "approved")
        self.assertIn("2020-01-02", blog["reason"])

    def test_an_unreadable_publish_date_is_not_a_state(self) -> None:
        """Scheduled with no day behind it promises something nobody wrote down."""
        blog = self.state(
            _card("TASK-084", "Cleared", attachment=self.article("TASK-084"),
                  extra="- Publish at: not scheduled"),
            approved="TASK-084",
        )["TASK-084"]

        self.assertEqual(blog["state"], "approved")

    def test_a_publish_date_on_an_unapproved_card_is_not_scheduled(self) -> None:
        """A publish date on something nobody agreed to publish is not a plan."""
        blog = self.state(
            _card("TASK-084", "Premature", section="CMO Review",
                  attachment=self.article("TASK-084"),
                  extra="- Publish at: 2099-09-02")
        )["TASK-084"]

        self.assertEqual(blog["state"], "checking")

    def test_a_card_on_the_branch_is_in_preview_not_live(self) -> None:
        """`published to cmo-changes` is the preview branch, and it read "Live on
        the site" -- a merge nobody had done yet, asserted on the screen."""
        blog = self.state(
            _card("TASK-084", "On cmo-changes", attachment=self.article("TASK-084"),
                  change_status="published to cmo-changes",
                  extra="- Preview URL: https://itarangwebsite.vercel.app/blog/battery-replacement")
        )["TASK-084"]

        self.assertEqual(blog["state"], "in_preview")
        self.assertEqual(blog["label"], "In preview")
        self.assertEqual(blog["url"], "https://itarangwebsite.vercel.app/blog/battery-replacement")

    def test_only_a_merge_to_main_reads_as_published(self) -> None:
        """The other half of the same bug: a genuinely live article read
        "Approved", because nothing recognised the status Gate 2 writes."""
        blog = self.state(
            _card("TASK-084", "Merged", attachment=self.article("TASK-084"),
                  change_status="merged to main")
        )["TASK-084"]

        self.assertEqual(blog["state"], "published")
        self.assertEqual(blog["label"], "Published")

    def test_a_completed_card_is_published_not_awaiting_him(self) -> None:
        """`Completed` fell through to the default and read "Awaiting you"."""
        blog = self.state(
            _card("TASK-084", "Done", section="Completed",
                  attachment=self.article("TASK-084"))
        )["TASK-084"]

        self.assertEqual(blog["state"], "published")


class PublishFingerprint(BlogsTab):
    """What "nothing changed since approval" is actually checking."""

    def task(self, *cards: str) -> dict:
        board = self.write_board(*cards)
        return console_board.read_board(board, self.root)["blogs"][0]

    def test_the_same_card_and_article_fingerprint_the_same(self) -> None:
        card = _card("TASK-084", "Ready", attachment=self.article("TASK-084"),
                     extra="- Category: financing")
        first = console_board.publish_fingerprint(self.task(card), self.root)
        second = console_board.publish_fingerprint(self.task(card), self.root)

        self.assertEqual(first, second)

    def test_editing_the_article_changes_the_fingerprint(self) -> None:
        card = _card("TASK-084", "Ready", attachment=self.article("TASK-084"),
                     extra="- Category: financing")
        before = console_board.publish_fingerprint(self.task(card), self.root)
        (self.root / "artifacts" / "TASK-084-content.md").write_text(
            ARTICLE + "\nOne more paragraph nobody approved.\n", encoding="utf-8"
        )

        self.assertNotEqual(console_board.publish_fingerprint(self.task(card), self.root), before)

    def test_changing_the_category_changes_the_fingerprint(self) -> None:
        attachment = self.article("TASK-084")
        before = console_board.publish_fingerprint(
            self.task(_card("TASK-084", "Ready", attachment=attachment, extra="- Category: financing")),
            self.root,
        )
        after = console_board.publish_fingerprint(
            self.task(_card("TASK-084", "Ready", attachment=attachment, extra="- Category: safety")),
            self.root,
        )

        self.assertNotEqual(after, before)

    def test_a_reworded_summary_does_not_change_the_fingerprint(self) -> None:
        """The hourly cycle rewrites summaries. That is not a reason to refuse."""
        attachment = self.article("TASK-084")
        before = console_board.publish_fingerprint(
            self.task(_card("TASK-084", "Ready", attachment=attachment, extra="- Category: financing")),
            self.root,
        )
        after = console_board.publish_fingerprint(
            self.task(
                _card("TASK-084", "Ready", attachment=attachment,
                      extra="- Category: financing\n- Latest summary: reworded by the hourly cycle")
            ),
            self.root,
        )

        self.assertEqual(after, before)


class ExcerptTruncation(unittest.TestCase):
    """A retained excerpt is cut without severing its Markdown.

    `test_ceo_reader.py` renders every artifact in the live profile and fails on
    raw Markdown. A flat character cut through `**bold**` put two literal asterisks
    into TASK-084's research brief and turned that suite red — from scraped source
    text, not from anything the writer produced.
    """

    def truncate(self, text: str, limit: int) -> str:
        from cmo_runtime.content_flow import _truncate_excerpt

        return _truncate_excerpt(text, limit)

    def test_short_text_is_returned_untouched(self) -> None:
        self.assertEqual(self.truncate("a short page", 3000), "a short page")

    def test_a_cut_through_bold_does_not_leave_a_dangling_marker(self) -> None:
        text = "x" * 40 + "\n" + "keep this line\n" + "**India E-Rickshaw Market Driver:**" + "y" * 200
        result = self.truncate(text, 60)

        self.assertEqual(result.count("**") % 2, 0, "an unpaired ** survived the cut")
        self.assertIn("[Excerpt truncated in retained brief.]", result)

    def test_the_cut_prefers_a_line_boundary(self) -> None:
        text = "first line\nsecond line\nthird line that runs past the limit\n"
        result = self.truncate(text, 30)

        self.assertTrue(result.startswith("first line\nsecond line"))
        self.assertNotIn("third line", result)

    def test_one_very_long_line_is_still_retained(self) -> None:
        # No newline to cut on: keep the budget rather than throw the page away.
        result = self.truncate("z" * 5000, 3000)

        self.assertGreater(len(result), 2900)

    def test_a_severed_bold_never_reaches_the_reader(self) -> None:
        # The production shape: prose with bold runs, cut mid-marker. This is what
        # put "**R" into TASK-084's brief and turned test_ceo_reader.py red.
        import ceo_reader

        text = (
            "India E-Rickshaw Market Driver\n"
            "Growth is driven by **low running cost** and rising demand.\n"
            "**Market Restraint:** charging access is uneven across states.\n"
        )
        for limit in range(40, len(text)):
            with self.subTest(limit=limit):
                rendered = ceo_reader.render_markdown_fragment(self.truncate(text, limit))
                self.assertNotIn("**", rendered, "bold survived as asterisks")


if __name__ == "__main__":
    unittest.main()
