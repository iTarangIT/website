"""What the tags on a post are, and what they are never allowed to be."""

from __future__ import annotations

import unittest

from cmo_runtime import social_tags
from cmo_runtime.content_flow import BLOG_CATEGORY_SLUGS


class EveryCategoryCarriesTags(unittest.TestCase):
    def test_every_category_the_writer_may_file_under_has_tags(self) -> None:
        """The hole this closes: a card with no keywords posted with no tags.

        Tags used to come only from `topic_keywords`, and `compose` appended them
        only `if summary.keywords`. A card without that field — every card the
        radar mints without one — went to three networks bare.
        """
        for slug in BLOG_CATEGORY_SLUGS:
            with self.subTest(category=slug):
                self.assertIn(slug, social_tags.CATEGORY_TAGS)
                self.assertTrue(social_tags.tags_for(category=slug))

    def test_an_article_with_no_keywords_at_all_still_gets_tags(self) -> None:
        tags = social_tags.tags_for(category="financing", keywords=[])

        self.assertTrue(tags)
        self.assertIn("#EVFinance", tags)

    def test_an_article_with_neither_category_nor_keywords_falls_back_to_the_beat(self) -> None:
        """Never nothing. The house tags are the floor."""
        self.assertEqual(
            social_tags.tags_for(category="", keywords=[]), list(social_tags.HOUSE_TAGS)
        )

    def test_no_category_tag_list_is_unknown_to_the_publisher(self) -> None:
        """A tag list for a category the writer cannot file under is dead code."""
        self.assertEqual(set(social_tags.CATEGORY_TAGS) - BLOG_CATEGORY_SLUGS, set())


class TagsReadTheWayTheIndustryWritesThem(unittest.TestCase):
    def test_a_known_term_reaches_the_settled_tag_not_a_slug(self) -> None:
        self.assertEqual(social_tags.tag_for_keyword("battery waste"), "#BatteryWasteRules")
        self.assertEqual(social_tags.tag_for_keyword("NBFC"), "#NBFC")
        self.assertEqual(social_tags.tag_for_keyword("e-rickshaw"), "#ERickshaw")

    def test_a_phrase_beats_a_word_inside_it(self) -> None:
        """`battery waste management rules 2022` is not `#EVBattery`."""
        self.assertEqual(
            social_tags.tag_for_keyword("Battery Waste Management Rules 2022"),
            "#BatteryWasteRules",
        )

    def test_a_short_term_never_matches_inside_a_longer_word(self) -> None:
        """`epr` inside `proper`, `emi` inside `emission` — the bug a plain
        substring search would ship."""
        self.assertNotEqual(social_tags.tag_for_keyword("proper sizing"), "#EPRCompliance")
        self.assertNotEqual(social_tags.tag_for_keyword("emission testing"), "#EMI")

    def test_an_unknown_keyword_is_camel_cased_not_lower_cased(self) -> None:
        """The old behaviour produced `#batteryswappingeconomics`."""
        self.assertEqual(
            social_tags.tag_for_keyword("battery swapping economics"),
            "#BatterySwapping",
        )
        self.assertEqual(social_tags.tag_for_keyword("driver livelihood"), "#DriverLivelihood")

    def test_an_acronym_survives_camel_casing_upper_case(self) -> None:
        """`#Nbfc` is worse than no tag."""
        self.assertEqual(social_tags.tag_for_keyword("nbfc partnerships"), "#NBFC")
        self.assertEqual(social_tags.tag_for_keyword("kwh per rupee"), "#KWHPerRupee")

    def test_a_tag_that_would_be_too_short_is_dropped(self) -> None:
        """`#ev` reaches everyone and therefore nobody."""
        self.assertNotIn("#ev", social_tags.tags_for(category="financing", keywords=["ev"]))

    def test_every_curated_tag_is_a_well_formed_hashtag(self) -> None:
        every = [
            *social_tags.HOUSE_TAGS,
            *social_tags.TERM_TAGS.values(),
            *(tag for tags in social_tags.CATEGORY_TAGS.values() for tag in tags),
        ]
        for tag in every:
            with self.subTest(tag=tag):
                self.assertRegex(tag, r"^#[A-Za-z][A-Za-z0-9]{2,}$")


class OrderingAndLimits(unittest.TestCase):
    def test_the_article_s_own_keywords_come_before_the_category(self) -> None:
        """A tight limit should spend itself on what makes this post different."""
        tags = social_tags.tags_for(
            category="financing", keywords=["battery swapping"], limit=2
        )

        self.assertEqual(tags[0], "#BatterySwapping")

    def test_the_house_tags_are_what_a_tight_limit_drops_first(self) -> None:
        tags = social_tags.tags_for(
            category="financing", keywords=["NBFC", "underwriting"], limit=3
        )

        self.assertNotIn("#EVIndia", tags)
        self.assertEqual(tags, ["#NBFC", "#Underwriting", "#EVFinance"])

    def test_a_tag_is_never_repeated_even_across_sources(self) -> None:
        """`financing` yields `#EVFinance` and so does the keyword `finance`."""
        tags = social_tags.tags_for(category="financing", keywords=["finance"], limit=6)

        self.assertEqual(len(tags), len(set(tags)))

    def test_each_platform_gets_the_count_its_readers_expect(self) -> None:
        for platform, limit in social_tags.PLATFORM_TAG_LIMITS.items():
            with self.subTest(platform=platform):
                tags = social_tags.tags_for_platform(
                    platform,
                    category="lifecycle-recycling",
                    keywords=["battery waste", "EPR", "circular economy", "second life"],
                )
                self.assertLessEqual(len(tags), limit)
                self.assertTrue(tags)

    def test_x_gets_the_fewest_because_they_cost_it_characters(self) -> None:
        self.assertLess(
            social_tags.PLATFORM_TAG_LIMITS["x"], social_tags.PLATFORM_TAG_LIMITS["linkedin"]
        )
        self.assertLess(
            social_tags.PLATFORM_TAG_LIMITS["linkedin"],
            social_tags.PLATFORM_TAG_LIMITS["instagram"],
        )

    def test_an_unknown_platform_is_refused_rather_than_defaulted(self) -> None:
        with self.assertRaises(KeyError):
            social_tags.tags_for_platform("threads", category="financing")

    def test_the_tag_line_is_one_line_of_space_separated_tags(self) -> None:
        line = social_tags.tag_line("linkedin", category="safety", keywords=["thermal runaway"])

        self.assertNotIn("\n", line)
        self.assertTrue(line.startswith("#"))
        self.assertEqual(line.split(), social_tags.tags_for_platform(
            "linkedin", category="safety", keywords=["thermal runaway"]
        ))



class TagsOnTheDraftsThemselves(unittest.TestCase):
    """`with_tags` runs after whichever producer wrote the prose."""

    ARTICLE = """---
title: E-Rickshaw Finance vs Upfront Purchase
meta_description: What buyers should compare before signing.
slug: erickshaw-finance-vs-upfront
category: financing
audience: fleet operators
---

Drivers who finance pay 18% more over three years.

The upfront route locks up working capital for months.

An NBFC underwrites on the battery, not the vehicle.
"""

    def summary(self, **kwargs):
        from cmo_runtime import social_copy

        return social_copy.summarise_article(
            self.ARTICLE, url="https://www.itarang.com/blog/x", **kwargs
        )

    def drafts(self, **kwargs):
        from cmo_runtime import social_copy

        summary = self.summary(**kwargs)
        return social_copy.drafts_for(task_id="TASK-1", summary=summary)

    def test_every_platform_carries_tags(self) -> None:
        for platform, draft in self.drafts(keywords=["NBFC"]).items():
            with self.subTest(platform=platform):
                text = "\n".join(draft.thread) if draft.thread else draft.body
                self.assertIn("#", text, f"{platform} went out untagged")

    def test_a_card_with_no_keywords_is_still_tagged(self) -> None:
        """The regression the whole taxonomy exists for."""
        for platform, draft in self.drafts(keywords=[]).items():
            with self.subTest(platform=platform):
                text = "\n".join(draft.thread) if draft.thread else draft.body
                self.assertIn("#EVFinance", text, f"{platform} lost its category tags")

    def test_the_x_tags_ride_the_last_item_not_the_hook(self) -> None:
        """Tags mid-thread interrupt the argument; the last item carries the link."""
        draft = self.drafts(keywords=["NBFC"])["x"]

        self.assertNotIn("#", draft.thread[0])
        self.assertIn("#", draft.thread[-1])

    def test_the_x_body_still_equals_the_first_thread_item(self) -> None:
        """Buffer rejects the pair otherwise — see `buffer_client.create_post`."""
        draft = self.drafts(keywords=["NBFC"])["x"]

        self.assertEqual(draft.body, draft.thread[0])

    def test_tags_are_dropped_rather_than_pushing_a_post_over_its_limit(self) -> None:
        from cmo_runtime import social_copy

        limit = social_copy.PLATFORM_LIMITS["x"]
        full = "x" * (limit - 4)
        fitted = social_copy._append_tags(full, ["#EVFinance", "#NBFC"], limit)

        self.assertLessEqual(len(fitted), limit)
        self.assertEqual(fitted, full, "a tag pushed the post over the limit")

    def test_as_many_tags_as_fit_are_kept(self) -> None:
        from cmo_runtime import social_copy

        fitted = social_copy._append_tags("body", ["#One", "#Two", "#Three"], len("body") + 2 + 4)

        self.assertEqual(fitted, "body\n\n#One")

    def test_every_draft_still_passes_the_platform_limits_after_tagging(self) -> None:
        from cmo_runtime import social_copy

        social_copy.validate(self.drafts(keywords=["NBFC", "underwriting", "e-rickshaw"]))

if __name__ == "__main__":
    unittest.main()
