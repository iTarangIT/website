"""Industry and business hashtags for the cross-post, chosen rather than slugified.

What this replaces was one line: lowercase the card's `topic_keywords`, strip the
punctuation, prepend `#`. It produced `#evfinance` where the industry writes
`#EVFinance`, it produced `#batterywastemanagementrules2022` from a keyword that
happened to be a phrase, and on a card with no `topic_keywords` at all it produced
nothing — the article shipped to three networks with no tags on it.

So tags come from three places, in this order of confidence:

1. **The beat.** Two tags that are true of every iTarang article, because the
   account is about one thing. They anchor a post that would otherwise carry only
   tags invented for it.
2. **The category.** Each of the eight `BLOG_CATEGORY_SLUGS` maps to established
   tags real practitioners in Indian EV, fleet and lending already follow. This is
   the reason a card with no keywords is no longer a card with no tags.
3. **The article's own keywords**, matched against a term table first so that
   "battery waste" reaches `#BatteryWasteRules` rather than `#batterywaste`, and
   camel-cased as a last resort so an unmatched keyword still reads as a tag.

Nothing here invents a tag from an article's prose. A hashtag is a room you are
asking readers to walk into, and one assembled from a sentence is an empty room.
"""

from __future__ import annotations

import re
from typing import Iterable, Sequence

#: How many tags each network gets. These are conventions, not API limits.
#:
#: LinkedIn's own guidance is three to five; past that the post reads as spam and
#: the feed treats it accordingly. X charges the tag against a 280-character post,
#: so two is the ceiling and one is usually right. Instagram is the one network
#: where a block of tags is native and expected.
PLATFORM_TAG_LIMITS = {"linkedin": 4, "x": 2, "instagram": 10}

#: True of every article this account publishes. Deliberately two, not ten: a
#: house block repeated on every post is how an account teaches the feed to
#: discount its tags.
HOUSE_TAGS = ("#EVIndia", "#ElectricMobility")

#: The eight categories the writer may file under, each with the tags that the
#: people who care about that beat actually follow. Ordered — the earlier a tag
#: sits, the more likely it survives a tight per-platform limit.
CATEGORY_TAGS: dict[str, tuple[str, ...]] = {
    "financing": (
        "#EVFinance",
        "#NBFC",
        "#FleetFinance",
        "#MSMELending",
        "#AssetFinance",
        "#VehicleFinance",
    ),
    "battery-selection": (
        "#LithiumIon",
        "#EVBattery",
        "#BatteryTech",
        "#ERickshaw",
        "#EnergyDensity",
    ),
    "charging-maintenance": (
        "#EVCharging",
        "#ChargingInfrastructure",
        "#FleetOps",
        "#EVMaintenance",
        "#Uptime",
    ),
    "safety": (
        "#BatterySafety",
        "#EVSafety",
        "#AISCertification",
        "#ThermalRunaway",
        "#ComplianceIndia",
    ),
    "lifecycle-recycling": (
        "#BatteryRecycling",
        "#CircularEconomy",
        "#EPRCompliance",
        "#BatteryWasteRules",
        "#SecondLifeBatteries",
    ),
    "partners-industry": (
        "#EVEcosystem",
        "#FleetManagement",
        "#LastMileDelivery",
        "#DealerNetwork",
        "#B2BPartnerships",
    ),
    "energy-storage": (
        "#EnergyStorage",
        "#BESS",
        "#GridScale",
        "#SolarStorage",
        "#PeakShaving",
    ),
    "energy-transition": (
        "#EnergyTransition",
        "#CleanEnergy",
        "#Decarbonisation",
        "#NetZero",
        "#RenewableEnergy",
    ),
}

#: Industry terms that have a settled tag, so a keyword reaches the tag the
#: industry uses rather than a slugified version of itself. Keys are matched
#: case-insensitively against the whole keyword and against its words, longest
#: key first, so "battery waste management rules" beats "battery".
TERM_TAGS: dict[str, str] = {
    "battery waste management rules": "#BatteryWasteRules",
    "extended producer responsibility": "#EPRCompliance",
    "battery as a service": "#BaaS",
    "total cost of ownership": "#TCO",
    "state of charge": "#StateOfCharge",
    "state of health": "#StateOfHealth",
    "battery management system": "#BMS",
    "charging infrastructure": "#ChargingInfrastructure",
    "last mile delivery": "#LastMileDelivery",
    "last mile": "#LastMileDelivery",
    "battery swapping": "#BatterySwapping",
    "battery recycling": "#BatteryRecycling",
    "battery waste": "#BatteryWasteRules",
    "fleet management": "#FleetManagement",
    "fleet operator": "#FleetOps",
    "electric rickshaw": "#ERickshaw",
    "e-rickshaw": "#ERickshaw",
    "erickshaw": "#ERickshaw",
    "three wheeler": "#ThreeWheelerEV",
    "3 wheeler": "#ThreeWheelerEV",
    "two wheeler": "#TwoWheelerEV",
    "lithium ion": "#LithiumIon",
    "lithium-ion": "#LithiumIon",
    "lead acid": "#LeadAcid",
    "energy storage": "#EnergyStorage",
    "electric vehicle": "#ElectricVehicles",
    "electric mobility": "#ElectricMobility",
    "circular economy": "#CircularEconomy",
    "second life": "#SecondLifeBatteries",
    "thermal runaway": "#ThermalRunaway",
    "vehicle finance": "#VehicleFinance",
    "asset finance": "#AssetFinance",
    "loan against vehicle": "#VehicleFinance",
    "credit underwriting": "#CreditRisk",
    "underwriting": "#Underwriting",
    "repossession": "#AssetRecovery",
    "delinquency": "#CreditRisk",
    "telematics": "#Telematics",
    "epr": "#EPRCompliance",
    "nbfc": "#NBFC",
    "bess": "#BESS",
    "baas": "#BaaS",
    "tco": "#TCO",
    "bms": "#BMS",
    "emi": "#EMI",
    "oem": "#OEM",
    "fame": "#FAME",
    "pli": "#PLI",
    "gst": "#GST",
    "msme": "#MSME",
    "solar": "#Solar",
    "subsidy": "#EVSubsidy",
    "policy": "#EVPolicyIndia",
    "regulation": "#ComplianceIndia",
    "compliance": "#ComplianceIndia",
    "warranty": "#Warranty",
    "dealer": "#DealerNetwork",
    "charger": "#EVCharging",
    "charging": "#EVCharging",
    "range": "#EVRange",
    "uptime": "#Uptime",
    "resale": "#ResaleValue",
    "insurance": "#Insurance",
    "leasing": "#Leasing",
    "financing": "#EVFinance",
    "finance": "#EVFinance",
    "safety": "#BatterySafety",
    "recycling": "#Recycling",
    "battery": "#EVBattery",
    "fleet": "#FleetOps",
}

#: Keys tried longest-first, so a phrase always beats a word inside it.
_TERMS_BY_LENGTH = tuple(sorted(TERM_TAGS, key=len, reverse=True))

_WORD = re.compile(r"[^a-z0-9]+")
#: Acronyms that stay upper-case when a keyword is camel-cased as a fallback.
_ACRONYMS = frozenset(
    {"ev", "evs", "nbfc", "bms", "baas", "bess", "tco", "epr", "emi", "oem",
     "gst", "msme", "pli", "fame", "soc", "soh", "kwh", "ah", "dc", "ac", "ui"}
)
#: Below this a tag is noise: `#ev` reaches everyone and therefore nobody.
MIN_TAG_LENGTH = 3


def _normalise(value: str) -> str:
    return " ".join(str(value or "").split()).strip().lower()


def _camel(keyword: str) -> str:
    """`battery swapping economics` -> `#BatterySwappingEconomics`.

    Only reached when a keyword matched nothing in `TERM_TAGS`. Acronyms are
    upper-cased rather than title-cased, because `#Nbfc` is worse than no tag.
    """
    words = [word for word in _WORD.split(_normalise(keyword)) if word]
    if not words:
        return ""
    parts = [word.upper() if word in _ACRONYMS else word.capitalize() for word in words]
    tag = "".join(parts)
    return f"#{tag}" if len(tag) >= MIN_TAG_LENGTH else ""


def tag_for_keyword(keyword: str) -> str:
    """The settled industry tag for one keyword, or a camel-cased fallback.

    Matches the whole keyword first, then the longest known term appearing inside
    it, so `battery waste management rules 2022` reaches `#BatteryWasteRules`
    rather than being camel-cased into a tag nobody follows.
    """
    text = _normalise(keyword)
    if not text:
        return ""
    if text in TERM_TAGS:
        return TERM_TAGS[text]
    for term in _TERMS_BY_LENGTH:
        # On a word boundary, so `epr` does not match inside `proper` and `emi`
        # does not match inside `emission`.
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text):
            return TERM_TAGS[term]
    return _camel(text)


def _ordered_unique(tags: Iterable[str]) -> list[str]:
    """Dedupe case-insensitively, keeping the first spelling and the order."""
    seen: set[str] = set()
    kept: list[str] = []
    for tag in tags:
        if not tag or len(tag) <= MIN_TAG_LENGTH:
            continue
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        kept.append(tag)
    return kept


def tags_for(
    *,
    category: str = "",
    keywords: Sequence[str] = (),
    limit: int = 4,
) -> list[str]:
    """The tags for one article, most specific first, capped at `limit`.

    Ordering is the whole design. The article's own keywords lead, because they
    are what makes this post different from the last one; the category follows,
    because it is what the post has in common with a readership; the house tags
    come last and are the ones a tight limit drops first. A post with four tags
    should not spend two of them saying "this is an EV account".
    """
    if limit <= 0:
        return []
    specific = [tag_for_keyword(word) for word in keywords]
    general = list(CATEGORY_TAGS.get(_normalise(category).replace(" ", "-"), ()))
    return _ordered_unique([*specific, *general, *HOUSE_TAGS])[:limit]


def tags_for_platform(
    platform: str, *, category: str = "", keywords: Sequence[str] = ()
) -> list[str]:
    """`tags_for` at the count that platform's readers expect."""
    limit = PLATFORM_TAG_LIMITS.get(platform)
    if limit is None:
        raise KeyError(f"{platform} is not a platform this console posts to")
    return tags_for(category=category, keywords=keywords, limit=limit)


def tag_line(platform: str, *, category: str = "", keywords: Sequence[str] = ()) -> str:
    """The tags as they are appended to a post: space separated, one line."""
    return " ".join(tags_for_platform(platform, category=category, keywords=keywords))
