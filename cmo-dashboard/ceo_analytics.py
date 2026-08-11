"""Search Console, shaped for the one screen that reads it.

`analytics_readers` answers "what are the totals"; this module answers the
questions the Analytics tab actually asks: how did each day go, which queries and
pages did the work, and which of them is worth writing about next.

Everything here is derived from rows Search Console returned. Nothing is
estimated, and a figure that has not been measured stays `None` so the page can
say "not yet" instead of drawing a zero.
"""

from __future__ import annotations

import datetime as dt
import os
import threading
import time
from typing import Any, Callable, Iterable, Sequence

CACHE_SECONDS = 600
COLLECTION_START = "2026-08-04"
#: Search Console finalises a day's data roughly two days later.
REPORTING_DELAY_DAYS = 2
DEVICES = ("all", "desktop", "mobile", "tablet")
RANGE_DAYS: dict[str, int | None] = {"7": 7, "28": 28, "90": 90, "all": None}
RANGE_LABELS = {"7": "7 days", "28": "28 days", "90": "90 days", "all": "All", "custom": "Custom"}
ROW_LIMIT = 250

_cache: dict[tuple[Any, ...], tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()


class SearchConsoleUnavailable(RuntimeError):
    """Raised when there is no configured, reachable Search Console to read."""


def _number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _ratio(part: int | float | None, whole: int | float | None) -> float | None:
    if part is None or not whole:
        return None
    return round(part / whole * 100, 2)


def _delta(current: Any, previous: Any) -> int | float | None:
    if current is None or previous is None:
        return None
    value = current - previous
    return round(value, 2) if isinstance(value, float) else value


def normalise_range(key: str, start: str = "", end: str = "", today: dt.date | None = None) -> dict[str, Any]:
    """Resolve a chip selection into a concrete, bounded date window."""
    today = today or dt.date.today()
    latest = today - dt.timedelta(days=REPORTING_DELAY_DAYS)
    collection = dt.date.fromisoformat(COLLECTION_START)
    key = (key or "28").strip().casefold()
    if key == "custom":
        try:
            first = dt.date.fromisoformat(start)
            last = dt.date.fromisoformat(end)
        except ValueError:
            key = "28"
        else:
            if first > last:
                first, last = last, first
            first = max(first, collection)
            last = min(last, latest)
            if first > last:
                first = last
            return {
                "key": "custom",
                "label": f"{first.isoformat()} to {last.isoformat()}",
                "start": first.isoformat(),
                "end": last.isoformat(),
                "days": (last - first).days + 1,
            }
    if key not in RANGE_DAYS:
        key = "28"
    days = RANGE_DAYS[key]
    last = latest
    first = collection if days is None else max(collection, last - dt.timedelta(days=days - 1))
    if first > last:
        first = last
    return {
        "key": key,
        "label": RANGE_LABELS[key],
        "start": first.isoformat(),
        "end": last.isoformat(),
        "days": (last - first).days + 1,
    }


def _previous_window(window: dict[str, Any]) -> dict[str, str] | None:
    """The window immediately before this one, only if collection covers it."""
    first = dt.date.fromisoformat(window["start"])
    collection = dt.date.fromisoformat(COLLECTION_START)
    last = first - dt.timedelta(days=1)
    start = last - dt.timedelta(days=window["days"] - 1)
    if last < collection or start < collection:
        return None
    return {"start": start.isoformat(), "end": last.isoformat()}


def _totals(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    row = rows[0] if rows else {}
    impressions = _number(row.get("impressions"))
    clicks = _number(row.get("clicks"))
    return {
        "impressions": impressions,
        "clicks": clicks,
        "ctr": _ratio(clicks, impressions),
        "position": round(float(row["position"]), 1) if _number(row.get("position")) is not None else None,
    }


def _keyed_rows(rows: Iterable[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        keys = row.get("keys")
        if not isinstance(keys, list) or not keys or not str(keys[0]).strip():
            continue
        impressions = _number(row.get("impressions"))
        clicks = _number(row.get("clicks"))
        position = _number(row.get("position"))
        output.append(
            {
                name: str(keys[0]).strip(),
                "impressions": impressions,
                "clicks": clicks,
                "ctr": _ratio(clicks, impressions),
                "position": round(float(position), 1) if position is not None else None,
            }
        )
    return sorted(output, key=lambda item: (item["impressions"] is None, -(item["impressions"] or 0)))


def _series(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    days = _keyed_rows(rows, "date")
    return sorted(days, key=lambda item: item["date"])


def _subject_from_page(page: str) -> str:
    path = page.split("://", 1)[-1]
    path = path.split("/", 1)[1] if "/" in path else ""
    segment = [part for part in path.split("/") if part]
    if not segment:
        return "the home page"
    return segment[-1].replace("-", " ").replace("_", " ")


def opportunities(
    queries: Sequence[dict[str, Any]],
    pages: Sequence[dict[str, Any]],
    previous_queries: Sequence[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Rows that qualify for "worth writing about next", each with its reason.

    Every rule is a plain statement about measured numbers. A query that meets no
    rule is not listed — the panel would rather be short than speculative.
    """
    prior = {row["query"]: row for row in previous_queries if row.get("query")}
    found: list[dict[str, Any]] = []
    for row in queries:
        subject = row["query"]
        impressions = row["impressions"] or 0
        clicks = row["clicks"] or 0
        position = row["position"]
        reason = ""
        kind = ""
        if impressions >= 20 and clicks == 0:
            kind = "unclicked"
            reason = (
                f"Seen {impressions:g} times in search and clicked none. "
                "Nothing we have answers this question directly."
            )
        elif position is not None and 10 < position <= 25 and impressions >= 10:
            kind = "page_two"
            reason = (
                f"We sit at position {position:g} — page two. "
                "A page written for this question could reach page one."
            )
        elif position is not None and position <= 10 and impressions >= 30 and (row["ctr"] or 0) < 2:
            kind = "weak_title"
            reason = (
                f"We rank at position {position:g} but only {row['ctr'] or 0:g}% of people click. "
                "The page appears, and then it does not look like the answer."
            )
        else:
            earlier = prior.get(subject)
            before = (earlier or {}).get("impressions") or 0
            if impressions >= 15 and before and impressions >= before * 1.5:
                kind = "rising"
                reason = (
                    f"Impressions went from {before:g} to {impressions:g} against the previous window. "
                    "Interest is growing faster than our coverage."
                )
        if kind:
            found.append(
                {
                    "kind": kind,
                    "subject": subject,
                    "source": "query",
                    "reason": reason,
                    "impressions": row["impressions"],
                    "clicks": row["clicks"],
                    "position": position,
                }
            )
    for row in pages:
        impressions = row["impressions"] or 0
        position = row["position"]
        if position is not None and 10 < position <= 25 and impressions >= 25:
            found.append(
                {
                    "kind": "page_two",
                    "subject": _subject_from_page(row["page"]),
                    "source": "page",
                    "reason": (
                        f"This page averages position {position:g} on {impressions:g} impressions. "
                        "A companion piece could pull the whole topic up."
                    ),
                    "impressions": row["impressions"],
                    "clicks": row["clicks"],
                    "position": position,
                }
            )
    order = {"unclicked": 0, "rising": 1, "page_two": 2, "weak_title": 3}
    found.sort(key=lambda item: (order[item["kind"]], -(item["impressions"] or 0)))
    seen: set[str] = set()
    unique = []
    for item in found:
        key = item["subject"].casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _empty(window: dict[str, Any], device: str, status: str, message: str) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "range": window,
        "device": device,
        "collection_start": COLLECTION_START,
        "reporting_delay_days": REPORTING_DELAY_DAYS,
        "required_variables": ["GSC_CREDENTIALS_PATH", "GSC_PROPERTY"],
        "totals": {"impressions": None, "clicks": None, "ctr": None, "position": None, "indexed_pages": None},
        "previous": None,
        "deltas": None,
        "series": [],
        "queries": [],
        "pages": [],
        "opportunities": [],
    }


def _live_client() -> Callable[..., Any]:
    credentials_path = os.getenv("GSC_CREDENTIALS_PATH", "").strip()
    property_name = os.getenv("GSC_PROPERTY", "").strip()
    if not credentials_path or not property_name:
        raise SearchConsoleUnavailable(
            "Search Console is not connected. Set GSC_CREDENTIALS_PATH and GSC_PROPERTY."
        )
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)

    def call(kind: str, **body: Any) -> Any:
        if kind == "sitemaps":
            return service.sitemaps().list(siteUrl=property_name).execute()
        return service.searchanalytics().query(siteUrl=property_name, body=body).execute()

    return call


def _device_filter(device: str) -> list[dict[str, Any]]:
    if device == "all":
        return []
    return [
        {
            "filters": [
                {"dimension": "device", "operator": "equals", "expression": device.upper()}
            ]
        }
    ]


def _indexed_pages(sitemaps: Any) -> int | None:
    total = 0
    seen = False
    for sitemap in (sitemaps or {}).get("sitemap", []) if isinstance(sitemaps, dict) else []:
        for content in sitemap.get("contents", []) or []:
            if content.get("type") == "WEB" and str(content.get("indexed", "")).isdigit():
                total += int(content["indexed"])
                seen = True
    return total if seen else None


def search_console_report(
    range_key: str = "28",
    device: str = "all",
    *,
    start: str = "",
    end: str = "",
    client: Callable[..., Any] | None = None,
    today: dt.date | None = None,
) -> dict[str, Any]:
    """Everything the Analytics tab renders, in one read."""
    if device not in DEVICES:
        device = "all"
    window = normalise_range(range_key, start, end, today)
    if client is None:
        try:
            client = _live_client()
        except SearchConsoleUnavailable as exc:
            return _empty(window, device, "not_connected", str(exc))
        except Exception as exc:  # a provider import or credential failure must not blank the tab
            return _empty(window, device, "error", f"Search Console reader failed: {type(exc).__name__}.")

    filters = _device_filter(device)

    def query(**body: Any) -> list[dict[str, Any]]:
        body.setdefault("startDate", window["start"])
        body.setdefault("endDate", window["end"])
        if filters:
            body["dimensionFilterGroups"] = filters
        result = client("search", **body)
        rows = result.get("rows", []) if isinstance(result, dict) else []
        return [row for row in rows if isinstance(row, dict)]

    try:
        totals_rows = query(rowLimit=1)
        series_rows = query(dimensions=["date"], rowLimit=ROW_LIMIT)
        query_rows = query(dimensions=["query"], rowLimit=ROW_LIMIT)
        page_rows = query(dimensions=["page"], rowLimit=ROW_LIMIT)
        indexed = _indexed_pages(client("sitemaps"))
        earlier = _previous_window(window)
        previous_totals = None
        previous_queries: list[dict[str, Any]] = []
        if earlier:
            previous_totals = _totals(query(rowLimit=1, **earlier))
            previous_queries = _keyed_rows(query(dimensions=["query"], rowLimit=ROW_LIMIT, **earlier), "query")
    except Exception as exc:  # never blank the console because a provider hiccuped
        return _empty(window, device, "error", f"Search Console read failed: {type(exc).__name__}.")

    totals = {**_totals(totals_rows), "indexed_pages": indexed}
    queries = _keyed_rows(query_rows, "query")
    pages = _keyed_rows(page_rows, "page")
    deltas = None
    if previous_totals is not None:
        deltas = {name: _delta(totals.get(name), previous_totals.get(name)) for name in previous_totals}
    measured = any(value is not None for value in totals.values())
    return {
        "status": "ready" if measured else "collecting",
        "message": ""
        if measured
        else f"Search Console is connected but has returned nothing since {COLLECTION_START}.",
        "range": window,
        "device": device,
        "collection_start": COLLECTION_START,
        "reporting_delay_days": REPORTING_DELAY_DAYS,
        "required_variables": ["GSC_CREDENTIALS_PATH", "GSC_PROPERTY"],
        "totals": totals,
        "previous": previous_totals,
        "deltas": deltas,
        "series": _series(series_rows),
        "queries": queries,
        "pages": pages,
        "opportunities": opportunities(queries, pages, previous_queries),
    }


def cached_report(range_key: str = "28", device: str = "all", *, start: str = "", end: str = "") -> dict[str, Any]:
    key = (range_key, device, start, end)
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if cached and cached[0] > now:
            return cached[1]
    report = search_console_report(range_key, device, start=start, end=end)
    with _cache_lock:
        _cache[key] = (now + CACHE_SECONDS, report)
    return report
