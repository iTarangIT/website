"""What each social card says, decided before anything is generated.

Two jobs are deliberately kept apart here.

**Choosing the words is this module's job, and it is deterministic.** The copy on
a card is the article's own title and sentences, picked by rule. Nothing here asks
a model what the article says, because a card is read as a quotation from the
piece: a headline the model wrote is a claim iTarang did not make, sitting under
iTarang's wordmark, with no reviewer able to tell it apart from one we did.

**Setting the words is the model's job**, and that is `image_gen.social_card_prompt`
plus `GeminiImageClient`. The model is a typesetter here, not an author.

The split is what makes a card auditable: `plan_cards` is pure, so a test can
assert the exact words on every card without generating an image or spending a
cent, and the prompt carries those words verbatim for the model to set.

The shapes follow the five cards committed by hand in `97ddb9b`, which are the
only precedent for what these should look like:

    <slug>-linkedin   1.91:1-ish wide card, the whole claim on one card
    <slug>-x          the same shape, terser
    <slug>-ig-cover   1:1, the hook that stops a thumb
    <slug>-ig-1..n    1:1, one point each
    <slug>-ig-close   1:1, the call to action
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:  # pragma: no cover - typing only
    from cmo_runtime.social_copy import ArticleSummary

#: Wide cards are 16:9 — the closest ratio the image API offers to the 1.91:1 that
#: LinkedIn and X actually crop to. Instagram is square, as the committed cards are.
WIDE_ASPECT = "16:9"
SQUARE_ASPECT = "1:1"

#: A carousel shorter than this is not worth swiping; longer than this is not
#: swiped. Cover and closing card are two of the count.
MIN_CAROUSEL_CARDS = 3
MAX_CAROUSEL_CARDS = 5

#: How the category slug reads as an eyebrow. Falls back to the slug in capitals,
#: so a category added to `BLOG_CATEGORY_SLUGS` without being added here still
#: renders something sane rather than an empty line.
CATEGORY_LABELS = {
    "financing": "EV Finance",
    "battery-selection": "Battery Selection",
    "charging-maintenance": "Charging & Maintenance",
    "safety": "Battery Safety",
    "lifecycle-recycling": "Lifecycle & Recycling",
    "partners-industry": "Industry",
    "energy-storage": "Energy Storage",
    "energy-transition": "Energy Transition",
}

#: The closing card's line. Instagram captions carry no live link, which is the
#: whole reason the carousel ends on a card that says where the article is.
CLOSING_LINE = "Full article linked in bio."


class CardPlanRefused(RuntimeError):
    """The article cannot carry a card set, in words an operator can act on."""


@dataclass(frozen=True)
class SocialCard:
    """One card: its copy, its shape, and the name it is stored and served under."""

    variant: str
    platform: str
    role: str
    aspect_ratio: str
    kicker: str
    headline: str
    support: str = ""
    footer: str = "itarang.com"

    @property
    def alt_text(self) -> str:
        """What a screen reader is given, and what Buffer requires per asset.

        `ImageMetadataInput.altText` is non-null, so every card needs one; and a
        card is text, so its alt text is that text rather than a description of a
        picture of it.
        """
        parts = [self.headline.rstrip(".") + "."]
        if self.support:
            parts.append(self.support)
        return f"{self.kicker}. " + " ".join(parts)

    def filename(self, slug: str, suffix: str = ".webp") -> str:
        """`bwmr-gazette-vs-market-ig-1.webp` — the precedent's naming."""
        return f"{slug}-{self.variant}{suffix}"

    def as_dict(self) -> dict[str, object]:
        return {
            "variant": self.variant,
            "platform": self.platform,
            "role": self.role,
            "aspect_ratio": self.aspect_ratio,
            "kicker": self.kicker,
            "headline": self.headline,
            "support": self.support,
            "footer": self.footer,
            "alt_text": self.alt_text,
        }


def category_label(category: str) -> str:
    slug = " ".join(str(category or "").split()).strip().lower()
    if not slug:
        return "iTarang"
    return CATEGORY_LABELS.get(slug, slug.replace("-", " ").title())


def _sentences(summary: "ArticleSummary") -> list[str]:
    """Article sentences short enough to set on a card, longest-first ties broken
    by document order.

    A card is read in about two seconds. A 40-word sentence set at card size is
    either unreadable or shrunk until it is, so the long ones are left out here
    rather than discovered to be unreadable after they are paid for.
    """
    return [item for item in summary.sentences if 30 <= len(item) <= 165]


def plan_cards(
    summary: "ArticleSummary", *, carousel_cards: int = MAX_CAROUSEL_CARDS
) -> list[SocialCard]:
    """Every card for one article: two wide, and the Instagram carousel.

    Raises `CardPlanRefused` when the article cannot fill a set, rather than
    generating cards with empty space where a sentence should be. An article with
    one usable sentence is a cover and a close, and that is not a carousel.
    """
    if not MIN_CAROUSEL_CARDS <= carousel_cards <= MAX_CAROUSEL_CARDS:
        raise CardPlanRefused(
            f"a carousel runs to between {MIN_CAROUSEL_CARDS} and "
            f"{MAX_CAROUSEL_CARDS} cards, not {carousel_cards}"
        )
    headline = " ".join(str(summary.title).split())
    if not headline:
        raise CardPlanRefused("the article has no title to put on a card")

    kicker = category_label(summary.category)
    lead = summary.meta_description or (summary.sentences[0] if summary.sentences else "")
    if not lead:
        raise CardPlanRefused("the article has neither a meta description nor a first sentence")

    points = _sentences(summary)
    wanted = carousel_cards - 2  # the cover and the close are not points
    if len(points) < wanted:
        # Not a refusal: a shorter carousel is a carousel. It shortens rather than
        # repeating a sentence to reach a target length nobody asked for.
        wanted = len(points)
    if wanted < MIN_CAROUSEL_CARDS - 2:
        raise CardPlanRefused(
            "the article has no sentence short enough to set on a card, so it "
            "cannot carry a carousel"
        )

    cards = [
        SocialCard(
            variant="linkedin",
            platform="linkedin",
            role="wide",
            aspect_ratio=WIDE_ASPECT,
            kicker=kicker,
            headline=headline,
            support=lead,
        ),
        SocialCard(
            variant="x",
            platform="x",
            role="wide",
            aspect_ratio=WIDE_ASPECT,
            kicker=kicker,
            headline=headline,
            # X is read faster and smaller than LinkedIn, so the wide card there
            # carries the claim and stops.
            support=points[0] if points else "",
        ),
        SocialCard(
            variant="ig-cover",
            platform="instagram",
            role="hook",
            aspect_ratio=SQUARE_ASPECT,
            kicker=kicker,
            headline=headline,
            support=lead,
        ),
    ]
    cards.extend(
        SocialCard(
            variant=f"ig-{index}",
            platform="instagram",
            role="point",
            aspect_ratio=SQUARE_ASPECT,
            kicker=f"{index} of {wanted}",
            headline=point,
        )
        for index, point in enumerate(points[:wanted], start=1)
    )
    cards.append(
        SocialCard(
            variant="ig-close",
            platform="instagram",
            role="close",
            aspect_ratio=SQUARE_ASPECT,
            kicker=kicker,
            headline=CLOSING_LINE,
            support="",
        )
    )
    return cards


def carousel(cards: Sequence[SocialCard]) -> list[SocialCard]:
    """The Instagram cards, in swipe order. Order is the content here."""
    return [card for card in cards if card.platform == "instagram"]


def card_for(cards: Sequence[SocialCard], platform: str) -> SocialCard | None:
    """The single wide card for LinkedIn or X."""
    return next(
        (card for card in cards if card.platform == platform and card.role == "wide"), None
    )


def estimated_cost_usd(cards: Sequence[SocialCard], price_per_image: float) -> float:
    """What generating this set will cost, to be shown before it is spent."""
    return round(len(cards) * float(price_per_image), 4)
