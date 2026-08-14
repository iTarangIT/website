"""Competitor analysis from what we already have.

Apoorv's question is "who else is in energy distribution, how do their sites rank, and
what must I improve". Three of those four parts are answerable today:

* their page inventory — their sitemap.xml, a plain HTTP GET, costs nothing;
* what they are targeting — their titles, meta descriptions and headings, read by
  scraping a bounded number of their pages directly at one credit each;
* our side — Search Console, free and authoritative for our own property;
* the gap between the two.

What is *not* answerable is what they actually rank for and how much traffic it pulls.
Search Console reports our property only, and no amount of page reading substitutes for
a rank index. Those figures render as unavailable and name what would supply them —
they are never estimated, and never shown as zero.

Search volume slots in behind `VolumeProvider` when the Google Ads Keyword Planner
token arrives; until then `NotConnectedVolumes` reports the gap honestly.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, Sequence
from urllib.parse import urlparse

from cmo_runtime.console_db import ConsoleDB, ConsoleDBError, norm_key
from cmo_runtime.topic_proposals import (
    FirecrawlProposalResearcher,
    GoogleSearchConsoleReader,
    ProposalRefused,
    SearchConsoleReader,
)

# Their sitemap is free; their pages are not. Ten pages is enough to read a small
# competitor's targeting and keeps one analysis at roughly ten credits.
COMPETITOR_PAGE_CAP = 10
SITEMAP_TIMEOUT_SECONDS = 30
MAX_SITEMAP_BYTES = 5_000_000
# Below this average position we are contesting the term but losing it.
WEAK_POSITION = 10.0

STOP_PATH_PARTS = frozenset({"privacy", "terms", "cookie", "legal", "sitemap", "contact"})


class CompetitorRefused(RuntimeError):
    """A fail-closed outcome that is safe to show to an operator."""


def normalise_domain(value: str) -> str:
    """Accept anything a human would paste and return a bare hostname."""
    text = re.sub(r"\s+", "", str(value)).strip().casefold()
    if not text:
        raise CompetitorRefused("enter a competitor website")
    if "://" not in text:
        text = "https://" + text
    parsed = urlparse(text)
    host = (parsed.hostname or "").strip(".")
    if not host or "." not in host or len(host) > 253:
        raise CompetitorRefused(f"that does not look like a website: {value!r}")
    if not re.fullmatch(r"[a-z0-9.-]+", host):
        raise CompetitorRefused(f"that does not look like a website: {value!r}")
    return host[4:] if host.startswith("www.") else host


@dataclass(frozen=True)
class CompetitorPage:
    url: str
    title: str
    meta_description: str
    headings: tuple[str, ...]
    word_count: int


@dataclass(frozen=True)
class GapFinding:
    """One topic they cover, scored against what Search Console says about us."""

    kind: str  # uncontested | weak_position | covered
    topic: str
    keywords: tuple[str, ...]
    their_url: str
    our_query: str
    our_position: float | None
    our_impressions: int | None
    recommendation: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "topic": self.topic,
            "keywords": list(self.keywords),
            "their_url": self.their_url,
            "our_query": self.our_query,
            "our_position": self.our_position,
            "our_impressions": self.our_impressions,
            "recommendation": self.recommendation,
        }


class VolumeProvider(Protocol):
    def volumes(self, keywords: Sequence[str]) -> tuple[dict[str, int], str]: ...


class NotConnectedVolumes:
    """The default. Says what is missing and what would supply it.

    Replaced by `GoogleAdsKeywordPlanner` once the developer token exists; the rest of
    the module is written against this interface so nothing else changes when it does.
    """

    message = (
        "Search volume is unavailable: Google Ads Keyword Planner is not connected. "
        "Set GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CUSTOMER_ID and "
        "GOOGLE_ADS_CREDENTIALS_PATH to enable it."
    )

    def volumes(self, keywords: Sequence[str]) -> tuple[dict[str, int], str]:
        del keywords
        return {}, self.message


def fetch_sitemap_urls(domain: str, *, opener=None) -> tuple[list[str], str]:
    """Read a competitor's page inventory for free.

    Follows one level of sitemap index. Returns (urls, message); an unreadable sitemap
    is reported, never guessed at from a crawl.
    """
    opener = opener or urllib.request.urlopen
    seen: list[str] = []
    message = ""
    for candidate in (f"https://{domain}/sitemap.xml", f"https://{domain}/sitemap_index.xml"):
        try:
            request = urllib.request.Request(
                candidate,
                headers={"User-Agent": "iTarang-CMO/1.0 (+https://itarang.com)"},
                method="GET",
            )
            with opener(request, timeout=SITEMAP_TIMEOUT_SECONDS) as response:
                body = response.read(MAX_SITEMAP_BYTES)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
            continue
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            continue
        tag = root.tag.rsplit("}", 1)[-1]
        locations = [
            (element.text or "").strip()
            for element in root.iter()
            if element.tag.rsplit("}", 1)[-1] == "loc" and (element.text or "").strip()
        ]
        if tag == "sitemapindex":
            for child in locations[:5]:
                try:
                    request = urllib.request.Request(
                        child,
                        headers={"User-Agent": "iTarang-CMO/1.0 (+https://itarang.com)"},
                        method="GET",
                    )
                    with opener(request, timeout=SITEMAP_TIMEOUT_SECONDS) as response:
                        nested = ET.fromstring(response.read(MAX_SITEMAP_BYTES))
                except Exception:
                    continue
                locations.extend(
                    (element.text or "").strip()
                    for element in nested.iter()
                    if element.tag.rsplit("}", 1)[-1] == "loc" and (element.text or "").strip()
                )
        for url in locations:
            if re.match(r"^https?://", url, re.I) and url not in seen:
                seen.append(url)
        if seen:
            return seen, ""
    if not seen:
        message = f"No readable sitemap was found at {domain}; their page inventory is unavailable."
    return seen, message


def interesting_pages(urls: Sequence[str], limit: int) -> list[str]:
    """Prefer content pages over boilerplate; the credits are finite."""
    scored: list[tuple[int, str]] = []
    for url in urls:
        path = urlparse(url).path.strip("/")
        parts = [part for part in path.split("/") if part]
        # The homepage and boilerplate carry no topic worth a credit.
        if not parts or any(part.casefold() in STOP_PATH_PARTS for part in parts):
            continue
        score = 0
        if any(part.casefold() in {"blog", "guide", "guides", "resources", "learn"} for part in parts):
            score += 2
        if len(parts) >= 2:
            score += 1
        scored.append((score, url))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [url for _score, url in scored[:limit]]


def _page_from_scrape(url: str, data: dict[str, Any]) -> CompetitorPage:
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    markdown = str(data.get("markdown") or "")
    headings = tuple(
        re.sub(r"\s+", " ", match.group(1)).strip()
        for match in re.finditer(r"(?m)^#{1,3}\s+(.+?)\s*$", markdown)
    )[:25]
    return CompetitorPage(
        url=url,
        title=re.sub(r"\s+", " ", str(metadata.get("title") or "")).strip()[:300],
        meta_description=re.sub(r"\s+", " ", str(metadata.get("description") or "")).strip()[:400],
        headings=headings,
        word_count=len(re.findall(r"\b[\w'-]+\b", markdown)),
    )


def build_gap(
    pages: Sequence[CompetitorPage],
    gsc_rows: Sequence[dict[str, Any]],
) -> list[GapFinding]:
    """Their topics, scored against our own Search Console position for each."""
    by_key: dict[str, dict[str, Any]] = {}
    for row in gsc_rows:
        key = norm_key(str(row.get("query", "")))
        if key and key not in by_key:
            by_key[key] = row

    findings: list[GapFinding] = []
    seen: set[str] = set()
    for page in pages:
        for topic in [page.title, *page.headings]:
            topic = topic.strip()
            key = norm_key(topic)
            if not topic or not key or key in seen or len(key.split()) < 2:
                continue
            seen.add(key)
            tokens = set(key.split())
            best_row: dict[str, Any] | None = None
            best_overlap = 0
            for candidate_key, row in by_key.items():
                overlap = len(tokens.intersection(candidate_key.split()))
                if overlap > best_overlap:
                    best_overlap, best_row = overlap, row
            if best_row is None or best_overlap < 2:
                findings.append(
                    GapFinding(
                        kind="uncontested",
                        topic=topic,
                        keywords=tuple(sorted(tokens))[:8],
                        their_url=page.url,
                        our_query="",
                        our_position=None,
                        our_impressions=None,
                        recommendation=(
                            "They cover this and Search Console shows no matching query for "
                            "itarang.com. Writing it is a first entry, not a contest."
                        ),
                    )
                )
                continue
            position = best_row.get("position")
            position = float(position) if isinstance(position, (int, float)) else None
            impressions = best_row.get("impressions")
            impressions = int(impressions) if isinstance(impressions, (int, float)) else None
            if position is not None and position > WEAK_POSITION:
                findings.append(
                    GapFinding(
                        kind="weak_position",
                        topic=topic,
                        keywords=tuple(sorted(tokens))[:8],
                        their_url=page.url,
                        our_query=str(best_row.get("query", "")),
                        our_position=position,
                        our_impressions=impressions,
                        recommendation=(
                            f"We already appear for this at average position {position:.1f}. "
                            "Improving the existing page is likely cheaper than a new one."
                        ),
                    )
                )
            else:
                findings.append(
                    GapFinding(
                        kind="covered",
                        topic=topic,
                        keywords=tuple(sorted(tokens))[:8],
                        their_url=page.url,
                        our_query=str(best_row.get("query", "")),
                        our_position=position,
                        our_impressions=impressions,
                        recommendation="We already hold a strong position here. No action.",
                    )
                )
    order = {"uncontested": 0, "weak_position": 1, "covered": 2}
    findings.sort(key=lambda item: (order[item.kind], -(item.our_impressions or 0)))
    return findings


COMPETITOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS competitors (
    id          INTEGER PRIMARY KEY,
    domain      TEXT NOT NULL UNIQUE,
    added_by    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS competitor_runs (
    id                INTEGER PRIMARY KEY,
    competitor_id     INTEGER NOT NULL REFERENCES competitors(id),
    status            TEXT NOT NULL,
    message           TEXT NOT NULL DEFAULT '',
    sitemap_url_count INTEGER NOT NULL DEFAULT 0,
    pages_requested   INTEGER NOT NULL DEFAULT 0,
    pages_fetched     INTEGER NOT NULL DEFAULT 0,
    credits_used      INTEGER NOT NULL DEFAULT 0,
    credits_remaining INTEGER,
    gsc_rows_used     INTEGER NOT NULL DEFAULT 0,
    volume_message    TEXT NOT NULL DEFAULT '',
    created_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS competitor_pages (
    id               INTEGER PRIMARY KEY,
    run_id           INTEGER NOT NULL REFERENCES competitor_runs(id),
    url              TEXT NOT NULL,
    title            TEXT NOT NULL DEFAULT '',
    meta_description TEXT NOT NULL DEFAULT '',
    headings_json    TEXT NOT NULL DEFAULT '[]',
    word_count       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS gap_findings (
    id              INTEGER PRIMARY KEY,
    run_id          INTEGER NOT NULL REFERENCES competitor_runs(id),
    kind            TEXT NOT NULL,
    topic           TEXT NOT NULL,
    keywords_json   TEXT NOT NULL DEFAULT '[]',
    their_url       TEXT NOT NULL DEFAULT '',
    our_query       TEXT NOT NULL DEFAULT '',
    our_position    REAL,
    our_impressions INTEGER,
    recommendation  TEXT NOT NULL DEFAULT ''
);
"""


class CompetitorService:
    def __init__(
        self,
        profile_dir: str | Path,
        *,
        database: ConsoleDB | None = None,
        researcher: FirecrawlProposalResearcher | None = None,
        search_console: SearchConsoleReader | None = None,
        volumes: VolumeProvider | None = None,
        sitemap_opener=None,
    ) -> None:
        self.profile_dir = Path(profile_dir)
        self.database = database or ConsoleDB(self.profile_dir)
        self.database._connection.executescript(COMPETITOR_SCHEMA)
        self.researcher = researcher or FirecrawlProposalResearcher(self.profile_dir)
        self.search_console = search_console or GoogleSearchConsoleReader()
        self.volumes = volumes or NotConnectedVolumes()
        self.sitemap_opener = sitemap_opener

    def analyse(self, target: str, actor: str) -> dict[str, Any]:
        """One bounded pass over a competitor. Runs only on an explicit action."""
        domain = normalise_domain(target)
        competitor_id = self._competitor(domain, actor)

        urls, sitemap_message = fetch_sitemap_urls(domain, opener=self.sitemap_opener)
        wanted = interesting_pages(urls, COMPETITOR_PAGE_CAP)

        pages: list[CompetitorPage] = []
        credits_used = 0
        credits_remaining: int | None = None
        message = sitemap_message
        if wanted:
            if not self.researcher.connected:
                message = (message + " Firecrawl is not connected, so their pages were not read.").strip()
            else:
                try:
                    before, _remaining = self.researcher.credit_state()
                    for url in wanted:
                        try:
                            response = self.researcher._request_json(
                                "POST",
                                "/v2/scrape",
                                {"url": url, "formats": ["markdown"], "onlyMainContent": True},
                            )
                        except ProposalRefused:
                            continue
                        data = response.get("data")
                        if isinstance(data, dict):
                            pages.append(_page_from_scrape(url, data))
                    after, credits_remaining = self.researcher.credit_state()
                    credits_used = max(0, after - before)
                except ProposalRefused as error:
                    message = (message + " " + str(error)).strip()

        gsc_rows, gsc_message = self.search_console.demand("")
        if gsc_message:
            message = (message + " " + gsc_message).strip()
        findings = build_gap(pages, gsc_rows)
        _volumes, volume_message = self.volumes.volumes(
            [finding.topic for finding in findings[:50]]
        )

        run_id = self._record(
            competitor_id=competitor_id,
            status="completed" if pages or gsc_rows else "no_data",
            message=message,
            sitemap_url_count=len(urls),
            pages_requested=len(wanted),
            pages=pages,
            credits_used=credits_used,
            credits_remaining=credits_remaining,
            gsc_rows_used=len(gsc_rows),
            volume_message=volume_message,
            findings=findings,
        )
        return self.latest(domain) | {"run_id": run_id}

    def _competitor(self, domain: str, actor: str) -> int:
        with self.database.write() as connection:
            row = connection.execute(
                "SELECT id FROM competitors WHERE domain = ?", (domain,)
            ).fetchone()
            if row is not None:
                return int(row["id"])
            cursor = connection.execute(
                "INSERT INTO competitors (domain, added_by, created_at) VALUES (?,?,?)",
                (domain, str(actor)[:180], datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")),
            )
            return int(cursor.lastrowid or 0)

    def _record(self, **fields: Any) -> int:
        pages: Sequence[CompetitorPage] = fields.pop("pages")
        findings: Sequence[GapFinding] = fields.pop("findings")
        with self.database.write() as connection:
            cursor = connection.execute(
                "INSERT INTO competitor_runs (competitor_id, status, message, sitemap_url_count,"
                " pages_requested, pages_fetched, credits_used, credits_remaining, gsc_rows_used,"
                " volume_message, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    fields["competitor_id"],
                    fields["status"],
                    fields["message"][:600],
                    fields["sitemap_url_count"],
                    fields["pages_requested"],
                    len(pages),
                    fields["credits_used"],
                    fields["credits_remaining"],
                    fields["gsc_rows_used"],
                    fields["volume_message"][:600],
                    datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                ),
            )
            run_id = int(cursor.lastrowid or 0)
            for page in pages:
                connection.execute(
                    "INSERT INTO competitor_pages (run_id, url, title, meta_description,"
                    " headings_json, word_count) VALUES (?,?,?,?,?,?)",
                    (
                        run_id,
                        page.url,
                        page.title,
                        page.meta_description,
                        json.dumps(list(page.headings), ensure_ascii=False),
                        page.word_count,
                    ),
                )
            for finding in findings[:200]:
                connection.execute(
                    "INSERT INTO gap_findings (run_id, kind, topic, keywords_json, their_url,"
                    " our_query, our_position, our_impressions, recommendation)"
                    " VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        run_id,
                        finding.kind,
                        finding.topic,
                        json.dumps(list(finding.keywords), ensure_ascii=False),
                        finding.their_url,
                        finding.our_query,
                        finding.our_position,
                        finding.our_impressions,
                        finding.recommendation,
                    ),
                )
            return run_id

    def latest(self, domain: str | None = None) -> dict[str, Any]:
        """The stored analysis. This is what the page reads — never a live crawl."""
        if domain:
            run = self.database._one(
                "SELECT r.*, c.domain FROM competitor_runs r JOIN competitors c"
                " ON c.id = r.competitor_id WHERE c.domain = ? ORDER BY r.id DESC LIMIT 1",
                (normalise_domain(domain),),
            )
        else:
            run = self.database._one(
                "SELECT r.*, c.domain FROM competitor_runs r JOIN competitors c"
                " ON c.id = r.competitor_id ORDER BY r.id DESC LIMIT 1"
            )
        if run is None:
            return {
                "status": "none",
                "domain": "",
                "message": "No competitor has been analysed yet.",
                "findings": [],
                "pages": [],
                "volume_message": NotConnectedVolumes.message,
            }
        run_id = int(run["id"])
        return {
            "status": run["status"],
            "domain": run["domain"],
            "message": run["message"],
            "measured_at": run["created_at"],
            "sitemap_url_count": run["sitemap_url_count"],
            "pages_fetched": run["pages_fetched"],
            "credits_used": run["credits_used"],
            "credits_remaining": run["credits_remaining"],
            "gsc_rows_used": run["gsc_rows_used"],
            "volume_message": run["volume_message"] or NotConnectedVolumes.message,
            "pages": [
                {
                    "url": row["url"],
                    "title": row["title"],
                    "meta_description": row["meta_description"],
                    "word_count": row["word_count"],
                }
                for row in self.database._query(
                    "SELECT * FROM competitor_pages WHERE run_id = ? ORDER BY id", (run_id,)
                )
            ],
            "findings": [
                {
                    "kind": row["kind"],
                    "topic": row["topic"],
                    "keywords": json.loads(row["keywords_json"]),
                    "their_url": row["their_url"],
                    "our_query": row["our_query"],
                    "our_position": row["our_position"],
                    "our_impressions": row["our_impressions"],
                    "recommendation": row["recommendation"],
                }
                for row in self.database._query(
                    "SELECT * FROM gap_findings WHERE run_id = ? ORDER BY id", (run_id,)
                )
            ],
            "competitors": [
                dict(row)
                for row in self.database._query("SELECT * FROM competitors ORDER BY domain")
            ],
        }
