"""The rules that turn measured numbers into a recommendation.

Every test here asserts on the sentence a CMO would read, not on a dict key.
A finding whose prose says something the numbers do not support is the failure
this module exists to prevent, and a structural assertion would pass through it.

Three properties are checked over and over because they are the ones that make a
rule engine trustworthy rather than merely confident:

* an unmeasured input produces **no finding**, not a hedged one,
* a real `0` survives as a `0` and still supports a finding,
* a sample too small to act on keeps its numbers and loses its recommendation.
"""

from __future__ import annotations

import unittest

import ceo_insights as insights

READY = {
    "status": "ready",
    "metrics": {"sessions": 341, "active_users": 268, "engagement_rate": 0.207},
    "previous": {"sessions": 300, "active_users": 240, "engagement_rate": 0.252},
    "deltas": {"sessions": 41, "active_users": 28, "engagement_rate": -0.045},
}


def country(name, sessions, share, rate, *, expected=False, previous=None):
    return {
        "country": name,
        "sessions": sessions,
        "share": share,
        "engagement_rate": rate,
        "expected": expected,
        "previous_sessions": previous,
        "delta_sessions": None if previous is None else sessions - previous,
    }


def channel(source, sessions, share, rate, *, views=2.0, examples=()):
    return {
        "source": source,
        "sessions": sessions,
        "share": share,
        "engagement_rate": rate,
        "views_per_session": views,
        "examples": list(examples),
    }


class UnexpectedGeography(unittest.TestCase):
    def test_two_unexplained_countries_are_one_question_and_one_finding(self) -> None:
        """Netherlands and Poland are not two investigations.

        The answer -- audience or noise -- is reached the same way for both, and
        two findings would make the action list look twice as long as the work.
        """
        geography = {
            "countries": [
                country("India", 250, 73.3, 0.28, expected=True, previous=280),
                country("Netherlands", 41, 12.0, 0.049),
                country("Poland", 22, 6.5, 0.045),
            ]
        }

        found = insights.unexpected_geography(geography, READY)

        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding["headline"], "Netherlands and Poland sent traffic we did not plan for")
        self.assertIn("63 sessions", finding["what"])
        self.assertIn("18%", finding["what"])
        self.assertIn("4.5% against 20.7%", finding["why"])
        self.assertIn("add a filter to the property", finding["action"])
        # The evidence has to name each country separately, because "which one"
        # is the first question anyone reading this asks.
        self.assertEqual(len(finding["evidence"]), 2)
        self.assertIn("new this window", finding["evidence"][0])

    def test_a_country_we_sell_into_is_never_a_finding_however_it_moves(self) -> None:
        geography = {"countries": [country("India", 300, 100.0, 0.05, expected=True, previous=100)]}

        self.assertEqual(insights.unexpected_geography(geography, READY), [])

    def test_engagement_close_to_the_site_reads_as_an_audience_not_as_noise(self) -> None:
        """The rule refuses to call traffic junk on volume alone."""
        geography = {"countries": [country("Singapore", 60, 18.0, 0.19)]}

        finding = insights.unexpected_geography(geography, READY)[0]

        self.assertEqual(finding["severity"], "medium")
        self.assertIn("may be a real audience rather than noise", finding["why"])

    def test_unmeasured_engagement_says_so_rather_than_concluding(self) -> None:
        geography = {"countries": [country("Poland", 60, 18.0, None)]}

        finding = insights.unexpected_geography(geography, READY)[0]

        self.assertIn("was not measured", finding["why"])
        self.assertIn("engagement not measured", finding["evidence"][0])

    def test_a_country_below_the_share_floor_is_left_to_the_table(self) -> None:
        geography = {"countries": [country("Poland", 4, 1.2, 0.01)]}

        self.assertEqual(insights.unexpected_geography(geography, READY), [])


class SampleSize(unittest.TestCase):
    def test_a_small_sample_keeps_its_numbers_and_loses_its_recommendation(self) -> None:
        """20.7% of 29 sessions is six sessions.

        The percentage is real; the trend it implies is not. The finding stays on
        screen because the number is worth watching, and the action goes because
        acting on it would be acting on six sessions.
        """
        geography = {"countries": [country("Poland", 20, 22.0, 0.01)]}

        finding = insights.unexpected_geography(geography, READY)[0]

        self.assertEqual(finding["confidence"], "too_small")
        self.assertEqual(finding["severity"], "low")
        self.assertEqual(finding["action"], "")
        self.assertIn("20 sessions", finding["what"])
        self.assertIn("too small to act on", finding["caveat"])

    def test_a_sample_above_the_floor_keeps_its_recommendation(self) -> None:
        geography = {"countries": [country("Poland", 41, 22.0, 0.01)]}

        finding = insights.unexpected_geography(geography, READY)[0]

        self.assertEqual(finding["confidence"], "measured")
        self.assertTrue(finding["action"])
        self.assertEqual(finding["caveat"], "")


class Channels(unittest.TestCase):
    def test_a_channel_above_the_site_rate_is_told_to_do_more(self) -> None:
        audience = {
            "traffic_sources": [
                channel("LinkedIn", 51, 15.0, 0.42, views=3.1, examples=["lnkd.in"]),
                channel("Direct", 150, 44.0, 0.20),
            ]
        }

        finding = insights.high_intent_channel(audience, READY)[0]

        self.assertEqual(finding["headline"], "LinkedIn sends the traffic that actually reads")
        self.assertIn("51 sessions", finding["what"])
        self.assertIn("42.0%", finding["what"])
        self.assertIn("+21.3 points", finding["why"])
        self.assertIn("Post to LinkedIn more often", finding["action"])

    def test_a_channel_below_the_site_rate_is_told_where_to_look_first(self) -> None:
        audience = {"traffic_sources": [channel("Direct", 150, 44.0, 0.06, examples=["(direct)"])]}

        finding = insights.low_engagement_channel(audience, READY)[0]

        self.assertIn("engaged only 6.0%", finding["what"])
        self.assertIn("-14.7 points", finding["why"])
        self.assertIn("before spending anything more on it", finding["action"])

    def test_a_channel_without_a_measured_rate_produces_nothing(self) -> None:
        """Not a hedge and not a zero -- nothing.

        A channel nobody instrumented and a channel nobody engaged with are
        opposite findings, and only one of them is a marketing problem.
        """
        audience = {"traffic_sources": [channel("Email", 200, 60.0, None)]}

        self.assertEqual(insights.high_intent_channel(audience, READY), [])
        self.assertEqual(insights.low_engagement_channel(audience, READY), [])

    def test_a_measured_zero_still_supports_a_finding(self) -> None:
        audience = {"traffic_sources": [channel("Referral", 90, 26.0, 0.0)]}

        finding = insights.low_engagement_channel(audience, READY)[0]

        self.assertIn("engaged only 0.0%", finding["what"])

    def test_nothing_is_concluded_when_the_site_rate_itself_is_unmeasured(self) -> None:
        blank = {"status": "ready", "metrics": {"engagement_rate": None}}
        audience = {"traffic_sources": [channel("LinkedIn", 90, 26.0, 0.9)]}

        self.assertEqual(insights.high_intent_channel(audience, blank), [])

    def test_a_share_that_moved_names_the_points_not_a_percentage(self) -> None:
        """A move from 30% to 44% is fourteen points, not "+14%".

        "+14%" reads as a relative gain and is a different, smaller number.
        """
        audience = {
            "traffic_sources": [channel("Direct", 150, 44.0, 0.06, examples=["(direct)"])],
            "previous_traffic_sources": [channel("Direct", 90, 30.0, 0.10)],
        }

        finding = insights.channel_shift(audience)[0]

        self.assertIn("+14.0 points", finding["what"])
        self.assertIn("from 30% to 44%", finding["what"])

    def test_no_previous_window_means_no_movement_to_report(self) -> None:
        audience = {"traffic_sources": [channel("Direct", 150, 44.0, 0.06)]}

        self.assertEqual(insights.channel_shift(audience), [])


class Funnel(unittest.TestCase):
    def test_a_step_with_no_event_is_an_engineering_finding_not_a_marketing_one(self) -> None:
        """The distinction the whole funnel is built on.

        "Nobody converted" sends a CMO to marketing. "Nothing reports a
        conversion" sends them to engineering, and a zero would send them to the
        wrong department.
        """
        events = {
            "funnel": [
                {"step": "Calculator started", "count": 52, "instrumented": True},
                {"step": "OTP requested", "count": None, "instrumented": False},
            ]
        }

        finding = insights.funnel_break(events)[0]

        self.assertIn("has never been seen by Google Analytics", finding["what"])
        self.assertIn("unwired container", finding["why"])
        self.assertIn("Send this to engineering, not to marketing", finding["action"])

    def test_a_measured_collapse_is_a_marketing_finding(self) -> None:
        events = {
            "funnel": [
                {"step": "Calculator started", "count": 520, "instrumented": True},
                {"step": "OTP requested", "count": 40, "instrumented": True},
            ]
        }

        finding = insights.funnel_break(events)[0]

        self.assertIn("92% did not continue", finding["what"])
        self.assertIn("Fix OTP requested", finding["action"])

    def test_a_funnel_that_holds_its_people_reports_nothing(self) -> None:
        events = {
            "funnel": [
                {"step": "Calculator started", "count": 100, "instrumented": True},
                {"step": "OTP requested", "count": 80, "instrumented": True},
            ]
        }

        self.assertEqual(insights.funnel_break(events), [])


class Devices(unittest.TestCase):
    def test_mobile_carrying_the_volume_and_losing_the_readers_is_a_render_finding(self) -> None:
        audience = {
            "devices": [
                {"device": "mobile", "sessions": 230, "engagement_rate": 0.14},
                {"device": "desktop", "sessions": 100, "engagement_rate": 0.35},
            ]
        }

        finding = insights.device_gap(audience, READY)[0]

        self.assertIn("230 of 330 sessions", finding["what"])
        self.assertIn("gap of 21.0 points", finding["why"])
        self.assertIn("rendering or layout problem", finding["why"])
        self.assertEqual(finding["severity"], "high")

    def test_a_minority_of_mobile_traffic_is_not_this_finding(self) -> None:
        audience = {
            "devices": [
                {"device": "mobile", "sessions": 40, "engagement_rate": 0.14},
                {"device": "desktop", "sessions": 200, "engagement_rate": 0.35},
            ]
        }

        self.assertEqual(insights.device_gap(audience, READY), [])

    def test_one_device_missing_its_rate_produces_nothing(self) -> None:
        audience = {
            "devices": [
                {"device": "mobile", "sessions": 230, "engagement_rate": None},
                {"device": "desktop", "sessions": 100, "engagement_rate": 0.35},
            ]
        }

        self.assertEqual(insights.device_gap(audience, READY), [])


class Pages(unittest.TestCase):
    def test_a_page_read_far_better_than_it_is_promoted_is_told_to_be_promoted(self) -> None:
        pages = [
            {"page": "/blog/cost", "screen_page_views": 300, "sessions": 250,
             "engagement_rate": 0.19, "active_users": 200},
            {"page": "/products", "screen_page_views": 60, "sessions": 50,
             "engagement_rate": 0.62, "active_users": 45},
            {"page": "/about", "screen_page_views": 40, "sessions": 35,
             "engagement_rate": 0.21, "active_users": 30},
        ]

        finding = insights.page_opportunity(pages, READY)[0]

        self.assertIn("/products", finding["what"])
        self.assertIn("under-read, not under-performing", finding["why"])
        self.assertIn("Promote /products", finding["action"])

    def test_a_page_wasting_the_traffic_it_gets_is_told_to_be_fixed_first(self) -> None:
        pages = [
            {"page": "/blog/cost", "screen_page_views": 300, "sessions": 250,
             "engagement_rate": 0.04, "active_users": 200},
            {"page": "/about", "screen_page_views": 40, "sessions": 35,
             "engagement_rate": 0.22, "active_users": 30},
        ]

        finding = insights.page_opportunity(pages, READY)[0]

        self.assertIn("being wasted", finding["headline"])
        self.assertIn("Fix /blog/cost before sending it anything more", finding["action"])

    def test_a_page_below_the_view_floor_is_not_evidence_of_anything(self) -> None:
        pages = [{"page": "/rare", "screen_page_views": 3, "sessions": 3,
                  "engagement_rate": 0.0, "active_users": 3}]

        self.assertEqual(insights.page_opportunity(pages, READY), [])


class SearchAgainstAnalytics(unittest.TestCase):
    def test_shown_and_never_opened_is_a_title_finding(self) -> None:
        posts = [{"title": "Repair or Replacement", "slug": "repair",
                  "impressions": 420, "views": 0, "clicks": 0, "position": 18.2}]

        finding = insights.search_vs_analytics(posts)[0]

        self.assertIn("shown 420 times in search", finding["what"])
        self.assertIn("does not look like the answer", finding["why"])
        self.assertIn("Rewrite the title", finding["action"])

    def test_an_article_nobody_has_impressions_for_is_not_a_finding(self) -> None:
        posts = [{"title": "New", "slug": "new", "impressions": None, "views": None}]

        self.assertEqual(insights.search_vs_analytics(posts), [])


class Assembly(unittest.TestCase):
    def _payloads(self):
        return {
            "ga4": READY,
            "audience": {
                "traffic_sources": [
                    channel("Direct", 150, 44.0, 0.06, examples=["(direct)"]),
                    channel("LinkedIn", 51, 15.0, 0.42, views=3.1),
                ],
                "previous_traffic_sources": [channel("Direct", 90, 30.0, 0.10)],
                "devices": [
                    {"device": "mobile", "sessions": 230, "engagement_rate": 0.14},
                    {"device": "desktop", "sessions": 100, "engagement_rate": 0.35},
                ],
            },
            "geography": {"countries": [country("Netherlands", 41, 12.0, 0.049)]},
            "events": {"key_events": 4, "funnel": []},
            "pages": [],
            "posts": [],
        }

    def test_one_channel_reached_by_two_rules_is_still_one_line(self) -> None:
        """Direct grew *and* Direct does not engage is one investigation.

        Printing both makes a short list look long, and a CMO reading two lines
        about the same channel runs the same check twice.
        """
        found = insights.findings(**self._payloads())

        directs = [item for item in found if item["subject"] == "Direct"]
        self.assertEqual(len(directs), 1)
        # LinkedIn is a different subject and keeps its own finding.
        self.assertTrue([item for item in found if item["subject"] == "LinkedIn"])

    def test_the_most_severe_finding_is_read_first(self) -> None:
        found = insights.findings(**self._payloads())

        self.assertEqual(found[0]["severity"], "high")

    def test_an_unconnected_property_concludes_nothing_at_all(self) -> None:
        payloads = self._payloads()
        payloads["ga4"] = {"status": "not_connected", "metrics": {}}

        self.assertEqual(insights.findings(**payloads), [])


class ExecutiveSummary(unittest.TestCase):
    def test_it_answers_what_then_why_then_what_to_do(self) -> None:
        found = insights.findings(
            ga4=READY,
            audience={
                "devices": [
                    {"device": "mobile", "sessions": 230, "engagement_rate": 0.14},
                    {"device": "desktop", "sessions": 100, "engagement_rate": 0.35},
                ]
            },
            geography={"countries": [country("Netherlands", 41, 12.0, 0.049)]},
            events={"key_events": 4, "funnel": []},
        )

        summary = insights.executive_summary(found, READY, {"key_events": 4}, range_days=28)

        self.assertIn("341 sessions from 268 visitors over 28 days", summary["what"][0])
        self.assertIn("41 more than the window before it", summary["what"][0])
        self.assertIn("-4.5 points", summary["what"][1])
        self.assertIn("4 key events were recorded.", summary["what"])
        self.assertTrue(summary["why"])
        self.assertTrue(summary["actions"])
        self.assertLessEqual(len(summary["actions"]), 3)

    def test_no_previous_window_is_stated_rather_than_implied(self) -> None:
        """A level is not a trend, and a summary that omitted this would read as one."""
        ga4 = {
            "status": "ready",
            "metrics": {"sessions": 41, "active_users": 30, "engagement_rate": 0.2},
            "previous": {"sessions": None, "engagement_rate": None},
            "deltas": {},
        }

        summary = insights.executive_summary([], ga4)

        self.assertIn(
            "no previous window to compare against", " ".join(summary["caveats"])
        )
        self.assertIn("Nothing crossed a threshold this window.", summary["why"])

    def test_watched_findings_are_counted_in_the_caveats(self) -> None:
        found = insights.findings(
            ga4=READY,
            geography={"countries": [country("Poland", 20, 22.0, 0.01)]},
        )

        summary = insights.executive_summary(found, READY)

        self.assertIn("below 30 sessions", " ".join(summary["caveats"]))
        self.assertEqual(summary["actions"], [])

    def test_an_unconnected_property_says_so_instead_of_summarising(self) -> None:
        summary = insights.executive_summary([], {"status": "not_connected", "message": "not wired"})

        self.assertEqual(summary["what"], [])
        self.assertIn("not wired", summary["caveats"])


class CampaignPerformance(unittest.TestCase):
    def test_what_is_measured_is_reported_and_what_is_not_stays_blank(self) -> None:
        """A zero here would read as a post that reached nobody.

        Impressions are recorded by the platform and no credential in this
        profile can read them, which is a different statement from "none".
        """
        audience = {"traffic_sources": [channel("LinkedIn", 51, 15.0, 0.42, views=3.1)]}

        result = insights.campaign_performance(
            audience, [{"platform": "linkedin"}, {"platform": "linkedin"}]
        )

        row = result["rows"][0]
        self.assertEqual(row["channel"], "LinkedIn")
        self.assertEqual(row["posts_sent"], 2)
        self.assertEqual(row["sessions"], 51)
        self.assertEqual(row["engagement_rate"], 0.42)
        self.assertIsNone(row["impressions"])
        self.assertIsNone(row["ctr"])
        self.assertIn("LINKEDIN_ACCESS_TOKEN", result["unavailable_reason"])
        self.assertIn("impressions", result["unavailable"])

    def test_buffer_platform_names_are_folded_onto_our_channel_names(self) -> None:
        """One channel is one row, not two spellings of the same thing."""
        result = insights.campaign_performance({}, [{"platform": "twitter"}, {"platform": "x"}])

        rows = {row["channel"]: row for row in result["rows"]}
        self.assertEqual(rows["X"]["posts_sent"], 2)

    def test_a_channel_that_sent_nothing_and_delivered_nothing_is_not_a_row(self) -> None:
        result = insights.campaign_performance({}, [])

        self.assertEqual(result["rows"], [])
