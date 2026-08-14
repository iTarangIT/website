"""Invariant 5 and the gap view: never zero where the answer is unavailable."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cmo_runtime.competitors import (  # noqa: E402
    COMPETITOR_PAGE_CAP,
    CompetitorPage,
    CompetitorRefused,
    CompetitorService,
    NotConnectedVolumes,
    build_gap,
    fetch_sitemap_urls,
    interesting_pages,
    normalise_domain,
)

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://rival.test/</loc></url>
  <url><loc>https://rival.test/privacy</loc></url>
  <url><loc>https://rival.test/blog/e-rickshaw-battery-cost</loc></url>
  <url><loc>https://rival.test/blog/lithium-battery-warranty</loc></url>
</urlset>
"""


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_exception):
        return False


def sitemap_opener(body: bytes | None):
    def opener(request, timeout=None):
        del timeout
        if body is None or "sitemap_index" in request.full_url:
            raise OSError("no sitemap")
        return FakeResponse(body)

    return opener


class FakeSearchConsole:
    def __init__(self, rows=None, message="") -> None:
        self.rows = rows or []
        self.message = message

    def demand(self, subject: str):
        return list(self.rows), self.message


class FakeResearcher:
    def __init__(self, *, connected=True, bodies=None) -> None:
        self.connected = connected
        self.bodies = bodies or {}
        self.used = 100
        self.remaining = 900
        self.scraped: list[str] = []

    def credit_state(self):
        return self.used, self.remaining

    def _request_json(self, method, path, payload):
        url = payload["url"]
        self.scraped.append(url)
        self.used += 1
        self.remaining -= 1
        markdown = self.bodies.get(url, "# Heading about battery cost\n\nbody text here")
        return {"data": {"markdown": markdown, "metadata": {"title": f"Title for {url}"}}}


class DomainNormalisation(unittest.TestCase):
    def test_common_paste_shapes_all_normalise(self) -> None:
        for value in (
            "rival.test",
            "www.rival.test",
            "https://rival.test/",
            "https://www.rival.test/blog?x=1",
            "  RIVAL.TEST  ",
        ):
            self.assertEqual(normalise_domain(value), "rival.test", value)

    def test_nonsense_is_refused_rather_than_analysed(self) -> None:
        for value in ("", "   ", "not a domain", "javascript:alert(1)"):
            with self.subTest(value=value), self.assertRaises(CompetitorRefused):
                normalise_domain(value)


class SitemapReading(unittest.TestCase):
    def test_a_sitemap_is_read_without_spending_a_credit(self) -> None:
        urls, message = fetch_sitemap_urls("rival.test", opener=sitemap_opener(SITEMAP.encode()))
        self.assertEqual(message, "")
        self.assertIn("https://rival.test/blog/e-rickshaw-battery-cost", urls)
        self.assertEqual(len(urls), 4)

    def test_a_missing_sitemap_says_so_rather_than_returning_nothing_silently(self) -> None:
        urls, message = fetch_sitemap_urls("rival.test", opener=sitemap_opener(None))
        self.assertEqual(urls, [])
        self.assertIn("No readable sitemap", message)

    def test_boilerplate_paths_are_not_worth_a_credit(self) -> None:
        urls, _ = fetch_sitemap_urls("rival.test", opener=sitemap_opener(SITEMAP.encode()))
        chosen = interesting_pages(urls, COMPETITOR_PAGE_CAP)
        self.assertNotIn("https://rival.test/privacy", chosen)
        self.assertNotIn("https://rival.test/", chosen)
        self.assertEqual(len(chosen), 2)

    def test_the_page_cap_is_honoured(self) -> None:
        many = [f"https://rival.test/blog/post-{index}" for index in range(50)]
        self.assertEqual(len(interesting_pages(many, COMPETITOR_PAGE_CAP)), COMPETITOR_PAGE_CAP)


class GapScoring(unittest.TestCase):
    def page(self, headings) -> CompetitorPage:
        return CompetitorPage(
            url="https://rival.test/blog/x",
            title="",
            meta_description="",
            headings=tuple(headings),
            word_count=900,
        )

    def test_a_topic_we_have_no_query_for_is_uncontested(self) -> None:
        findings = build_gap([self.page(["Battery swapping station economics"])], [])
        self.assertEqual(findings[0].kind, "uncontested")
        self.assertIsNone(findings[0].our_position)
        self.assertIn("no matching query", findings[0].recommendation)

    def test_a_topic_we_rank_badly_for_is_a_weak_position_not_a_new_page(self) -> None:
        rows = [{"query": "e rickshaw battery cost", "impressions": 120, "position": 24.0}]
        findings = build_gap([self.page(["E rickshaw battery cost in 2026"])], rows)
        self.assertEqual(findings[0].kind, "weak_position")
        self.assertEqual(findings[0].our_position, 24.0)
        self.assertIn("Improving the existing page", findings[0].recommendation)

    def test_a_topic_we_already_win_is_marked_no_action(self) -> None:
        rows = [{"query": "e rickshaw battery cost", "impressions": 500, "position": 3.0}]
        findings = build_gap([self.page(["E rickshaw battery cost in 2026"])], rows)
        self.assertEqual(findings[0].kind, "covered")
        self.assertIn("No action", findings[0].recommendation)

    def test_uncontested_topics_are_ranked_first(self) -> None:
        rows = [{"query": "e rickshaw battery cost", "impressions": 500, "position": 3.0}]
        findings = build_gap(
            [self.page(["E rickshaw battery cost in 2026", "Battery swapping station economics"])],
            rows,
        )
        self.assertEqual(findings[0].kind, "uncontested")

    def test_a_position_is_never_invented_when_search_console_is_silent(self) -> None:
        findings = build_gap([self.page(["Battery swapping station economics"])], [])
        for finding in findings:
            self.assertIsNone(finding.our_position)
            self.assertIsNone(finding.our_impressions)


class NotConnectedRendersAsNotConnected(unittest.TestCase):
    """Invariant 5."""

    def make(self, **kwargs):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()
        service = CompetitorService(
            root,
            researcher=kwargs.get("researcher", FakeResearcher()),
            search_console=kwargs.get("search_console", FakeSearchConsole()),
            sitemap_opener=kwargs.get("sitemap_opener", sitemap_opener(SITEMAP.encode())),
        )
        self.addCleanup(service.database.close)
        return service

    def test_with_no_analysis_the_panel_says_none_not_zero(self) -> None:
        service = self.make()
        latest = service.latest()
        self.assertEqual(latest["status"], "none")
        self.assertEqual(latest["findings"], [])
        self.assertIn("No competitor has been analysed yet", latest["message"])

    def test_search_volume_is_reported_as_unavailable_not_as_zero(self) -> None:
        service = self.make()
        result = service.analyse("rival.test", "sanchit@example.test")
        self.assertIn("Keyword Planner is not connected", result["volume_message"])
        self.assertIn("GOOGLE_ADS_DEVELOPER_TOKEN", result["volume_message"])

    def test_firecrawl_disconnected_still_delivers_the_free_half(self) -> None:
        service = self.make(researcher=FakeResearcher(connected=False))
        result = service.analyse("rival.test", "sanchit@example.test")
        self.assertEqual(result["sitemap_url_count"], 4, "the sitemap is free and still read")
        self.assertEqual(result["pages_fetched"], 0)
        self.assertIn("Firecrawl is not connected", result["message"])
        self.assertEqual(result["credits_used"], 0)

    def test_search_console_disconnected_is_named_not_silently_empty(self) -> None:
        service = self.make(
            search_console=FakeSearchConsole(message="Search Console is not connected.")
        )
        result = service.analyse("rival.test", "sanchit@example.test")
        self.assertIn("Search Console is not connected", result["message"])

    def test_an_unreadable_sitemap_is_reported(self) -> None:
        service = self.make(sitemap_opener=sitemap_opener(None))
        result = service.analyse("rival.test", "sanchit@example.test")
        self.assertIn("No readable sitemap", result["message"])
        self.assertEqual(result["pages_fetched"], 0)


class AnalysisIsStoredAndReadBack(unittest.TestCase):
    """Invariant 6 — the page reads the stored analysis, never a live crawl."""

    def make(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        (root / "state").mkdir()
        self.researcher = FakeResearcher()
        service = CompetitorService(
            root,
            researcher=self.researcher,
            search_console=FakeSearchConsole(
                rows=[{"query": "e rickshaw battery cost", "impressions": 120, "position": 24.0}]
            ),
            sitemap_opener=sitemap_opener(SITEMAP.encode()),
        )
        self.addCleanup(service.database.close)
        return service

    def test_an_analysis_survives_into_the_read_model(self) -> None:
        service = self.make()
        service.analyse("https://www.rival.test/", "sanchit@example.test")

        latest = service.latest()

        self.assertEqual(latest["domain"], "rival.test")
        self.assertEqual(latest["pages_fetched"], 2)
        self.assertEqual(latest["credits_used"], 2, "one credit per page, measured")
        self.assertTrue(latest["findings"])
        self.assertTrue(all(finding["their_url"] for finding in latest["findings"]))

    def test_reading_the_panel_scrapes_nothing(self) -> None:
        service = self.make()
        service.analyse("rival.test", "sanchit@example.test")
        scraped = list(self.researcher.scraped)

        service.latest()
        service.latest("rival.test")

        self.assertEqual(self.researcher.scraped, scraped, "a read must not spend credits")

    def test_the_page_budget_is_capped(self) -> None:
        service = self.make()
        service.analyse("rival.test", "sanchit@example.test")
        self.assertLessEqual(len(self.researcher.scraped), COMPETITOR_PAGE_CAP)


if __name__ == "__main__":
    unittest.main()
