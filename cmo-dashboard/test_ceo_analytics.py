"""The Analytics tab's reader — ranges, series, tables and the opportunity rules.

The rules in `opportunities` are the only place in this console that turns numbers
into a recommendation, so each one is pinned to the numbers that trigger it. A
query that meets no rule must not appear: an empty panel is the honest answer.
"""

from __future__ import annotations

import datetime as dt
import unittest

import ceo_analytics as analytics

TODAY = dt.date(2026, 9, 15)


def rows(*items: dict) -> dict:
    return {"rows": list(items)}


def row(key: str, *, clicks: int = 0, impressions: int = 0, position: float = 0.0) -> dict:
    return {"keys": [key], "clicks": clicks, "impressions": impressions, "position": position}


class RangeChips(unittest.TestCase):
    def test_a_window_ends_at_the_last_finalised_day(self) -> None:
        window = analytics.normalise_range("28", today=TODAY)

        self.assertEqual(window["end"], "2026-09-13")
        self.assertEqual(window["start"], "2026-08-17")
        self.assertEqual(window["days"], 28)

    def test_all_starts_at_the_collection_date_and_never_before(self) -> None:
        window = analytics.normalise_range("all", today=TODAY)

        self.assertEqual(window["start"], analytics.COLLECTION_START)
        self.assertEqual(window["label"], "All")

    def test_a_short_history_clamps_the_ninety_day_window(self) -> None:
        window = analytics.normalise_range("90", today=dt.date(2026, 8, 11))

        self.assertEqual(window["start"], analytics.COLLECTION_START)
        self.assertEqual(window["days"], 6)

    def test_a_custom_range_is_clamped_to_measurable_days(self) -> None:
        window = analytics.normalise_range("custom", "2020-01-01", "2030-01-01", today=TODAY)

        self.assertEqual(window["start"], analytics.COLLECTION_START)
        self.assertEqual(window["end"], "2026-09-13")

    def test_a_reversed_custom_range_is_put_back_in_order(self) -> None:
        window = analytics.normalise_range("custom", "2026-09-01", "2026-08-20", today=TODAY)

        self.assertEqual((window["start"], window["end"]), ("2026-08-20", "2026-09-01"))

    def test_an_unparsable_range_falls_back_to_twenty_eight_days(self) -> None:
        for key in ("", "banana", "custom"):
            self.assertEqual(analytics.normalise_range(key, today=TODAY)["key"], "28")

    def test_a_previous_window_is_offered_only_when_collection_covers_it(self) -> None:
        recent = analytics.normalise_range("7", today=dt.date(2026, 8, 11))
        settled = analytics.normalise_range("7", today=TODAY)

        self.assertIsNone(analytics._previous_window(recent))
        self.assertEqual(analytics._previous_window(settled)["end"], "2026-09-06")


class OpportunityRules(unittest.TestCase):
    def qualify(self, queries, pages=(), previous=()):
        return analytics.opportunities(
            analytics._keyed_rows([row(**item) for item in queries], "query"),
            analytics._keyed_rows([row(**item) for item in pages], "page"),
            analytics._keyed_rows([row(**item) for item in previous], "query"),
        )

    def test_impressions_with_no_clicks_qualify(self) -> None:
        found = self.qualify([{"key": "battery price delhi", "impressions": 140, "clicks": 0, "position": 18.4}])

        self.assertEqual(found[0]["kind"], "unclicked")
        self.assertIn("clicked none", found[0]["reason"])
        self.assertEqual(found[0]["subject"], "battery price delhi")

    def test_a_page_two_position_qualifies(self) -> None:
        found = self.qualify([{"key": "battery replacement", "impressions": 40, "clicks": 3, "position": 14.2}])

        self.assertEqual(found[0]["kind"], "page_two")
        self.assertIn("page two", found[0]["reason"])

    def test_ranking_well_while_losing_the_click_qualifies(self) -> None:
        found = self.qualify([{"key": "itarang emi", "impressions": 400, "clicks": 3, "position": 4.0}])

        self.assertEqual(found[0]["kind"], "weak_title")
        self.assertIn("does not look like the answer", found[0]["reason"])

    def test_growth_against_the_previous_window_qualifies(self) -> None:
        found = self.qualify(
            [{"key": "e rickshaw finance", "impressions": 60, "clicks": 9, "position": 5.0}],
            previous=[{"key": "e rickshaw finance", "impressions": 20, "clicks": 3, "position": 6.0}],
        )

        self.assertEqual(found[0]["kind"], "rising")
        self.assertIn("20 to 60", found[0]["reason"])

    def test_a_query_that_is_simply_working_does_not_qualify(self) -> None:
        found = self.qualify([{"key": "itarang", "impressions": 400, "clicks": 260, "position": 1.1}])

        self.assertEqual(found, [])

    def test_thin_data_does_not_qualify(self) -> None:
        found = self.qualify([{"key": "rare query", "impressions": 4, "clicks": 0, "position": 22.0}])

        self.assertEqual(found, [])

    def test_a_page_on_page_two_qualifies_and_names_a_readable_subject(self) -> None:
        found = self.qualify([], pages=[
            {"key": "https://itarang.com/blog/battery-replacement-cost", "impressions": 90, "clicks": 2, "position": 14.0}
        ])

        self.assertEqual(found[0]["subject"], "battery replacement cost")
        self.assertEqual(found[0]["source"], "page")

    def test_the_same_subject_is_listed_once(self) -> None:
        found = self.qualify(
            [{"key": "battery cost", "impressions": 140, "clicks": 0, "position": 18.0}],
            pages=[{"key": "https://itarang.com/battery-cost", "impressions": 90, "clicks": 1, "position": 14.0}],
        )

        self.assertEqual(len(found), 1)

    def test_unclicked_queries_are_ranked_above_page_two_ones(self) -> None:
        found = self.qualify([
            {"key": "second page", "impressions": 200, "clicks": 5, "position": 13.0},
            {"key": "never clicked", "impressions": 30, "clicks": 0, "position": 20.0},
        ])

        self.assertEqual([item["kind"] for item in found], ["unclicked", "page_two"])


class ReportShape(unittest.TestCase):
    def client(self, **overrides):
        def call(kind, **body):
            if kind == "sitemaps":
                return {"sitemap": [{"contents": [{"type": "WEB", "indexed": "12", "submitted": "20"}]}]}
            dimensions = body.get("dimensions") or []
            if not dimensions:
                return rows({"clicks": 42, "impressions": 5400, "position": 14.23})
            if dimensions == ["date"]:
                return rows(*[row(f"2026-09-0{day}", clicks=day, impressions=day * 30, position=13.0) for day in range(1, 6)])
            if dimensions == ["query"]:
                return rows(
                    row("battery price delhi", clicks=0, impressions=140, position=18.4),
                    row("itarang", clicks=90, impressions=120, position=1.1),
                )
            return rows(row("https://itarang.com/emi", clicks=4, impressions=90, position=15.5))

        return overrides.get("call", call)

    def report(self, **kwargs):
        return analytics.search_console_report(client=self.client(), today=TODAY, **kwargs)

    def test_a_ready_report_carries_every_section_the_tab_renders(self) -> None:
        report = self.report()

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["totals"]["impressions"], 5400)
        self.assertEqual(report["totals"]["ctr"], 0.78)
        self.assertEqual(report["totals"]["position"], 14.2)
        self.assertEqual(report["totals"]["indexed_pages"], 12)
        self.assertEqual(len(report["series"]), 5)
        self.assertEqual(report["series"][0]["date"], "2026-09-01")
        self.assertEqual(len(report["queries"]), 2)
        self.assertEqual(len(report["pages"]), 1)
        self.assertTrue(report["opportunities"])

    def test_ctr_is_derived_from_clicks_and_impressions_not_reported_blind(self) -> None:
        report = self.report()

        self.assertEqual(report["queries"][0]["ctr"], 0.0)
        self.assertEqual(report["queries"][1]["ctr"], 75.0)

    def test_deltas_appear_only_when_a_previous_window_was_measured(self) -> None:
        settled = self.report(range_key="7")
        self.assertIsNotNone(settled["deltas"])
        self.assertEqual(settled["deltas"]["impressions"], 0)

        early = analytics.search_console_report(
            "90", client=self.client(), today=dt.date(2026, 8, 11)
        )
        self.assertIsNone(early["deltas"])
        self.assertIsNone(early["previous"])

    def test_a_device_selection_reaches_the_query_as_a_filter(self) -> None:
        seen = []

        def call(kind, **body):
            seen.append(body)
            return {"sitemap": []} if kind == "sitemaps" else rows()

        analytics.search_console_report("28", "mobile", client=call, today=TODAY)

        self.assertTrue(seen)
        self.assertEqual(
            seen[0]["dimensionFilterGroups"][0]["filters"][0],
            {"dimension": "device", "operator": "equals", "expression": "MOBILE"},
        )

    def test_an_unknown_device_falls_back_to_all_rather_than_filtering_blind(self) -> None:
        report = self.report(device="watch")

        self.assertEqual(report["device"], "all")

    def test_missing_credentials_produce_a_not_connected_report_not_zeroes(self) -> None:
        report = analytics.search_console_report("28", "all", today=TODAY)

        self.assertEqual(report["status"], "not_connected")
        self.assertIsNone(report["totals"]["impressions"])
        self.assertEqual(report["series"], [])
        self.assertEqual(report["opportunities"], [])
        self.assertIn("GSC_CREDENTIALS_PATH", report["required_variables"])

    def test_a_provider_failure_reports_itself_without_blanking_the_shape(self) -> None:
        def explode(kind, **body):
            raise TimeoutError("upstream")

        report = analytics.search_console_report("28", "all", client=explode, today=TODAY)

        self.assertEqual(report["status"], "error")
        self.assertIn("TimeoutError", report["message"])
        self.assertIsNone(report["totals"]["clicks"])
        self.assertEqual(report["queries"], [])

    def test_a_connected_but_silent_property_says_collecting_rather_than_zero(self) -> None:
        def quiet(kind, **body):
            return {"sitemap": []} if kind == "sitemaps" else rows()

        report = analytics.search_console_report("28", "all", client=quiet, today=TODAY)

        self.assertEqual(report["status"], "collecting")
        self.assertIsNone(report["totals"]["impressions"])
        self.assertIn("returned nothing since", report["message"])


if __name__ == "__main__":
    unittest.main()


class BlogSlugJoin(unittest.TestCase):
    """The slug is the join key, and it has to survive both sides' URL shapes.

    Search Console reports an absolute URL, Google Analytics reports a path, and
    a shared link comes back with UTM parameters attached. All three are the same
    article and must fold onto one row.
    """

    def test_both_shapes_of_the_same_article_yield_the_same_slug(self):
        self.assertEqual(
            analytics.blog_slug("https://www.itarang.com/blog/battery-passport"),
            analytics.blog_slug("/blog/battery-passport"),
        )

    def test_a_utm_tagged_share_is_the_same_article(self):
        """Our own ShareBar stamps these, so failing here would split every shared post."""
        self.assertEqual(
            analytics.blog_slug("/blog/battery-passport?utm_source=whatsapp&utm_medium=social"),
            "battery-passport",
        )

    def test_a_category_archive_is_not_an_article(self):
        """Folding it in would credit every post's impressions to a listing page."""
        self.assertEqual(analytics.blog_slug("/blog/category/safety"), "")

    def test_the_blog_index_and_other_pages_are_not_articles(self):
        for page in ("/blog", "/blog/", "/products", "https://www.itarang.com/"):
            self.assertEqual(analytics.blog_slug(page), "", page)


class BlogPerformance(unittest.TestCase):
    """One row per article, from two systems that each know half of it."""

    def report(self):
        return {
            "pages": [
                {
                    "page": "https://www.itarang.com/blog/battery-passport",
                    "impressions": 540,
                    "clicks": 18,
                    "ctr": 3.33,
                    "position": 8.4,
                },
                {
                    "page": "https://www.itarang.com/blog/informal-financing",
                    "impressions": 120,
                    "clicks": 0,
                    "ctr": 0.0,
                    "position": 22.1,
                },
                {"page": "https://www.itarang.com/products", "impressions": 900, "clicks": 40},
            ]
        }

    def ga4(self):
        return [
            {"page": "/blog/battery-passport", "screen_page_views": 230, "sessions": 180},
            {"page": "/blog/only-shared", "screen_page_views": 95, "sessions": 80},
            {"page": "/products", "screen_page_views": 400, "sessions": 300},
        ]

    def test_only_blog_pages_reach_the_table(self):
        result = analytics.blog_performance(self.report(), self.ga4())
        self.assertEqual(
            sorted(row["slug"] for row in result["posts"]),
            ["battery-passport", "informal-financing", "only-shared"],
        )

    def test_the_two_halves_join_onto_one_row(self):
        row = next(
            item
            for item in analytics.blog_performance(self.report(), self.ga4())["posts"]
            if item["slug"] == "battery-passport"
        )
        self.assertEqual(row["impressions"], 540)
        self.assertEqual(row["views"], 230)
        self.assertEqual(sorted(row["sources"]), ["ga4", "search_console"])

    def test_an_article_seen_by_only_one_system_is_a_row_that_says_so(self):
        """Views with no impressions is a post that was shared, not found. Both are real."""
        posts = {
            item["slug"]: item
            for item in analytics.blog_performance(self.report(), self.ga4())["posts"]
        }
        self.assertEqual(posts["only-shared"]["sources"], ["ga4"])
        self.assertIsNone(posts["only-shared"]["impressions"])
        self.assertEqual(posts["informal-financing"]["sources"], ["search_console"])
        self.assertIsNone(posts["informal-financing"]["views"])

    def test_an_unmeasured_column_stays_none_and_never_becomes_zero(self):
        """`0 impressions` is a measurement. `no impressions recorded` is not."""
        result = analytics.blog_performance({"pages": []}, [])
        self.assertEqual(result["posts"], [])
        self.assertIsNone(result["totals"]["impressions"])
        self.assertIsNone(result["totals"]["views"])

    def test_a_real_zero_survives_as_a_zero(self):
        row = next(
            item
            for item in analytics.blog_performance(self.report(), self.ga4())["posts"]
            if item["slug"] == "informal-financing"
        )
        self.assertEqual(row["clicks"], 0)

    def test_totals_add_only_what_was_measured(self):
        totals = analytics.blog_performance(self.report(), self.ga4())["totals"]
        self.assertEqual(totals["impressions"], 660)
        self.assertEqual(totals["views"], 325)

    def test_the_board_title_is_used_when_there_is_one(self):
        posts = {
            item["slug"]: item
            for item in analytics.blog_performance(
                self.report(), self.ga4(), titles={"battery-passport": "The real title"}
            )["posts"]
        }
        self.assertEqual(posts["battery-passport"]["title"], "The real title")
        self.assertEqual(
            posts["informal-financing"]["title"],
            "Informal Financing",
            "an article the board does not name still needs something readable",
        )
