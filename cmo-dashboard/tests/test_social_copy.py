"""Platform-specific copy: that the three pieces really are three pieces.

The failure this suite exists to catch is the one the feature was built to end —
the same paragraph pasted to LinkedIn, X and Instagram. So the assertions are
about difference and about limits, not about wording.

Nothing here runs Hermes. The writer is stood in for, and the deterministic
composer is exercised directly, because it is what a human sees whenever the
writer is unavailable.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmo_runtime import social_copy  # noqa: E402
from cmo_runtime.social_copy import (  # noqa: E402
    MAX_THREAD_ITEMS,
    PLATFORM_LIMITS,
    SocialCopyRefused,
    SocialDraft,
    compose,
    drafts_for,
    summarise_article,
    validate,
)

ARTICLE = """---
title: What an e-rickshaw battery actually costs to replace
meta_title: E-rickshaw battery replacement cost, itemised
meta_description: A replacement pack is rarely the whole bill, and the rest of it is predictable.
slug: e-rickshaw-battery-replacement-cost
category: financing
audience: fleet operators and lenders
source_urls: https://example.gov/report
---

# What an e-rickshaw battery actually costs to replace

A replacement pack is rarely the whole bill. Labour, downtime and disposal move
the number by a third. Operators who plan for the pack alone are the ones who
end up borrowing twice.

## The itemised bill

The pack is 62 per cent of it. Downtime is the part nobody budgets for.

![Figure](diagram)
"""


def summary(**overrides):
    values = {
        "url": "https://www.itarang.com/blog/e-rickshaw-battery-replacement-cost",
        "keywords": ("e-rickshaw battery cost", "battery replacement"),
        "cover_alt": "A depot at dusk",
    }
    values.update(overrides)
    return summarise_article(ARTICLE, **values)


class Reading(unittest.TestCase):
    def test_the_header_is_read_and_kept_out_of_the_prose(self):
        read = summary()
        self.assertEqual(read.title, "What an e-rickshaw battery actually costs to replace")
        self.assertEqual(read.audience, "fleet operators and lenders")
        self.assertNotIn("slug:", read.body)
        self.assertNotIn("meta_description", " ".join(read.sentences))

    def test_headings_and_figures_do_not_become_sentences(self):
        """A heading pulled into a thread reads as a fragment, which is how it shows."""
        joined = " ".join(summary().sentences)
        self.assertNotIn("The itemised bill", joined)
        self.assertNotIn("![Figure]", joined)


class ThreePiecesNotOne(unittest.TestCase):
    def test_the_three_drafts_are_not_the_same_text(self):
        drafts = compose(summary())
        bodies = {platform: draft.body for platform, draft in drafts.items()}
        self.assertEqual(len(set(bodies.values())), 3, "one paragraph reached every platform")

    def test_linkedin_opens_with_the_audience_and_closes_with_the_link(self):
        draft = compose(summary())["linkedin"]
        self.assertTrue(draft.body.startswith("For fleet operators and lenders:"))
        self.assertIn("https://www.itarang.com/blog/e-rickshaw-battery-replacement-cost", draft.body)

    def test_x_is_a_thread_whose_last_item_carries_the_link(self):
        draft = compose(summary())["x"]
        self.assertGreater(len(draft.thread), 1)
        self.assertEqual(draft.body, draft.thread[0])
        self.assertIn("https://www.itarang.com/blog/", draft.thread[-1])

    def test_instagram_says_link_in_bio_because_captions_carry_no_live_link(self):
        draft = compose(summary())["instagram"]
        self.assertIn("linked in bio", draft.body)
        self.assertNotIn("https://", draft.body)

    def test_instagram_carries_alt_text_because_it_must_carry_a_picture(self):
        self.assertEqual(compose(summary())["instagram"].image_alt, "A depot at dusk")

    def test_compose_writes_prose_and_leaves_the_tags_to_the_taxonomy(self):
        """Tagging moved out of `compose` so the writer path gets the same tags.

        These used to assert `#erickshawbatterycost` — the keyword, lowercased
        and stripped of its spaces. That is not a tag anyone follows, and it was
        only ever produced when the card happened to carry `topic_keywords`.
        `cmo_runtime.social_tags` chooses them now, for both producers, from the
        curated set; `with_tags` is what puts them on a draft.
        """
        self.assertNotIn("#", compose(summary())["instagram"].body)

    def test_the_tagged_draft_carries_industry_tags_from_its_keywords(self):
        drafts = social_copy.with_tags(compose(summary()), summary())

        self.assertIn("#ERickshaw", drafts["instagram"].body)
        self.assertNotIn("#erickshawbatterycost", drafts["instagram"].body)

    def test_a_two_letter_keyword_never_becomes_a_hashtag(self):
        """`#ev` reaches everyone and therefore nobody. Still true, new mechanism."""
        read = summary(keywords=("EV", "battery finance"))
        draft = social_copy.with_tags(compose(read), read)["instagram"]

        self.assertNotIn("#ev ", draft.body + " ")
        self.assertIn("#EVFinance", draft.body)

    def test_an_article_with_nothing_to_say_is_refused_rather_than_padded(self):
        with self.assertRaises(SocialCopyRefused):
            compose(
                social_copy.ArticleSummary(
                    title="A title", meta_description="", slug="s", category="financing",
                    audience="", url="https://x/y", body="", sentences=(),
                )
            )


class Limits(unittest.TestCase):
    def test_every_composed_draft_is_inside_its_platform_limit(self):
        drafts = compose(summary())
        validate(drafts)
        for platform, draft in drafts.items():
            self.assertLessEqual(len(draft.body), PLATFORM_LIMITS[platform])
            for item in draft.thread:
                self.assertLessEqual(len(item), PLATFORM_LIMITS[platform])

    def test_an_overlong_draft_is_refused_naming_the_platform_and_the_overrun(self):
        with self.assertRaises(SocialCopyRefused) as caught:
            validate({"x": SocialDraft(platform="x", body="w" * 500)})
        message = str(caught.exception)
        self.assertIn("x", message)
        self.assertIn("500", message)
        self.assertIn("280", message)

    def test_a_thread_longer_than_the_cap_is_refused(self):
        items = tuple(f"post {index}" for index in range(MAX_THREAD_ITEMS + 2))
        with self.assertRaises(SocialCopyRefused):
            validate({"x": SocialDraft(platform="x", body=items[0], thread=items)})

    def test_a_composed_thread_never_exceeds_the_cap(self):
        long_article = ARTICLE + "\n" + " ".join(f"Sentence number {n} here." for n in range(60))
        drafts = compose(summarise_article(long_article, url="https://www.itarang.com/blog/a"))
        self.assertLessEqual(len(drafts["x"].thread), MAX_THREAD_ITEMS)
        validate(drafts)

    def test_a_platform_this_console_does_not_post_to_is_refused(self):
        with self.assertRaises(SocialCopyRefused):
            validate({"facebook": SocialDraft(platform="facebook", body="Copy.")})


class WhoWroteIt(unittest.TestCase):
    class Writer:
        def __init__(self, error=None):
            self.error = error
            self.calls = 0

        def write(self, *, task_id, summary, skill_text):
            self.calls += 1
            if self.error:
                raise self.error
            return {
                "linkedin": SocialDraft(platform="linkedin", body="Written.", source="writer"),
                "x": SocialDraft(platform="x", body="Hook.", thread=("Hook.",), source="writer"),
                "instagram": SocialDraft(platform="instagram", body="Caption.", source="writer"),
            }

    def test_the_writer_is_used_when_it_can_be(self):
        writer = self.Writer()
        drafts = drafts_for(task_id="TASK-1", summary=summary(), skill_text="SKILL", writer=writer)
        self.assertEqual(writer.calls, 1)
        self.assertEqual({draft.source for draft in drafts.values()}, {"writer"})

    def test_a_writer_failure_costs_the_drafts_their_authorship_and_says_so(self):
        """Not a silent downgrade: `composed` is what the console prints on the card."""
        writer = self.Writer(error=SocialCopyRefused("the writer response was malformed"))
        drafts = drafts_for(task_id="TASK-1", summary=summary(), skill_text="SKILL", writer=writer)
        self.assertEqual({draft.source for draft in drafts.values()}, {"composed"})
        self.assertEqual(len(drafts), 3)

    def test_no_skill_text_means_the_writer_is_not_asked_at_all(self):
        """The skill is the whole instruction. Calling without it is a call worth nothing."""
        writer = self.Writer()
        drafts_for(task_id="TASK-1", summary=summary(), skill_text="", writer=writer)
        self.assertEqual(writer.calls, 0)


if __name__ == "__main__":
    unittest.main()
