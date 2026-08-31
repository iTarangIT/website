"""What goes on a social card, and what a card is never allowed to say.

`plan_cards` is pure, so every word on every card is assertable here without
generating an image or spending a cent. That is the whole reason the words are
chosen in Python and only *set* by the model: a headline a model wrote is a claim
iTarang did not make, printed under iTarang's wordmark.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmo_runtime import image_gen, social_cards, social_copy  # noqa: E402
from cmo_runtime.image_gen import ImageGenRefused  # noqa: E402
from cmo_runtime.social_cards import CardPlanRefused  # noqa: E402

ARTICLE = """---
title: The gazette says "may". The internet says "must".
meta_description: S.O. 958(E) makes the QR code optional. Ten sources checked, none quoted it.
slug: bwmr-gazette-vs-market
category: lifecycle-recycling
audience: compliance leads
---

The notification uses "may", not "shall", and that one word creates a choice.

A policy research institute published the opposite reading in April 2025.

Ten sources were checked for this piece and none of them quoted the notification.

Producers are budgeting for a QR code the gazette never required of them.
"""


def summary(markdown: str = ARTICLE, **kwargs):
    return social_copy.summarise_article(
        markdown, url="https://www.itarang.com/blog/bwmr-gazette-vs-market", **kwargs
    )


class TheSetOfCards(unittest.TestCase):
    def test_the_set_covers_all_three_platforms(self) -> None:
        cards = social_cards.plan_cards(summary())
        platforms = {card.platform for card in cards}

        self.assertEqual(platforms, {"linkedin", "x", "instagram"})

    def test_linkedin_and_x_get_one_wide_card_each(self) -> None:
        cards = social_cards.plan_cards(summary())

        for platform in ("linkedin", "x"):
            with self.subTest(platform=platform):
                card = social_cards.card_for(cards, platform)
                self.assertIsNotNone(card)
                self.assertEqual(card.aspect_ratio, social_cards.WIDE_ASPECT)

    def test_the_carousel_opens_on_the_hook_and_closes_on_the_call_to_action(self) -> None:
        """Swipe order is the content, so the ends are fixed."""
        swipe = social_cards.carousel(social_cards.plan_cards(summary()))

        self.assertEqual(swipe[0].variant, "ig-cover")
        self.assertEqual(swipe[0].role, "hook")
        self.assertEqual(swipe[-1].variant, "ig-close")
        self.assertEqual(swipe[-1].headline, social_cards.CLOSING_LINE)

    def test_every_instagram_card_is_square(self) -> None:
        for card in social_cards.carousel(social_cards.plan_cards(summary())):
            with self.subTest(variant=card.variant):
                self.assertEqual(card.aspect_ratio, social_cards.SQUARE_ASPECT)

    def test_the_carousel_never_runs_past_its_ceiling(self) -> None:
        swipe = social_cards.carousel(social_cards.plan_cards(summary()))

        self.assertLessEqual(len(swipe), social_cards.MAX_CAROUSEL_CARDS)
        self.assertGreaterEqual(len(swipe), social_cards.MIN_CAROUSEL_CARDS)

    def test_the_point_cards_are_numbered_for_the_reader(self) -> None:
        points = [
            card
            for card in social_cards.plan_cards(summary())
            if card.role == "point"
        ]

        self.assertEqual([card.kicker for card in points], [f"{n} of {len(points)}" for n in
                                                            range(1, len(points) + 1)])

    def test_the_filenames_follow_the_committed_precedent(self) -> None:
        """`97ddb9b` named them; the console must not invent a second scheme."""
        names = {
            card.filename("bwmr-gazette-vs-market")
            for card in social_cards.plan_cards(summary())
        }

        self.assertIn("bwmr-gazette-vs-market-linkedin.webp", names)
        self.assertIn("bwmr-gazette-vs-market-ig-cover.webp", names)
        self.assertIn("bwmr-gazette-vs-market-ig-1.webp", names)


class ACardNeverInventsAnything(unittest.TestCase):
    def test_every_headline_is_the_article_s_own_words(self) -> None:
        """The one property that makes an unreviewed card safe to publish."""
        source = summary()
        allowed = {source.title, social_cards.CLOSING_LINE, *source.sentences}

        for card in social_cards.plan_cards(source):
            with self.subTest(variant=card.variant):
                self.assertIn(card.headline, allowed, "a card said something the article did not")

    def test_every_support_line_is_the_article_s_own_words(self) -> None:
        source = summary()
        allowed = {source.meta_description, "", *source.sentences}

        for card in social_cards.plan_cards(source):
            with self.subTest(variant=card.variant):
                self.assertIn(card.support, allowed)

    def test_every_card_carries_alt_text(self) -> None:
        """`ImageMetadataInput.altText` is non-null, and a card is text anyway."""
        for card in social_cards.plan_cards(summary()):
            with self.subTest(variant=card.variant):
                self.assertTrue(card.alt_text.strip())
                self.assertIn(card.headline.rstrip("."), card.alt_text)


class Refusals(unittest.TestCase):
    def test_an_article_with_no_title_cannot_carry_a_card(self) -> None:
        with self.assertRaises(CardPlanRefused) as caught:
            social_cards.plan_cards(summary(ARTICLE.replace('title: The gazette says "may". The internet says "must".', "title:")))
        self.assertIn("no title", str(caught.exception))

    def test_an_article_with_nothing_short_enough_to_set_is_refused(self) -> None:
        """Rather than paying for cards with an unreadable wall of text on them."""
        long_line = "word " * 80
        markdown = f"""---
title: A title
meta_description: A description that is long enough to serve as the lead.
slug: s
category: financing
audience: fleet operators
---

{long_line}.
"""
        with self.assertRaises(CardPlanRefused) as caught:
            social_cards.plan_cards(summary(markdown))
        self.assertIn("cannot carry a carousel", str(caught.exception))

    def test_a_carousel_length_outside_the_bounds_is_refused(self) -> None:
        with self.assertRaises(CardPlanRefused):
            social_cards.plan_cards(summary(), carousel_cards=9)

    def test_a_thin_article_shortens_the_carousel_rather_than_repeating_itself(self) -> None:
        markdown = """---
title: A title
meta_description: A description long enough to be the lead sentence here.
slug: s
category: financing
audience: fleet operators
---

Only one sentence here is short enough to set on a card at all.
"""
        swipe = social_cards.carousel(social_cards.plan_cards(summary(markdown)))
        headlines = [card.headline for card in swipe]

        self.assertEqual(len(headlines), len(set(headlines)), "a sentence was repeated to pad")


class ThePromptTheModelIsGiven(unittest.TestCase):
    def card(self):
        return social_cards.card_for(social_cards.plan_cards(summary()), "linkedin")

    def prompt(self):
        card = self.card()
        return image_gen.social_card_prompt(
            role=card.role, kicker=card.kicker, headline=card.headline, support=card.support
        )

    def test_the_copy_reaches_the_model_verbatim(self) -> None:
        card, prompt = self.card(), self.prompt()

        # Quotes are neutralised for the prompt, so compare on that basis.
        self.assertIn(card.headline.replace('"', "'"), prompt)
        self.assertIn(card.support.replace('"', "'"), prompt)
        self.assertIn(card.kicker, prompt)

    def test_the_model_is_told_to_set_the_words_not_write_them(self) -> None:
        prompt = self.prompt()

        self.assertIn("EXACTLY as given", prompt)
        self.assertIn("no invented statistic", prompt)

    def test_the_card_rules_permit_text_where_the_article_rules_forbid_it(self) -> None:
        """The reason social cards need their own rules at all: an infographic is
        precisely what `HOUSE_RULES` exists to prevent."""
        self.assertIn("Render NO text", image_gen.HOUSE_RULES)
        self.assertNotIn("Render NO text", image_gen.SOCIAL_CARD_RULES)

    def test_a_card_still_may_not_invent_a_logo(self) -> None:
        """The one thing both rule sets agree on."""
        self.assertIn("No logo", image_gen.SOCIAL_CARD_RULES)

    def test_an_unknown_role_is_refused_rather_than_defaulted(self) -> None:
        with self.assertRaises(ImageGenRefused):
            image_gen.social_card_prompt(role="billboard", kicker="K", headline="H")

    def test_a_card_with_no_headline_is_refused(self) -> None:
        with self.assertRaises(ImageGenRefused):
            image_gen.social_card_prompt(role="wide", kicker="K", headline="   ")

    def test_every_planned_card_produces_a_prompt(self) -> None:
        """A role added to the planner without a direction would fail at spend time."""
        for card in social_cards.plan_cards(summary()):
            with self.subTest(variant=card.variant):
                self.assertTrue(
                    image_gen.social_card_prompt(
                        role=card.role,
                        kicker=card.kicker,
                        headline=card.headline,
                        support=card.support,
                    )
                )

    def test_every_planned_aspect_ratio_is_one_the_api_offers(self) -> None:
        for card in social_cards.plan_cards(summary()):
            with self.subTest(variant=card.variant):
                self.assertIn(card.aspect_ratio, image_gen.ASPECT_RATIOS)


class WhatTheSetCosts(unittest.TestCase):
    def test_the_cost_is_reported_before_it_is_spent(self) -> None:
        cards = social_cards.plan_cards(summary())

        self.assertAlmostEqual(
            social_cards.estimated_cost_usd(cards, 0.067), round(len(cards) * 0.067, 4)
        )

    def test_a_full_set_stays_well_under_the_monthly_warning(self) -> None:
        """Seven cards an article, priced at the model the console actually uses."""
        cards = social_cards.plan_cards(summary())
        price = image_gen.PER_IMAGE_USD[(image_gen.DEFAULT_MODEL, image_gen.DEFAULT_IMAGE_SIZE)]

        self.assertLess(social_cards.estimated_cost_usd(cards, price), 1.0)


if __name__ == "__main__":
    unittest.main()
