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
                    image_alt="", images=(), thread=(), mode="addToQueue"):
        self.posted.append(
            {"platform": platform, "text": text, "link": link,
             "image_url": image_url, "images": [dict(item) for item in images],
             "thread": list(thread), "mode": mode}
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


class FakeImages:
    """A Gemini that draws nothing and records every prompt it was given."""

    def __init__(self, *, fail_after: int | None = None) -> None:
        self.prompts: list[dict] = []
        self.fail_after = fail_after

    def generate(self, prompt, *, task_id="", aspect_ratio="16:9", image_size="1K"):
        from cmo_runtime.image_gen import GeneratedImage, ImageGenRefused

        if self.fail_after is not None and len(self.prompts) >= self.fail_after:
            raise ImageGenRefused("blocked — month-to-date spend crosses the threshold")
        self.prompts.append(
            {"prompt": prompt, "task_id": task_id, "aspect_ratio": aspect_ratio}
        )
        return GeneratedImage(
            webp=b"RIFFfake-card", width=1080, height=1080,
            model="gemini-3.1-flash-image", image_size=image_size,
            aspect_ratio=aspect_ratio, prompt=prompt, estimated_cost_usd=0.067,
        )


class TheCards(SocialFixture):
    """The infographics and the carousel: planned, drawn, bound, and posted."""

    def plan(self):
        return ceo_social.plan_cards(self.profile, "TASK-900", website_root=self.website)

    def draw(self, **overrides):
        options = {
            "actor": "ceo@itarang.test",
            "website_root": self.website,
            "client": FakeImages(),
        }
        options.update(overrides)
        return ceo_social.generate_cards(self.profile, "TASK-900", **options)

    def test_the_plan_spends_nothing_and_says_what_would_be_drawn(self):
        """A human sees the set and its cost before a rupee is spent."""
        cards, slug = self.plan()

        self.assertTrue(slug)
        self.assertTrue(cards)
        self.assertEqual({card.platform for card in cards}, {"linkedin", "x", "instagram"})

    def test_every_card_is_written_to_the_artifact_store(self):
        self.generate()
        result = self.draw()

        for card in result["cards"]:
            with self.subTest(variant=card["variant"]):
                self.assertTrue((self.profile / "artifacts" / card["filename"]).is_file())

    def test_each_card_is_asked_for_at_its_own_aspect_ratio(self):
        """A square carousel card drawn at 16:9 is cropped by Instagram, not by us."""
        self.generate()
        client = FakeImages()
        self.draw(client=client)

        ratios = {
            call["aspect_ratio"] for call in client.prompts
        }
        self.assertEqual(ratios, {"16:9", "1:1"})

    def test_the_prompt_carries_the_planned_copy_rather_than_asking_for_copy(self):
        """The model sets words it is given; it never writes them."""
        self.generate()
        client = FakeImages()
        self.draw(client=client)

        for call in client.prompts:
            with self.subTest(prompt=call["prompt"][:40]):
                self.assertIn("EXACTLY as given", call["prompt"])

    def test_the_carousel_is_bound_to_instagram_in_swipe_order(self):
        self.generate()
        self.draw()
        images = self.drafts()["instagram"]["images"]

        self.assertGreater(len(images), 1, "instagram got a single card, not a carousel")
        self.assertIn("-ig-cover", images[0]["url"])
        self.assertIn("-ig-close", images[-1]["url"])

    def test_linkedin_and_x_each_get_exactly_one_infographic(self):
        self.generate()
        self.draw()
        drafts = self.drafts()

        for platform in ("linkedin", "x"):
            with self.subTest(platform=platform):
                self.assertEqual(len(drafts[platform]["images"]), 1)

    def test_every_bound_card_carries_alt_text(self):
        """`ImageMetadataInput.altText` is non-null; Buffer 400s on an empty one."""
        self.generate()
        self.draw()

        for platform, row in self.drafts().items():
            for image in row["images"]:
                with self.subTest(platform=platform, url=image["url"]):
                    self.assertTrue(image["alt"].strip())

    def test_the_bound_urls_are_public_and_not_artifact_paths(self):
        """Buffer fetches over the internet; a profile path is not an image."""
        self.generate()
        self.draw()

        for row in self.drafts().values():
            for image in row["images"]:
                with self.subTest(url=image["url"]):
                    self.assertTrue(image["url"].startswith("http"))
                    self.assertIn("/images/social/", image["url"])

    def test_drawing_cards_does_not_disturb_the_copy(self):
        """Two separate presses, two separate columns."""
        self.generate()
        before = {name: row["body"] for name, row in self.drafts().items()}
        self.draw()

        self.assertEqual({name: row["body"] for name, row in self.drafts().items()}, before)

    def test_rewriting_the_copy_does_not_discard_the_cards(self):
        """They cost money. A caption edit must not throw them away."""
        self.generate()
        self.draw()
        before = self.drafts()["instagram"]["images"]
        self.generate()

        self.assertEqual(self.drafts()["instagram"]["images"], before)

    def test_a_budget_refusal_says_how_many_cards_were_already_paid_for(self):
        """Otherwise a retry pays for them twice with no way to know."""
        self.generate()
        with self.assertRaises(ceo_social.PublicationRefused) as caught:
            self.draw(client=FakeImages(fail_after=2))

        self.assertIn("2 of", str(caught.exception))

    def test_cards_are_refused_outright_when_gemini_is_not_connected(self):
        """The key the user supplies. Its absence is a sentence, not a stack trace."""
        self.generate()
        with self.assertRaises(ceo_social.PublicationRefused) as caught:
            ceo_social.generate_cards(
                self.profile, "TASK-900", actor="ceo@itarang.test",
                website_root=self.website,
            )

        self.assertIn("Gemini not connected", str(caught.exception))


class TheCardsOnTheWire(SocialFixture):
    """What Buffer is actually handed once the cards exist."""

    def draw_and_send(self, **overrides):
        self.generate()
        ceo_social.generate_cards(
            self.profile, "TASK-900", actor="ceo@itarang.test",
            website_root=self.website, client=FakeImages(),
        )
        return self.send(**overrides)

    def posted(self) -> dict[str, dict]:
        return {item["platform"]: item for item in self.buffer.posted}

    def test_instagram_is_handed_the_carousel_not_the_article_cover(self):
        self.draw_and_send()
        instagram = self.posted()["instagram"]

        self.assertGreater(len(instagram["images"]), 1)
        self.assertEqual(instagram["image_url"], "", "the cover was sent beside the carousel")

    def test_linkedin_and_x_are_handed_their_infographic(self):
        self.draw_and_send()
        posted = self.posted()

        for platform in ("linkedin", "x"):
            with self.subTest(platform=platform):
                self.assertEqual(len(posted[platform]["images"]), 1)

    def test_an_article_with_no_cards_still_sends_on_its_cover(self):
        """Every article published before the cards existed relies on this."""
        self.generate()
        self.send()
        instagram = self.posted()["instagram"]

        self.assertEqual(instagram["images"], [])
        self.assertIn("/images/blog/", instagram["image_url"])

    def test_a_platform_whose_cards_are_not_live_yet_is_not_offered(self):
        """Buffer would fetch a 404 and report it as a flat invalid input."""
        self.generate()
        ceo_social.generate_cards(
            self.profile, "TASK-900", actor="ceo@itarang.test",
            website_root=self.website, client=FakeImages(),
        )

        def nothing_is_reachable(request, timeout=0):
            raise OSError("not deployed yet")

        check = self.preflight(check_live=True, opener=nothing_is_reachable)

        self.assertEqual(check.sendable, [])
        self.assertTrue(
            any("not on the live site yet" in note for note in check.notes),
            check.notes,
        )
