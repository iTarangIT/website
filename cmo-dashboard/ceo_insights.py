"""What happened, why it happened, and what to do about it.

`analytics_readers` answers "what are the numbers" and `ceo_analytics` answers
"how did each article do". This module answers the only question a CMO opens the
tab for, and the one the tab has never answered: given those numbers, what should
change this week.

Three rules govern everything here, and they are the reason this is a rule engine
and not a model.

**Every sentence names the numbers it came from.** A finding that cannot quote the
figures behind it is an opinion, and an opinion on a marketing console is
indistinguishable from a measurement once it has been read.

**An unmeasured input produces no finding.** Not a hedged one, not a zero -- none.
This is the same rule the readers follow, carried one layer up: `None` and `0` are
different answers, and a rule that treats them alike will confidently recommend
acting on a channel nobody instrumented.

**A sample too small to support a recommendation gets an observation instead.**
20.7% of 29 sessions is six sessions. The percentage is real and the trend it
implies is not, so below `MIN_SAMPLE` a finding keeps its numbers, drops its
`action`, and says why.

The output is plain dicts, shipped as JSON in `state_payload` and rendered by the
console. `panel` is what lets each table carry its own finding underneath it,
which is what makes the tab decision-shaped rather than a wall of prose at the top.
"""
from __future__ import annotations

from typing import Any, Sequence

#: Below this many sessions a rule reports what it saw and recommends nothing.
MIN_SAMPLE = 30

#: A channel or country has to clear this share of sessions before it is worth a
#: sentence. Under it, the row in the table already says everything true.
MIN_SHARE = 5.0

#: How far from the site engagement rate counts as "materially" different, in
#: percentage points. Two points is noise at this volume; ten is a decision.
ENGAGEMENT_GAP = 10.0

#: How far a channel's share has to move between windows to be a finding.
SHIFT_POINTS = 8.0

#: A page needs this many views before "nobody finished it" means anything.
MIN_PAGE_VIEWS = 25

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

#: The channels a post can be sent to, in the naming `classify_source` uses.
SOCIAL_CHANNELS = ("LinkedIn", "X", "Facebook", "Instagram", "WhatsApp")

#: Buffer names a platform in its own vocabulary; this maps it onto ours so one
#: channel is one row rather than two spellings of the same thing.
SOCIAL_PLATFORMS = {
    "linkedin": "LinkedIn",
    "twitter": "X",
    "x": "X",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "whatsapp": "WhatsApp",
}


def _num(value: Any) -> float | None:
    """A number, or None. A string that is not a number is not a zero."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _count(value: Any) -> str:
    number = _num(value)
    return "—" if number is None else f"{int(round(number)):,}"


def _pct(value: Any) -> str:
    """A GA4 proportion as a percentage. Rates arrive between 0 and 1."""
    number = _num(value)
    return "—" if number is None else f"{number * 100:.1f}%"


def _share(value: Any) -> str:
    number = _num(value)
    return "—" if number is None else f"{number:.0f}%"


def _points(value: Any) -> str:
    """A difference between two rates, in percentage *points*.

    Not percent. A move from 20.7% to 25.7% is five points and a quarter more
    engagement, and calling it "+5%" invites the second reading of the first
    number.
    """
    number = _num(value)
    if number is None:
        return "—"
    return f"{number:+.1f} points"


def _finding(
    kind: str,
    panel: str,
    subject: str,
    severity: str,
    headline: str,
    what: str,
    why: str,
    action: str,
    evidence: Sequence[str],
    *,
    sample: float | None,
) -> dict[str, Any]:
    """One finding, downgraded to an observation when the sample cannot carry it."""
    size = _num(sample)
    small = size is not None and size < MIN_SAMPLE
    return {
        "kind": kind,
        "panel": panel,
        # What the finding is about, so two rules that reach the same channel
        # from different directions collapse to one line. A CMO reading "Direct
        # grew" directly above "Direct does not engage" has one investigation to
        # run, not two, and printing it twice makes the shorter list look longer.
        "subject": subject,
        "severity": "low" if small else severity,
        "headline": headline,
        "what": what,
        "why": why,
        "action": "" if small else action,
        "evidence": list(evidence),
        "confidence": "too_small" if small else "measured",
        "sample": None if size is None else int(size),
        "caveat": (
            f"A sample of {_count(size)} is too small to act on; "
            "this is here to be watched, not decided."
            if small
            else ""
        ),
    }


def _site_engagement(ga4: dict[str, Any]) -> float | None:
    return _num((ga4.get("metrics") or {}).get("engagement_rate"))


# --------------------------------------------------------------------------
# The rules. Each takes what it needs, returns a list of 0 or 1 findings, and
# returns nothing at all when the figures it would quote were never measured.
# --------------------------------------------------------------------------


def unexpected_geography(geography: dict[str, Any], ga4: dict[str, Any]) -> list[dict[str, Any]]:
    """Traffic from outside the markets this business sells into.

    One finding for all of them rather than one each: two unexplained countries
    are one question -- is this an audience or is it noise -- and the answer is
    the same investigation either way.
    """
    countries = geography.get("countries") or []
    if not countries:
        return []
    site_rate = _site_engagement(ga4)
    suspects = [
        row
        for row in countries
        if not row.get("expected")
        and (_num(row.get("share")) or 0) >= MIN_SHARE
        and _num(row.get("sessions")) is not None
    ]
    if not suspects:
        return []
    names = [str(row["country"]) for row in suspects]
    sessions = sum(int(_num(row.get("sessions")) or 0) for row in suspects)
    share = sum(_num(row.get("share")) or 0 for row in suspects)
    listed = names[0] if len(names) == 1 else ", ".join(names[:-1]) + f" and {names[-1]}"

    evidence = []
    for row in suspects:
        rate = _num(row.get("engagement_rate"))
        was = row.get("previous_sessions")
        movement = (
            "new this window" if was is None else f"{_count(was)} last window"
        )
        evidence.append(
            f"{row['country']}: {_count(row.get('sessions'))} sessions "
            f"({_share(row.get('share'))} of all traffic), "
            f"{_pct(rate) if rate is not None else 'engagement not measured'}, {movement}."
        )

    rates = [_num(row.get("engagement_rate")) for row in suspects]
    measured = [rate for rate in rates if rate is not None]
    worst = min(measured) if measured else None
    if site_rate is not None and worst is not None and (site_rate - worst) * 100 >= ENGAGEMENT_GAP:
        why = (
            f"They engage at {_pct(worst)} against {_pct(site_rate)} across the site — "
            "the shape of traffic that arrives and leaves, not of readers."
        )
        severity = "high"
    elif worst is not None:
        why = (
            f"They engage at {_pct(worst)}, close enough to the site's {_pct(site_rate)} "
            "that this may be a real audience rather than noise."
        )
        severity = "medium"
    else:
        why = "Engagement was not measured for them, so nothing here says whether they read anything."
        severity = "medium"

    return [
        _finding(
            "unexpected_geography",
            "places",
            listed,
            severity,
            f"{listed} sent traffic we did not plan for",
            f"{listed} sent {_count(sessions)} sessions, {_share(share)} of everything "
            "recorded in this window, from outside the markets this business sells into.",
            why,
            "Open the country in GA4 and check the landing pages and hostnames behind it. "
            "If it is unattributed traffic to one page, add a filter to the property — "
            "every site-wide rate on this tab is being computed over it until you do.",
            evidence,
            sample=sessions,
        )
    ]


def channel_shift(audience: dict[str, Any]) -> list[dict[str, Any]]:
    """A channel whose share of sessions moved materially between windows."""
    current = audience.get("traffic_sources") or []
    previous = {row["source"]: row for row in audience.get("previous_traffic_sources") or []}
    if not current or not previous:
        return []
    moves = []
    for row in current:
        now = _num(row.get("share"))
        was = _num((previous.get(row["source"]) or {}).get("share"))
        if now is None or was is None:
            continue
        if abs(now - was) >= SHIFT_POINTS:
            moves.append((now - was, row, was))
    if not moves:
        return []
    moves.sort(key=lambda item: -abs(item[0]))
    change, row, was = moves[0]
    grew = change > 0
    return [
        _finding(
            "channel_shift",
            "sources",
            str(row["source"]),
            "medium",
            f"{row['source']} {'grew' if grew else 'shrank'} against the previous window",
            f"{row['source']} moved from {_share(was)} to {_share(row.get('share'))} of sessions, "
            f"{_points(change)}, on {_count(row.get('sessions'))} sessions this window.",
            (
                f"It now engages at {_pct(row.get('engagement_rate'))} over "
                f"{_count(row.get('sessions'))} sessions."
                if _num(row.get("engagement_rate")) is not None
                else "Engagement was not measured for it this window."
            ),
            (
                f"Find what changed. {row['source']} is now the channel most responsible for "
                "the movement in the tiles above, and reading any other panel before "
                "attributing this one will attribute it twice."
            ),
            [
                f"Seen as: {', '.join(row.get('examples') or []) or 'not recorded'}.",
                f"Other channels moved less than {SHIFT_POINTS:.0f} points.",
            ],
            sample=_num(row.get("sessions")),
        )
    ]


def _channel_against_site(
    audience: dict[str, Any], ga4: dict[str, Any], *, above: bool
) -> list[dict[str, Any]]:
    site_rate = _site_engagement(ga4)
    if site_rate is None:
        return []
    candidates = []
    for row in audience.get("traffic_sources") or []:
        rate = _num(row.get("engagement_rate"))
        sessions = _num(row.get("sessions"))
        share = _num(row.get("share"))
        if rate is None or sessions is None or (share or 0) < MIN_SHARE:
            continue
        gap = (rate - site_rate) * 100
        if (above and gap >= ENGAGEMENT_GAP) or (not above and -gap >= ENGAGEMENT_GAP):
            candidates.append((gap, row))
    if not candidates:
        return []
    candidates.sort(key=lambda item: -abs(item[0]))
    gap, row = candidates[0]
    if above:
        return [
            _finding(
                "high_intent_channel",
                "sources",
                str(row["source"]),
                "medium",
                f"{row['source']} sends the traffic that actually reads",
                f"{row['source']} sent {_count(row.get('sessions'))} sessions "
                f"({_share(row.get('share'))} of the total) and engaged "
                f"{_pct(row.get('engagement_rate'))} of them.",
                f"That is {_points(gap)} above the site's {_pct(site_rate)}, over "
                f"{_count(row.get('views_per_session'))} pages a session.",
                f"Post to {row['source']} more often. This is the one channel on the tab "
                "where more volume is measured to bring more reading, not just more sessions.",
                [
                    f"Seen as: {', '.join(row.get('examples') or []) or 'not recorded'}.",
                    f"Site engagement rate: {_pct(site_rate)}.",
                ],
                sample=_num(row.get("sessions")),
            )
        ]
    return [
        _finding(
            "low_engagement_channel",
            "sources",
            str(row["source"]),
            "medium",
            f"{row['source']} sends sessions that do not stay",
            f"{row['source']} sent {_count(row.get('sessions'))} sessions "
            f"({_share(row.get('share'))} of the total) and engaged only "
            f"{_pct(row.get('engagement_rate'))} of them.",
            f"That is {_points(gap)} against the site's {_pct(site_rate)}.",
            f"Look at where {row['source']} lands before spending anything more on it. "
            "A channel this far below the site rate is either pointed at the wrong page "
            "or is not the audience the post was written for.",
            [
                f"Seen as: {', '.join(row.get('examples') or []) or 'not recorded'}.",
                f"Site engagement rate: {_pct(site_rate)}.",
            ],
            sample=_num(row.get("sessions")),
        )
    ]


def high_intent_channel(audience: dict[str, Any], ga4: dict[str, Any]) -> list[dict[str, Any]]:
    return _channel_against_site(audience, ga4, above=True)


def low_engagement_channel(audience: dict[str, Any], ga4: dict[str, Any]) -> list[dict[str, Any]]:
    return _channel_against_site(audience, ga4, above=False)


def page_opportunity(pages: Sequence[dict[str, Any]], ga4: dict[str, Any]) -> list[dict[str, Any]]:
    """A page earning attention it is not being sent, or sent traffic it wastes."""
    site_rate = _site_engagement(ga4)
    if site_rate is None or not pages:
        return []
    rows = [
        row
        for row in pages
        if _num(row.get("screen_page_views")) is not None
        and _num(row.get("engagement_rate")) is not None
        and (_num(row.get("screen_page_views")) or 0) >= MIN_PAGE_VIEWS
    ]
    if not rows:
        return []
    ranked = sorted(rows, key=lambda row: -(_num(row.get("screen_page_views")) or 0))
    median_views = (_num(ranked[len(ranked) // 2].get("screen_page_views")) or 0)

    for row in sorted(rows, key=lambda row: -((_num(row.get("engagement_rate")) or 0) - site_rate)):
        rate = _num(row.get("engagement_rate")) or 0
        views = _num(row.get("screen_page_views")) or 0
        if (rate - site_rate) * 100 >= ENGAGEMENT_GAP and views <= median_views:
            return [
                _finding(
                    "page_opportunity",
                    "pages",
                    str(row["page"]),
                    "medium",
                    "One page holds people far better than the traffic it gets",
                    f"{row['page']} was viewed {_count(views)} times and engaged "
                    f"{_pct(rate)} of its sessions.",
                    f"That is {_points((rate - site_rate) * 100)} above the site's "
                    f"{_pct(site_rate)}, on below-median volume — it is under-read, "
                    "not under-performing.",
                    f"Promote {row['page']}. Link it from the pages that do get traffic, "
                    "and put it in the next social slot rather than writing something new.",
                    [
                        f"Sessions: {_count(row.get('sessions'))}.",
                        f"Visitors: {_count(row.get('active_users'))}.",
                        f"Median page views this window: {_count(median_views)}.",
                    ],
                    sample=_num(row.get("sessions")),
                )
            ]

    worst = min(rows, key=lambda row: _num(row.get("engagement_rate")) or 0)
    rate = _num(worst.get("engagement_rate")) or 0
    if (site_rate - rate) * 100 >= ENGAGEMENT_GAP:
        return [
            _finding(
                "page_opportunity",
                "pages",
                str(worst["page"]),
                "medium",
                "The traffic reaching one page is being wasted",
                f"{worst['page']} was viewed {_count(worst.get('screen_page_views'))} times "
                f"and engaged only {_pct(rate)} of its sessions.",
                f"That is {_points((rate - site_rate) * 100)} against the site's {_pct(site_rate)}.",
                f"Fix {worst['page']} before sending it anything more. It already receives "
                "the traffic; what it does with it is the problem.",
                [
                    f"Sessions: {_count(worst.get('sessions'))}.",
                    f"Visitors: {_count(worst.get('active_users'))}.",
                ],
                sample=_num(worst.get("sessions")),
            )
        ]
    return []


def device_gap(audience: dict[str, Any], ga4: dict[str, Any]) -> list[dict[str, Any]]:
    """Mobile carrying the volume and losing the readers."""
    devices = {row["device"]: row for row in audience.get("devices") or []}
    mobile, desktop = devices.get("mobile"), devices.get("desktop")
    if not mobile or not desktop:
        return []
    mobile_rate = _num(mobile.get("engagement_rate"))
    desktop_rate = _num(desktop.get("engagement_rate"))
    mobile_sessions = _num(mobile.get("sessions"))
    desktop_sessions = _num(desktop.get("sessions"))
    if None in (mobile_rate, desktop_rate, mobile_sessions, desktop_sessions):
        return []
    total = mobile_sessions + desktop_sessions
    if not total:
        return []
    gap = (desktop_rate - mobile_rate) * 100
    if gap < ENGAGEMENT_GAP or mobile_sessions < desktop_sessions:
        return []
    return [
        _finding(
            "device_gap",
            "devices",
            "mobile",
            "high",
            "Mobile brings the most sessions and keeps the fewest",
            f"Mobile sent {_count(mobile_sessions)} of {_count(total)} sessions and "
            f"engaged {_pct(mobile_rate)} of them; desktop engaged {_pct(desktop_rate)}.",
            f"A gap of {gap:.1f} points on the majority of traffic is a rendering or "
            "layout problem, not an audience one — the same pages hold desktop readers.",
            "Open the top landing pages on a phone before changing anything about the "
            "traffic. Every channel on this tab is mostly mobile, so this gap is "
            "subtracted from all of them.",
            [
                f"Mobile share: {_share(mobile_sessions * 100 / total)}.",
                f"Desktop sessions: {_count(desktop_sessions)}.",
            ],
            sample=mobile_sessions,
        )
    ]


def funnel_break(events: dict[str, Any]) -> list[dict[str, Any]]:
    """The step that loses the money path, or the step nobody wired up.

    The distinction is the whole point and it is already carried by the reader:
    `instrumented` false means no event has ever arrived, which is an engineering
    problem, and a measured zero means people left, which is a marketing one.
    """
    steps = events.get("funnel") or []
    if not steps:
        return []
    missing = [step for step in steps if not step.get("instrumented")]
    if missing:
        names = ", ".join(str(step["step"]) for step in missing)
        return [
            _finding(
                "funnel_break",
                "funnel",
                "funnel",
                "high",
                "Part of the lead path reports nothing at all",
                f"{names} has never been seen by Google Analytics in this window.",
                "A step with no event is not a step nobody reached. GTM forwards an event "
                "to GA4 only when the container holds a tag with a trigger for that name, "
                "so this reads as an unwired container, not as lost demand.",
                "Send this to engineering, not to marketing. Until the container carries a "
                "tag for these names, no conversion figure on this tab is complete.",
                [f"Steps reporting: {', '.join(str(s['step']) for s in steps if s.get('instrumented')) or 'none'}."],
                sample=None,
            )
        ]
    worst = None
    for index, step in enumerate(steps[1:], start=1):
        before = _num(steps[index - 1].get("count"))
        now = _num(step.get("count"))
        if before is None or now is None or before <= 0:
            continue
        lost = (before - now) / before * 100
        if worst is None or lost > worst[0]:
            worst = (lost, steps[index - 1], step)
    if worst is None or worst[0] < 50:
        return []
    lost, before, step = worst
    return [
        _finding(
            "funnel_break",
            "funnel",
            "funnel",
            "high",
            f"The lead path loses most people at {step['step']}",
            f"{_count(before.get('count'))} reached {before['step']} and "
            f"{_count(step.get('count'))} reached {step['step']} — {lost:.0f}% did not continue.",
            "Every step after this one is computed over what survives it, so this is the "
            "single largest constraint on leads from the site.",
            f"Fix {step['step']} before buying any more traffic. Doubling sessions doubles "
            "what arrives at this step and nothing that gets past it.",
            [
                f"{s['step']}: {_count(s.get('count'))}"
                for s in steps
                if _num(s.get("count")) is not None
            ],
            sample=_num(before.get("count")),
        )
    ]


def search_vs_analytics(posts: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """An article Google shows and nobody opens."""
    shown = [
        row
        for row in posts
        if (_num(row.get("impressions")) or 0) >= 100 and (_num(row.get("views")) or 0) == 0
    ]
    if not shown:
        return []
    shown.sort(key=lambda row: -(_num(row.get("impressions")) or 0))
    row = shown[0]
    return [
        _finding(
            "search_vs_analytics",
            "posts",
            str(row.get("slug") or row.get("title") or "article"),
            "medium",
            "An article Google shows and nobody opens",
            f"“{row.get('title') or row.get('slug')}” was shown "
            f"{_count(row.get('impressions'))} times in search and recorded "
            f"{_count(row.get('views'))} views.",
            "Search Console knows what Google displayed and Google Analytics knows what a "
            "browser loaded. Impressions without views means the page appears and then does "
            "not look like the answer.",
            "Rewrite the title and meta description for this article. The ranking is already "
            "paid for; the click is what is missing.",
            [
                f"Clicks: {_count(row.get('clicks'))}.",
                f"Average position: {_count(row.get('position'))}.",
            ],
            sample=_num(row.get("impressions")),
        )
    ]


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def findings(
    *,
    ga4: dict[str, Any] | None = None,
    audience: dict[str, Any] | None = None,
    geography: dict[str, Any] | None = None,
    events: dict[str, Any] | None = None,
    pages: Sequence[dict[str, Any]] = (),
    posts: Sequence[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Every rule, run over what was measured, ordered by what to read first."""
    ga4 = ga4 or {}
    audience = audience or {}
    geography = geography or {}
    events = events or {}
    if ga4.get("status") not in {"ready", "collecting"}:
        return []
    found: list[dict[str, Any]] = []
    found += unexpected_geography(geography, ga4)
    found += funnel_break(events)
    found += device_gap(audience, ga4)
    found += channel_shift(audience)
    found += high_intent_channel(audience, ga4)
    found += low_engagement_channel(audience, ga4)
    found += page_opportunity(pages, ga4)
    found += search_vs_analytics(posts)
    found.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(item["severity"], 3),
            -(item.get("sample") or 0),
        )
    )
    seen: set[tuple[str, str]] = set()
    unique = []
    for item in found:
        key = (item["panel"], item["subject"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def executive_summary(
    found: Sequence[dict[str, Any]],
    ga4: dict[str, Any] | None = None,
    events: dict[str, Any] | None = None,
    *,
    range_days: int = 28,
) -> dict[str, Any]:
    """What happened, why, and what to do — in that order and no other.

    `caveats` is not a disclaimer. When there is no previous window the honest
    summary is that nothing here is a trend yet, and a summary that omitted that
    would read as one.
    """
    ga4 = ga4 or {}
    events = events or {}
    metrics = ga4.get("metrics") or {}
    deltas = ga4.get("deltas") or {}
    previous = ga4.get("previous") or {}
    connected = ga4.get("status") in {"ready", "collecting"}

    what: list[str] = []
    if connected:
        sessions = _num(metrics.get("sessions"))
        users = _num(metrics.get("active_users"))
        rate = _num(metrics.get("engagement_rate"))
        if sessions is not None:
            move = _num(deltas.get("sessions"))
            what.append(
                f"{_count(sessions)} sessions from {_count(users)} visitors over "
                f"{range_days} days"
                + (f", {_count(abs(move))} {'more' if move >= 0 else 'fewer'} than the "
                   f"window before it." if move is not None else ".")
            )
        if rate is not None:
            move = _num(deltas.get("engagement_rate"))
            what.append(
                f"{_pct(rate)} of those sessions engaged"
                + (
                    f", {_points(move * 100)} against {_pct(previous.get('engagement_rate'))}."
                    if move is not None
                    else "."
                )
            )
        # Key events come from `ga4_events`, which asks for them in its own
        # request: GA4 renamed `conversions` to `keyEvents` and a property answers
        # to one name or the other, so they are never in the summary metrics.
        events_total = _num(events.get("key_events"))
        if events_total is not None:
            what.append(f"{_count(events_total)} key events were recorded.")

    why = [
        f"{item['headline']}. {item['why']}"
        for item in found
        if item["confidence"] == "measured"
    ][:3]

    actions = [
        {"action": item["action"], "kind": item["kind"], "panel": item["panel"]}
        for item in found
        if item["action"]
    ][:3]

    caveats: list[str] = []
    if not connected:
        caveats.append(
            ga4.get("message")
            or "Google Analytics is not connected, so nothing on this tab is measured yet."
        )
    elif not any(_num(value) is not None for value in previous.values()):
        caveats.append(
            "There is no previous window to compare against, so every figure here is a "
            "level and none of them is yet a trend."
        )
    watched = [item for item in found if item["confidence"] == "too_small"]
    if watched:
        caveats.append(
            f"{len(watched)} finding{'s' if len(watched) > 1 else ''} sit below "
            f"{MIN_SAMPLE} sessions and are shown to be watched, not acted on."
        )
    if connected and not found:
        why = ["Nothing crossed a threshold this window."]

    return {"what": what, "why": why, "actions": actions, "caveats": caveats}


def campaign_performance(
    audience: dict[str, Any] | None,
    sent: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    """How the posts we sent performed — as far as anything here can measure it.

    This is an arrival-side measurement and says so. Sessions, visitors and
    engagement are what GA4 recorded landing on the site; impressions, clicks and
    CTR are what the platform recorded before that, and no credential in this
    profile can read them. They stay `None` with the reason attached rather than
    rendering as zero, because a zero here would read as a post that reached
    nobody.
    """
    audience = audience or {}
    by_channel = {row["source"]: row for row in audience.get("traffic_sources") or []}
    posted: dict[str, int] = {}
    for row in sent:
        platform = str(row.get("platform") or "").strip()
        if platform:
            posted[SOCIAL_PLATFORMS.get(platform.casefold(), platform.title())] = (
                posted.get(SOCIAL_PLATFORMS.get(platform.casefold(), platform.title()), 0) + 1
            )
    rows = []
    for channel in SOCIAL_CHANNELS:
        arrival = by_channel.get(channel)
        if arrival is None and channel not in posted:
            continue
        rows.append(
            {
                "channel": channel,
                "posts_sent": posted.get(channel),
                "sessions": (arrival or {}).get("sessions"),
                "active_users": (arrival or {}).get("active_users"),
                "engagement_rate": (arrival or {}).get("engagement_rate"),
                "views_per_session": (arrival or {}).get("views_per_session"),
                "impressions": None,
                "clicks": None,
                "ctr": None,
                "engagements": None,
            }
        )
    rows.sort(key=lambda row: -(_num(row.get("sessions")) or 0))
    return {
        "rows": rows,
        "measured": "Google Analytics, on arrival",
        "unavailable": ["impressions", "clicks", "ctr", "engagements"],
        "unavailable_reason": (
            "Impressions, clicks, CTR and engagements are recorded by the platform, not by "
            "this site, and no credential in this profile can read them. LinkedIn needs an "
            "app with organization access and a LINKEDIN_ACCESS_TOKEN; until one exists "
            "these stay blank rather than showing a zero that would read as a post nobody saw."
        ),
    }

