"""Cross-posting a published article: the gate, the drafts, and a partial send.

Nothing here reaches Buffer. A fake client stands in, so a failure means the
console's own logic moved and never means a network was down. What is asserted is
the behaviour the feature exists for:

* an article a reader cannot open yet is not sendable, and the screen says why;
* an instruction is single-use, and a replay never reaches the fake;
* three platforms are three independent calls, so one refusal does not cost the
  other two — and the result says which went and which did not;
* a queued row is not offered again, and regenerating copy does not clear it.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import ceo_social
from ceo_publish import PublicationConflict, PublicationRefused
from cmo_runtime.buffer_client import BufferChannel, BufferPost, BufferRefused
from cmo_runtime.console_db import ConsoleDB

ARTICLE = """---
title: What an e-rickshaw battery costs to replace
meta_title: E-rickshaw battery replacement cost
meta_description: A replacement pack is rarely the whole bill, and the rest is predictable.
slug: battery-replacement-cost
category: financing
audience: fleet operators
source_urls: https://example.org/source
---

# What an e-rickshaw battery costs to replace

A replacement pack is rarely the whole bill. Labour and downtime move the number
by a third. Operators who budget for the pack alone borrow twice.
"""


def card(change_status: str, section: str) -> str:
    lines = [
        "### TASK-900 — What an e-rickshaw battery costs to replace",
        "- ID: TASK-900",
        "- Title: What an e-rickshaw battery costs to replace",
        "- Owner: content",
        "- Skill: content",
        "- Priority: medium",
        f"- Status: {section}",
        "- Attachment: artifacts/TASK-900-content.md",
        "- Category: financing",
        "- Change type: website",
        f"- Change status: {change_status}",
        "- Preview URL: https://itarangwebsite.vercel.app/blog/battery-replacement-cost",
        "- Topic keywords: battery replacement cost, e-rickshaw finance",
        "- Metric: Organic sessions",
        "- Tag: action to be taken by: human",
        "- Revision round: 0",
        "- Completed date: not completed",
        "- Last updated: 2026-08-11T00:00:00Z",
        "- Updated: 2026-08-11T00:00:00Z",
    ]
    return "\n".join(lines) + "\n"


def board(change_status: str = "merged to main", section: str = "Completed") -> str:
    body = card(change_status, section)
    sections = {name: "_No tasks._\n" for name in
                ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")}
    sections[section] = body
    return "# CMO Task Board\n\n" + "\n".join(
        f"## {name}\n\n{sections[name]}" for name in
        ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")
    )


class FakeBuffer:
    """Answers like Buffer, and records exactly what it was asked to post."""

    def __init__(self, *, refuse: set[str] | None = None, channels: list[str] | None = None):
        self.refuse = refuse or set()
        self.posted: list[dict] = []
        self._channels = channels if channels is not None else ["linkedin", "x", "instagram"]

    def channels(self) -> list[BufferChannel]:
        return [
            BufferChannel(
                id=platform[0] * 24,
                name=platform.title(),
                service="twitter" if platform == "x" else platform,
                platform=platform,
                disconnected=False,
                locked=False,
                queue_paused=False,
            )
            for platform in self._channels
        ]

    def create_post(self, *, channel_id, platform, text, link="", image_url="",
                    image_alt="", thread=(), mode="addToQueue"):
        self.posted.append(
            {"platform": platform, "text": text, "link": link,
             "image_url": image_url, "thread": list(thread), "mode": mode}
        )
        if platform in self.refuse:
            raise BufferRefused(f"Buffer would not take the {platform} post.")
        return BufferPost(
            id=platform[0] * 24, status="queued", platform=platform,
            due_at="2026-09-01T10:00:00Z", text=text,
        )


class SocialFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)

        self.profile = root / "profile"
        (self.profile / "artifacts").mkdir(parents=True)
        (self.profile / "state").mkdir()
        (self.profile / "logs").mkdir()
        (self.profile / "tasks.md").write_text(board(), encoding="utf-8")
        (self.profile / "artifacts/TASK-900-content.md").write_text(ARTICLE, encoding="utf-8")

        self.website = root / "website"
        (self.website / "public/images/blog").mkdir(parents=True)
        (self.website / "public/images/blog/battery-replacement-cost-cover.webp").write_bytes(b"RIFFfake")

        self.buffer = FakeBuffer()

    # ---- helpers ---------------------------------------------------------

    def preflight(self, **overrides):
        options = {
            "website_root": self.website,
            "client": self.buffer,
            "check_live": False,
        }
        options.update(overrides)
        return ceo_social.preflight(self.profile, "TASK-900", **options)

    def generate(self):
        return ceo_social.generate(
            self.profile, "TASK-900", actor="ceo@itarang.test", website_root=self.website
        )

    def send(self, platforms=("linkedin", "x", "instagram"), **overrides):
        check = self.preflight()
        request_id = ceo_social.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test",
            fingerprint=check.fingerprint, platforms=check.sendable,
        )
        options = {
            "actor": "ceo@itarang.test",
            "role": "ceo",
            "request_id": request_id,
            "platforms": list(platforms),
            "website_root": self.website,
            "client": self.buffer,
            "check_live": False,
        }
        options.update(overrides)
        return request_id, ceo_social.send(self.profile, "TASK-900", **options)

    def drafts(self) -> dict[str, dict]:
        database = ConsoleDB(self.profile)
        try:
            return {row["platform"]: row for row in database.crosspost_drafts("TASK-900")}
        finally:
            database.close()


class TheGate(SocialFixture):
    def test_an_article_that_is_not_live_cannot_be_sent_and_the_reason_is_a_sentence(self):
        """A social post is a link. This is the whole reason the tab waits for Gate 2."""
        (self.profile / "tasks.md").write_text(
            board(change_status="published to cmo-changes", section="Human Approval"),
            encoding="utf-8",
        )
        check = self.preflight()
        self.assertFalse(check.eligible)
        self.assertTrue(any("not live yet" in blocker for blocker in check.blockers))
        self.assertEqual(self.buffer.posted, [])

    def test_a_live_url_that_does_not_answer_blocks_the_send(self):
        """Merged is not deployed. Asking the site is the difference."""
        def dead(request, timeout=0):
            raise OSError("connection refused")

        self.generate()
        check = self.preflight(check_live=True, opener=dead)
        self.assertFalse(check.eligible)
        self.assertTrue(any("did not answer" in blocker for blocker in check.blockers))

    def test_a_live_url_that_answers_unblocks_the_send(self):
        """The other half of the check: proving the refusal is not unconditional."""

        class Answered:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exception):
                return False

        asked = []

        def alive(request, timeout=0):
            asked.append(request.full_url)
            return Answered()

        self.generate()
        check = self.preflight(check_live=True, opener=alive)
        self.assertTrue(check.eligible, check.blockers)
        self.assertEqual(asked, ["https://itarang.com/blog/battery-replacement-cost"])

    def test_an_article_with_no_cover_cannot_go_to_instagram_but_can_go_elsewhere(self):
        (self.website / "public/images/blog/battery-replacement-cost-cover.webp").unlink()
        self.generate()
        check = self.preflight()
        self.assertEqual(check.sendable, ["linkedin", "x"])
        self.assertTrue(any("Instagram requires a picture" in note for note in check.notes))
        self.assertTrue(check.eligible, "the other two are still sendable")

    def test_an_svg_cover_is_refused_for_instagram_by_name(self):
        (self.website / "public/images/blog/battery-replacement-cost-cover.webp").unlink()
        (self.website / "public/images/blog/battery-replacement-cost-cover.svg").write_text("<svg/>")
        self.generate()
        check = self.preflight()
        self.assertNotIn("instagram", check.sendable)
        self.assertTrue(any("SVG" in note for note in check.notes))

    def test_a_platform_with_no_connected_channel_is_named_not_silently_dropped(self):
        self.buffer = FakeBuffer(channels=["linkedin"])
        self.generate()
        check = self.preflight()
        self.assertEqual(check.sendable, ["linkedin"])
        self.assertIn("No usable x channel is connected in Buffer.", check.notes)

    def test_nothing_is_sendable_before_any_copy_exists(self):
        check = self.preflight()
        self.assertEqual(check.sendable, [])
        self.assertFalse(check.eligible)
        self.assertIn("No copy has been written for this article yet.", check.notes)


class TheDrafts(SocialFixture):
    def test_generating_writes_one_draft_per_platform(self):
        self.generate()
        drafts = self.drafts()
        self.assertEqual(sorted(drafts), ["instagram", "linkedin", "x"])
        self.assertEqual({row["status"] for row in drafts.values()}, {"draft"})

    def test_the_three_drafts_are_three_different_pieces_of_writing(self):
        self.generate()
        bodies = {row["body"] for row in self.drafts().values()}
        self.assertEqual(len(bodies), 3)

    def test_the_x_draft_stores_its_thread(self):
        self.generate()
        self.assertGreater(len(self.drafts()["x"]["thread"]), 1)

    def test_a_human_edit_replaces_the_copy(self):
        self.generate()
        ceo_social.save_draft(
            self.profile, "TASK-900", platform="linkedin",
            body="My own words about the bill.", actor="ceo@itarang.test",
        )
        self.assertEqual(self.drafts()["linkedin"]["body"], "My own words about the bill.")

    def test_an_edit_over_the_platform_limit_is_refused_here_not_by_buffer(self):
        self.generate()
        with self.assertRaises(PublicationRefused) as caught:
            ceo_social.save_draft(
                self.profile, "TASK-900", platform="x",
                body="w" * 400, actor="ceo@itarang.test",
            )
        self.assertIn("280", str(caught.exception))

    def test_a_queued_post_cannot_be_edited_here(self):
        self.generate()
        self.send()
        with self.assertRaises(PublicationConflict) as caught:
            ceo_social.save_draft(
                self.profile, "TASK-900", platform="linkedin",
                body="Second thoughts.", actor="ceo@itarang.test",
            )
        self.assertIn("edit it there", str(caught.exception).lower())

    def test_regenerating_copy_does_not_forget_that_a_post_was_sent(self):
        """LinkedIn holds the post either way; a console that forgot would double it."""
        self.generate()
        self.send()
        self.generate()
        drafts = self.drafts()
        self.assertEqual(drafts["linkedin"]["status"], "queued")
        self.assertTrue(drafts["linkedin"]["buffer_post_id"])


class TheSend(SocialFixture):
    def test_a_send_queues_one_buffer_post_per_platform(self):
        self.generate()
        _, result = self.send()
        self.assertEqual(result["result"], "queued")
        self.assertEqual(
            [post["platform"] for post in self.buffer.posted], ["linkedin", "x", "instagram"]
        )
        self.assertEqual({row["status"] for row in self.drafts().values()}, {"queued"})

    def test_instagram_is_sent_the_public_cover_url_and_the_others_are_not(self):
        self.generate()
        self.send()
        by_platform = {post["platform"]: post for post in self.buffer.posted}
        self.assertIn(
            "/images/blog/battery-replacement-cost-cover.webp", by_platform["instagram"]["image_url"]
        )
        self.assertEqual(by_platform["linkedin"]["image_url"], "")

    def test_the_queued_row_records_the_buffer_post_and_who_pressed_the_button(self):
        self.generate()
        self.send()
        row = self.drafts()["linkedin"]
        self.assertTrue(row["buffer_post_id"])
        self.assertEqual(row["sent_by"], "ceo@itarang.test")
        self.assertEqual(row["scheduled_at"], "2026-09-01T10:00:00Z")

    def test_one_platforms_refusal_does_not_cost_the_other_two(self):
        """Three calls, no transaction. Reporting one failure as total would be a lie."""
        self.buffer = FakeBuffer(refuse={"x"})
        self.generate()
        _, result = self.send()
        self.assertEqual(result["result"], "partial")
        self.assertEqual([post["platform"] for post in result["queued"]], ["linkedin", "instagram"])
        self.assertEqual([item["platform"] for item in result["failed"]], ["x"])
        drafts = self.drafts()
        self.assertEqual(drafts["linkedin"]["status"], "queued")
        self.assertEqual(drafts["x"]["status"], "failed")

    def test_a_refusal_keeps_buffers_own_words_on_the_row(self):
        self.buffer = FakeBuffer(refuse={"instagram"})
        self.generate()
        self.send()
        self.assertIn("would not take the instagram post", self.drafts()["instagram"]["error"])

    def test_an_instruction_is_single_use_and_a_replay_never_reaches_buffer(self):
        self.generate()
        request_id, _ = self.send()
        before = len(self.buffer.posted)
        with self.assertRaises(PublicationConflict):
            ceo_social.send(
                self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
                request_id=request_id, platforms=["linkedin"],
                website_root=self.website, client=self.buffer, check_live=False,
            )
        self.assertEqual(len(self.buffer.posted), before, "a replay reached Buffer")

    def test_an_instruction_issued_for_someone_else_is_refused(self):
        self.generate()
        check = self.preflight()
        request_id = ceo_social.issue_request(
            self.profile, "TASK-900", actor="someone@else.test",
            fingerprint=check.fingerprint, platforms=check.sendable,
        )
        with self.assertRaises(PublicationConflict):
            ceo_social.send(
                self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
                request_id=request_id, platforms=["linkedin"],
                website_root=self.website, client=self.buffer, check_live=False,
            )
        self.assertEqual(self.buffer.posted, [])

    def test_an_article_edited_after_the_instruction_was_issued_is_refused(self):
        self.generate()
        check = self.preflight()
        request_id = ceo_social.issue_request(
            self.profile, "TASK-900", actor="ceo@itarang.test",
            fingerprint="a-fingerprint-from-before", platforms=check.sendable,
        )
        with self.assertRaises(PublicationConflict) as caught:
            ceo_social.send(
                self.profile, "TASK-900", actor="ceo@itarang.test", role="ceo",
                request_id=request_id, platforms=["linkedin"],
                website_root=self.website, client=self.buffer, check_live=False,
            )
        self.assertIn("changed after this instruction", str(caught.exception))
        self.assertEqual(self.buffer.posted, [])

    def test_a_platform_that_is_already_queued_cannot_be_sent_again(self):
        self.generate()
        self.send()
        check = self.preflight()
        self.assertEqual(check.sendable, [], "a queued post was offered a second time")

    def test_the_send_is_written_into_the_approvals_log(self):
        self.generate()
        self.send()
        log = (self.profile / "logs" / "approvals.log").read_text(encoding="utf-8")
        self.assertIn('"event": "social-crosspost"', log)
        self.assertIn("ceo@itarang.test", log)


if __name__ == "__main__":
    unittest.main()
