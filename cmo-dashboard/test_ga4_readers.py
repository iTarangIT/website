"""The Google Analytics readers behind the Analytics tab's tiles and panels.

Every test here drives the real reader with a stubbed transport, so what is
asserted is what the console would be handed: the shape of the request that goes
out, and the payload that comes back.

Two rules run through all of it. A figure that was not measured is `None` and
never `0` -- "nobody did this" and "this was never wired up" are opposite
findings and only one of them is a marketing problem. And a failure in any one
panel must leave the others standing, because a provider hiccup that blanks the
whole tab is worse than the panel it took down.
"""

from __future__ import annotations

import os
import unittest
from typing import Any
from unittest import mock

import analytics_readers as readers

ENVIRONMENT = {
    "GA4_PROPERTY_ID": "properties/1",
    "GA4_CREDENTIALS_PATH": "/dev/null",
    "GA4_MEASUREMENT_ID": "G-TEST",
    "GA4_TAG_INSTALLED": "1",
}


def metric_row(*values: str, dimensions: tuple[str, ...] = ()) -> dict[str, Any]:
    row: dict[str, Any] = {"metricValues": [{"value": value} for value in values]}
    if dimensions:
        row["dimensionValues"] = [{"value": value} for value in dimensions]
    return row


def summary_response(*values: str) -> dict[str, Any]:
    return {"rows": [metric_row(*values)]}


# A full ten-metric summary row, in GA4_SUMMARY_METRICS order.
READY = summary_response(
    "24",     # activeUsers
    "29",     # sessions
    "46",     # screenPageViews
    "0.207",  # engagementRate
    "18",     # newUsers
    "6",      # engagedSessions
    "72.4",   # averageSessionDuration
    "1.586",  # screenPageViewsPerSession
    "0.793",  # bounceRate
    "1.208",  # sessionsPerUser
)


class ReaderCase(unittest.TestCase):
    def setUp(self) -> None:
        for cache in (
            readers._ga4_cache,
            readers._ga4_detail_cache,
            readers._ga4_audience_cache,
            readers._ga4_events_cache,
            readers._ga4_geography_cache,
        ):
            cache.clear()
        patcher = mock.patch.dict(os.environ, ENVIRONMENT, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)


class SummaryMetrics(ReaderCase):
    def test_each_value_lands_on_its_own_key(self) -> None:
        """The one bug this pairing exists to prevent.

        `_ga4_values` reads metric values back by position. If the request's
        metric list and the payload's key order ever disagree, every tile shows
        its neighbour's number -- plausibly, and with nothing on screen to say
        so. Asserting the whole mapping at once is the only way to catch a
        one-place shift.
        """
        with mock.patch.object(readers, "_ga4_request", return_value=READY):
            result = readers.ga4_summary(28)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["metrics"]["active_users"], 24)
        self.assertEqual(result["metrics"]["sessions"], 29)
        self.assertEqual(result["metrics"]["screen_page_views"], 46)
        self.assertEqual(result["metrics"]["engagement_rate"], 0.207)
        self.assertEqual(result["metrics"]["new_users"], 18)
        self.assertEqual(result["metrics"]["engaged_sessions"], 6)
        self.assertEqual(result["metrics"]["average_session_duration"], 72.4)
        self.assertEqual(result["metrics"]["screen_page_views_per_session"], 1.586)
        self.assertEqual(result["metrics"]["bounce_rate"], 0.793)
        self.assertEqual(result["metrics"]["sessions_per_user"], 1.208)

    def test_the_request_asks_for_the_metrics_the_keys_promise(self) -> None:
        calls: list[dict[str, Any]] = []

        def capture(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
            calls.append(payload)
            return READY

        with mock.patch.object(readers, "_ga4_request", side_effect=capture):
            readers.ga4_summary(28)

        asked = [metric["name"] for metric in calls[0]["metrics"]]
        self.assertEqual(asked, [name for _, name in readers.GA4_SUMMARY_METRICS])
        # The GA4 Data API refuses a runReport carrying more than ten metrics,
        # and a request rejected outright takes every tile with it.
        self.assertLessEqual(len(asked), 10)

    def test_engagement_rate_is_left_as_the_ratio_google_reported(self) -> None:
        """The reader does not format. 0.207 stays 0.207 here and becomes
        "20.7%" in `figure(value,'rate')`, so one console-wide rule decides how
        every ratio reads."""
        with mock.patch.object(readers, "_ga4_request", return_value=READY):
            result = readers.ga4_summary(28)

        self.assertEqual(result["metrics"]["engagement_rate"], 0.207)

    def test_returning_visitors_are_the_difference_not_a_second_request(self) -> None:
        with mock.patch.object(readers, "_ga4_request", return_value=READY):
            result = readers.ga4_summary(28)

        self.assertEqual(result["metrics"]["returning_users"], 6)

    def test_returning_visitors_are_unmeasured_when_either_half_is(self) -> None:
        partial = summary_response("24", "29", "46", "0.207")  # newUsers absent
        with mock.patch.object(readers, "_ga4_request", return_value=partial):
            result = readers.ga4_summary(28)

        self.assertIsNone(result["metrics"]["new_users"])
        self.assertIsNone(result["metrics"]["returning_users"])

    def test_a_silent_property_reports_nothing_rather_than_zeros(self) -> None:
        with mock.patch.object(readers, "_ga4_request", return_value={"rows": []}):
            result = readers.ga4_summary(28)

        self.assertEqual(result["status"], "collecting")
        for key in readers.GA4_METRIC_KEYS:
            self.assertIsNone(result["metrics"][key], key)


class Channels(ReaderCase):
    def test_engagement_is_rebuilt_from_counts_not_averaged_across_rows(self) -> None:
        """Two LinkedIn referrers fold into one channel.

        Averaging their rates would weight a 2-session referrer the same as a
        200-session one. The fold sums the counts GA4 measured and divides once.
        """
        folded = readers._fold_sources([
            {"sessionSource": "linkedin.com", "sessionMedium": "referral",
             "sessions": 200, "activeUsers": 180, "engagedSessions": 100,
             "screenPageViews": 400},
            {"sessionSource": "lnkd.in", "sessionMedium": "referral",
             "sessions": 2, "activeUsers": 2, "engagedSessions": 2,
             "screenPageViews": 8},
        ])

        self.assertEqual(len(folded), 1)
        self.assertEqual(folded[0]["source"], "LinkedIn")
        self.assertEqual(folded[0]["sessions"], 202)
        # 102/202, not the mean of 0.5 and 1.0.
        self.assertAlmostEqual(folded[0]["engagement_rate"], 102 / 202)
        self.assertAlmostEqual(folded[0]["views_per_session"], round(408 / 202, 2))

    def test_a_channel_with_no_session_reports_no_rate(self) -> None:
        folded = readers._fold_sources([
            {"sessionSource": "example.com", "sessionMedium": "referral",
             "sessions": 0, "activeUsers": 0, "engagedSessions": 0,
             "screenPageViews": 0},
        ])

        self.assertIsNone(folded[0]["engagement_rate"])
        self.assertIsNone(folded[0]["views_per_session"])
        self.assertIsNone(folded[0]["share"])

    def test_first_touch_folds_through_the_same_channel_rules(self) -> None:
        folded = readers._fold_sources(
            [{"firstUserSource": "lnkd.in", "firstUserMedium": "referral",
              "sessions": 5, "activeUsers": 5, "engagedSessions": 3,
              "screenPageViews": 9}],
            source_key="firstUserSource",
            medium_key="firstUserMedium",
        )

        self.assertEqual(folded[0]["source"], "LinkedIn")
        self.assertEqual(folded[0]["examples"], ["lnkd.in"])


class Funnel(ReaderCase):
    def test_a_step_no_event_reached_is_uninstrumented_not_zero(self) -> None:
        steps = readers._funnel_from_counts({})

        self.assertEqual([step["step"] for step in steps],
                         [label for label, _ in readers.GA4_FUNNEL_STEPS])
        for step in steps:
            self.assertIsNone(step["count"], step["event"])
            self.assertFalse(step["instrumented"])
            self.assertIsNone(step["retention"])

    def test_retention_is_measured_against_the_step_above(self) -> None:
        steps = readers._funnel_from_counts({
            "calculator_start": 100,
            "otp_requested": 40,
            "otp_verified": 30,
            "generate_lead": 27,
        })

        self.assertEqual([step["retention"] for step in steps], [None, 40.0, 75.0, 90.0])

    def test_a_real_zero_survives_as_a_zero(self) -> None:
        """A step GA4 reported as 0 is a genuine measurement and must not be
        laundered into "not instrumented"."""
        steps = readers._funnel_from_counts({"calculator_start": 10, "otp_requested": 0})

        self.assertEqual(steps[1]["count"], 0)
        self.assertTrue(steps[1]["instrumented"])
        self.assertEqual(steps[1]["retention"], 0.0)


class Events(ReaderCase):
    def _responses(self, *, key_metric: str | None) -> Any:
        events = {"rows": [
            metric_row("120", "80", dimensions=("page_view",)),
            metric_row("9", "7", dimensions=("generate_lead",)),
        ]}

        summary_names = [name for _, name in readers.GA4_SUMMARY_METRICS]

        def respond(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
            names = [metric["name"] for metric in payload.get("metrics", [])]
            if names == summary_names:
                return READY
            if "eventCount" in names and payload.get("dimensions"):
                return events
            if key_metric and names and names[0] == key_metric:
                return summary_response("9", "0.31")
            # A property that answers to neither key-event name rejects the
            # request outright, exactly as the live API does.
            raise RuntimeError(f"unknown metric {names}")

        return respond

    def test_the_events_a_visitor_fired_reach_the_console(self) -> None:
        with mock.patch.object(readers, "_ga4_request",
                               side_effect=self._responses(key_metric="keyEvents")):
            result = readers.ga4_events(28)

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["events"][1]["event"], "generate_lead")
        self.assertEqual(result["events"][1]["count"], 9)
        self.assertTrue(result["events"][1]["intent"])
        self.assertFalse(result["events"][0]["intent"], "page_view is not intent")
        self.assertTrue(result["instrumented"])
        self.assertEqual(result["key_events"], 9)
        self.assertEqual(result["session_key_event_rate"], 0.31)

    def test_a_property_on_the_older_name_still_reports_key_events(self) -> None:
        """GA4 renamed `conversions` to `keyEvents`, and which name a property
        answers to depends on when it was created. Asking for the wrong one is a
        400 for the whole request, so both are tried."""
        with mock.patch.object(readers, "_ga4_request",
                               side_effect=self._responses(key_metric="conversions")):
            result = readers.ga4_events(28)

        self.assertEqual(result["key_events"], 9)
        self.assertEqual(result["key_event_message"], "")

    def test_neither_name_working_leaves_the_events_standing(self) -> None:
        with mock.patch.object(readers, "_ga4_request",
                               side_effect=self._responses(key_metric=None)):
            result = readers.ga4_events(28)

        self.assertIsNone(result["key_events"])
        self.assertIn("admin", result["key_event_message"])
        self.assertEqual(result["events"][1]["event"], "generate_lead",
                         "a key-event failure must not blank the event table")

    def test_a_page_nobody_finished_reads_as_a_measured_zero(self) -> None:
        """Scroll is collected site-wide by enhanced measurement, so a page with
        views and no scroll row was genuinely never finished. That is one of the
        few honest zeros on this tab, and it is a zero precisely because the
        event is known to be collected."""
        summary_names = [name for _, name in readers.GA4_SUMMARY_METRICS]
        events = {"rows": [metric_row("120", "80", dimensions=("page_view",))]}
        depth = {"rows": [
            metric_row("40", dimensions=("/blog/emi", "page_view")),
            metric_row("10", dimensions=("/blog/emi", "scroll")),
            metric_row("25", dimensions=("/products", "page_view")),
        ]}

        def respond(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
            names = [metric["name"] for metric in payload.get("metrics", [])]
            if names == summary_names:
                return READY
            if payload.get("dimensions") == [{"name": "pagePath"}, {"name": "eventName"}]:
                return depth
            if payload.get("dimensions"):
                return events
            raise RuntimeError("no key-event metric")

        with mock.patch.object(readers, "_ga4_request", side_effect=respond):
            result = readers.ga4_events(28)

        by_page = {row["page"]: row for row in result["scroll_depth"]}
        self.assertEqual(by_page["/blog/emi"]["reached_end"], 10)
        self.assertEqual(by_page["/blog/emi"]["share"], 25.0)
        self.assertEqual(by_page["/products"]["reached_end"], 0)
        self.assertEqual(by_page["/products"]["share"], 0.0)

    def test_a_scroll_failure_leaves_the_funnel_standing(self) -> None:
        summary_names = [name for _, name in readers.GA4_SUMMARY_METRICS]
        events = {"rows": [metric_row("9", "7", dimensions=("generate_lead",))]}

        def respond(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
            names = [metric["name"] for metric in payload.get("metrics", [])]
            if names == summary_names:
                return READY
            if payload.get("dimensions") == [{"name": "pagePath"}, {"name": "eventName"}]:
                raise TimeoutError("slow")
            if payload.get("dimensions"):
                return events
            raise RuntimeError("no key-event metric")

        with mock.patch.object(readers, "_ga4_request", side_effect=respond):
            result = readers.ga4_events(28)

        self.assertEqual(result["scroll_depth"], [])
        self.assertIn("TimeoutError", result["scroll_message"])
        self.assertTrue(result["instrumented"], "the funnel survives a scroll failure")

    def test_a_property_with_only_page_views_is_not_instrumented(self) -> None:
        only_views = {"rows": [metric_row("120", "80", dimensions=("page_view",))]}
        summary_names = [name for _, name in readers.GA4_SUMMARY_METRICS]

        def respond(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
            names = [metric["name"] for metric in payload.get("metrics", [])]
            return READY if names == summary_names else only_views

        with mock.patch.object(readers, "_ga4_request", side_effect=respond):
            result = readers.ga4_events(28)

        self.assertFalse(result["instrumented"],
                         "enhanced measurement supplies page_view on its own")


class NotConnected(ReaderCase):
    def test_every_new_panel_names_what_is_missing_rather_than_showing_zero(self) -> None:
        with mock.patch.dict(os.environ, {"GA4_PROPERTY_ID": ""}, clear=False):
            for cache in (readers._ga4_cache, readers._ga4_events_cache):
                cache.clear()
            events = readers.ga4_events(28)

        self.assertEqual(events["status"], "not_connected")
        self.assertIn("GA4_PROPERTY_ID", events["required_variables"])
        self.assertEqual(events["funnel"], [])
        self.assertEqual(events["scroll_depth"], [])
        self.assertIsNone(events["key_events"])


if __name__ == "__main__":
    unittest.main()


class ChannelNaming(unittest.TestCase):
    """`classify_source`, including the two channels it used to have no name for."""

    def test_an_email_medium_is_a_channel_and_a_bare_referral_is_another(self) -> None:
        self.assertEqual(readers.classify_source("newsletter-sept", "email"), "Email")
        self.assertEqual(readers.classify_source("some-blog.in", "referral"), "Referral")

    def test_an_email_service_provider_is_named_by_its_source_alone(self) -> None:
        """The link a provider rewrites carries its host and not always a medium."""
        self.assertEqual(readers.classify_source("mailchimp", ""), "Email")

    def test_the_source_beats_the_medium(self) -> None:
        """A LinkedIn newsletter is LinkedIn traffic that happened to arrive by email.

        Filing it under Email would lose the channel that earned the visit, and
        every referral host below would collapse into one undifferentiated row.
        """
        self.assertEqual(readers.classify_source("linkedin.com", "email"), "LinkedIn")
        self.assertEqual(readers.classify_source("lnkd.in", "referral"), "LinkedIn")
        self.assertEqual(readers.classify_source("google", "organic"), "Google")

    def test_an_unmapped_source_is_named_honestly(self) -> None:
        self.assertEqual(readers.classify_source("partner-portal", "cpc"), "Other")


def place_rows(*rows: tuple[tuple[str, ...], tuple[str, ...]]) -> dict[str, Any]:
    return {"rows": [metric_row(*values, dimensions=dimensions) for dimensions, values in rows]}


#: One window of geography, shaped like the property this console reads: India
#: carrying the work, and an unexplained country that engages at almost nothing.
COUNTRY_TOTALS = place_rows(
    (("India",), ("300", "210", "0.31")),
    (("Netherlands",), ("41", "39", "0.049")),
)
PLACE_TREE = place_rows(
    (("India", "Delhi", "New Delhi"), ("180", "70")),
    (("India", "Maharashtra", "Pune"), ("120", "33")),
    (("Netherlands", "(not set)", "(not set)"), ("41", "2")),
)
PREVIOUS_COUNTRIES = place_rows((("India",), ("120",)))
COUNTRY_SOURCES = place_rows(
    (("India", "google", "organic"), ("200", "150", "80", "400")),
    (("India", "lnkd.in", "referral"), ("100", "70", "55", "260")),
    (("Netherlands", "(direct)", ""), ("38", "36", "2", "40")),
    (("Netherlands", "some-host.nl", "referral"), ("3", "3", "0", "3")),
)
COUNTRY_CHANNELS = place_rows(
    (("India", "Organic Search"), ("200", "80")),
    (("India", "Organic Social"), ("100", "55")),
    (("Netherlands", "Direct"), ("38", "2")),
)


def geography_responder(**overrides: Any):
    """Route each outgoing report by the dimensions it asks for.

    An unrecognised request raises rather than returning a plausible payload,
    which is how the live API answers a dimension it does not know: a 400 for the
    whole report. A responder that answered everything would let a typo in a
    dimension name pass every test here and blank the panel in production.
    """
    answers: dict[tuple[str, ...], Any] = {
        (): READY,
        ("country", "region", "city"): PLACE_TREE,
        ("country", "sessionSource", "sessionMedium"): COUNTRY_SOURCES,
        ("country", "sessionDefaultChannelGroup"): COUNTRY_CHANNELS,
    }
    answers.update(overrides.pop("answers", {}))

    def respond(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
        names = tuple(item["name"] for item in payload.get("dimensions", []))
        if names == ("country",):
            # Same dimension, two windows: the previous one asks for sessions
            # alone, because visitors and engagement are only ever read forward.
            return (
                PREVIOUS_COUNTRIES if len(payload["metrics"]) == 1 else COUNTRY_TOTALS
            )
        if names in answers:
            return answers[names]
        raise RuntimeError(f"no report for {names}")

    return respond


class Geography(ReaderCase):
    def test_the_levels_add_up_to_the_country_above_them(self) -> None:
        """The property the tree exists to have.

        Regions and cities come from one report rolled up in Python rather than
        three reports asked separately, precisely so a drill-down cannot disagree
        with the row it opens from.
        """
        with mock.patch.object(readers, "_ga4_request", side_effect=geography_responder()):
            result = readers.ga4_geography(28)

        self.assertEqual(result["status"], "ready")
        for country in result["countries"]:
            self.assertEqual(
                sum(region["sessions"] for region in country["regions"]),
                country["tree_sessions"],
                country["country"],
            )
            for region in country["regions"]:
                self.assertEqual(
                    sum(city["sessions"] for city in region["cities"]),
                    region["sessions"],
                    region["region"],
                )

    def test_an_unresolved_place_keeps_its_row_rather_than_its_name(self) -> None:
        """Dropping `(not set)` from the tree would stop the levels summing.

        A flat list can afford to drop it. A tree cannot: the sessions are real
        and they belong to a country whose total would then exceed its parts.
        """
        with mock.patch.object(readers, "_ga4_request", side_effect=geography_responder()):
            result = readers.ga4_geography(28)

        netherlands = next(row for row in result["countries"] if row["country"] == "Netherlands")
        self.assertEqual([region["region"] for region in netherlands["regions"]], ["Not reported"])
        self.assertEqual(netherlands["regions"][0]["sessions"], 41)

    def test_a_country_names_itself_expected_or_not_and_says_what_it_was(self) -> None:
        with mock.patch.object(readers, "_ga4_request", side_effect=geography_responder()):
            result = readers.ga4_geography(28)

        india = next(row for row in result["countries"] if row["country"] == "India")
        netherlands = next(row for row in result["countries"] if row["country"] == "Netherlands")

        self.assertTrue(india["expected"])
        self.assertEqual(india["previous_sessions"], 120)
        self.assertEqual(india["delta_sessions"], 180)
        self.assertFalse(netherlands["expected"])
        # None, not zero. A country GA4 never reported and one it reported as
        # zero are different answers, and only the second supports "this is new".
        self.assertIsNone(netherlands["previous_sessions"])
        self.assertIsNone(netherlands["delta_sessions"])

    def test_visitors_come_from_the_country_report_and_never_from_the_tree(self) -> None:
        """`activeUsers` is de-duplicated by GA4 and does not add up.

        A visitor who browsed from two cities is one user at country level and
        two if you sum the city rows, so the tree carries sessions only.
        """
        with mock.patch.object(readers, "_ga4_request", side_effect=geography_responder()):
            result = readers.ga4_geography(28)

        india = next(row for row in result["countries"] if row["country"] == "India")
        self.assertEqual(india["active_users"], 210)
        self.assertNotIn("active_users", india["regions"][0])
        self.assertNotIn("active_users", india["regions"][0]["cities"][0])

    def test_the_two_cross_tabs_ask_two_different_questions(self) -> None:
        """One is source-shaped and ours; the other is spend-shaped and GA4's.

        Where they disagree the disagreement is the finding, so the reader must
        actually request `sessionDefaultChannelGroup` rather than deriving a
        channel group from the sources it already has.
        """
        asked: list[tuple[str, ...]] = []

        def capture(credentials: str, property_id: str, payload: dict[str, Any]) -> dict[str, Any]:
            asked.append(tuple(item["name"] for item in payload.get("dimensions", [])))
            return geography_responder()(credentials, property_id, payload)

        with mock.patch.object(readers, "_ga4_request", side_effect=capture):
            result = readers.ga4_geography(28)

        self.assertIn(("country", "sessionDefaultChannelGroup"), asked)
        self.assertIn(("country", "sessionSource", "sessionMedium"), asked)

        netherlands = next(
            row for row in result["country_sources"] if row["country"] == "Netherlands"
        )
        # Folded by the same rule the site-wide channel table uses: a cross-tab
        # whose "Direct" meant something narrower than the row above would be
        # worse than no cross-tab.
        self.assertEqual(
            [(row["source"], row["sessions"]) for row in netherlands["channels"]],
            [("Direct", 38), ("Referral", 3)],
        )
        groups = next(
            row for row in result["country_channels"] if row["country"] == "Netherlands"
        )
        self.assertEqual([row["channel"] for row in groups["channels"]], ["Direct"])

    def test_the_previous_window_is_the_one_immediately_before_this_one(self) -> None:
        windows: list[tuple[str, str]] = []

        def capture(credentials: str, property_id: str, payload: dict[str, Any]) -> dict[str, Any]:
            window = payload["dateRanges"][0]
            windows.append((window["startDate"], window["endDate"]))
            return geography_responder()(credentials, property_id, payload)

        with mock.patch.object(readers, "_ga4_request", side_effect=capture):
            readers.ga4_geography(7)

        import datetime as dt

        end = dt.date.today() - dt.timedelta(days=1)
        start = end - dt.timedelta(days=6)
        previous_end = start - dt.timedelta(days=1)
        previous_start = previous_end - dt.timedelta(days=6)
        self.assertIn((start.isoformat(), end.isoformat()), windows)
        self.assertIn((previous_start.isoformat(), previous_end.isoformat()), windows)

    def test_a_rejected_cross_tab_leaves_the_other_panels_standing(self) -> None:
        """The reason this is its own reader.

        Two of its five reports are cross-tabs at a cardinality GA4 can threshold
        or reject outright, and a rejection there must not take the channel table
        and the device panel down with it.
        """
        geography = geography_responder()

        def respond(credentials: str, property_id: str, payload: dict[str, Any]) -> dict[str, Any]:
            names = tuple(item["name"] for item in payload.get("dimensions", []))
            if names == ("country", "sessionDefaultChannelGroup"):
                raise ValueError("400: dimension not supported")
            try:
                return geography(credentials, property_id, payload)
            except RuntimeError:
                # Whatever the audience reader asks for, answered emptily. This
                # test is about one reader failing, not about the other's rows.
                return {"rows": []}

        with mock.patch.object(readers, "_ga4_request", side_effect=respond):
            result = readers.ga4_geography(28)
            audience = readers.ga4_audience(28)

        self.assertEqual(result["status"], "error")
        self.assertIn("ValueError", result["message"])
        self.assertEqual(result["countries"], [])
        # The reader that did not fail is unaffected, which is the whole point.
        self.assertNotEqual(audience["status"], "error")

    def test_an_unconnected_property_names_what_is_missing_rather_than_erroring(self) -> None:
        with mock.patch.dict(os.environ, {"GA4_PROPERTY_ID": ""}):
            readers._ga4_cache.clear()
            readers._ga4_geography_cache.clear()
            result = readers.ga4_geography(28)

        self.assertEqual(result["status"], "not_connected")
        self.assertIn("GA4_PROPERTY_ID", result["required_variables"])
        self.assertEqual(result["countries"], [])


class AudienceWindows(ReaderCase):
    def test_the_channel_table_carries_the_window_before_it(self) -> None:
        """A share is only a decision once you know which way it moved."""
        current = place_rows(
            (("google", "organic"), ("120", "90", "40", "260")),
            (("lnkd.in", "referral"), ("51", "44", "21", "158")),
        )
        previous = place_rows((("google", "organic"), ("140", "100", "50", "300")))
        seen: list[str] = []

        def respond(_credentials: str, _property: str, payload: dict[str, Any]) -> dict[str, Any]:
            names = tuple(item["name"] for item in payload.get("dimensions", []))
            if not names:
                return READY
            if names == ("sessionSource", "sessionMedium"):
                start = payload["dateRanges"][0]["startDate"]
                seen.append(start)
                return previous if len(seen) > 1 and start < max(seen) else current
            return {"rows": []}

        with mock.patch.object(readers, "_ga4_request", side_effect=respond):
            result = readers.ga4_audience(28)

        self.assertTrue(result["traffic_sources"])
        self.assertTrue(result["previous_traffic_sources"])
        self.assertLess(min(seen), max(seen))

    def test_geography_no_longer_lives_here(self) -> None:
        """One reader owns a subject.

        Countries and cities moved to `ga4_geography`, which needs three levels
        and two windows of its own. Leaving a second copy behind is how a country
        total and the cities inside it come to describe different sessions.
        """
        self.assertNotIn("countries", readers._empty_audience(28, "all", {}))
        self.assertNotIn("cities", readers._empty_audience(28, "all", {}))
