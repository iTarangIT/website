from __future__ import annotations

import datetime as dt
import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib import error, request

PROFILE_DIR = Path(os.getenv("CMO_DASHBOARD_PROFILE_DIR", Path(__file__).resolve().parent.parent)).resolve()
X_TRENDS_FILE = PROFILE_DIR / "state" / "x-trending.json"
FACEBOOK_TRENDS_FILE = PROFILE_DIR / "state" / "facebook-trending.json"
GA4_REQUIRED_VARIABLES = (
    "GA4_PROPERTY_ID",
    "GA4_CREDENTIALS_PATH",
    "GA4_MEASUREMENT_ID",
    "GA4_TAG_INSTALLED",
)
# The summary tiles, as (payload key, GA4 metric name) pairs.
#
# One table rather than two parallel sequences: `_ga4_values` reads metric values
# back positionally, so a metric list and a name tuple that drift by one index
# make every tile show its neighbour's number -- silently, and plausibly. Pairing
# them here makes that particular mistake unrepresentable.
#
# The GA4 Data API caps a single runReport at 10 metrics, and this is exactly 10.
# An eleventh needs a second request, not a longer tuple.
GA4_SUMMARY_METRICS: tuple[tuple[str, str], ...] = (
    ("active_users", "activeUsers"),
    ("sessions", "sessions"),
    ("screen_page_views", "screenPageViews"),
    ("engagement_rate", "engagementRate"),
    ("new_users", "newUsers"),
    ("engaged_sessions", "engagedSessions"),
    ("average_session_duration", "averageSessionDuration"),
    ("screen_page_views_per_session", "screenPageViewsPerSession"),
    ("bounce_rate", "bounceRate"),
    ("sessions_per_user", "sessionsPerUser"),
)
# Computed from the pairs above rather than measured, so it costs no metric slot.
GA4_DERIVED_KEYS: tuple[str, ...] = ("returning_users",)
GA4_METRIC_KEYS: tuple[str, ...] = tuple(
    key for key, _ in GA4_SUMMARY_METRICS
) + GA4_DERIVED_KEYS

CACHE_SECONDS = 300
_ga4_cache: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}
_ga4_events_cache: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}
_ga4_detail_cache: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}
_gsc_trend_cache: dict[tuple[str, ...], tuple[float, tuple[list[dict[str, Any]], str]]] = {}
_ga4_audience_cache: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}
_ga4_geography_cache: dict[tuple[str, ...], tuple[float, dict[str, Any]]] = {}
_cache_lock = threading.Lock()


def _truthy(value: str) -> bool:
    return value.strip().casefold() in {"1", "true", "yes", "installed"}


def _number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _delta(current: int | float | None, previous: int | float | None) -> int | float | None:
    if current is None or previous is None:
        return None
    return current - previous


def _empty_ga4(message: str, *, status: str = "not_connected") -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "required_variables": list(GA4_REQUIRED_VARIABLES),
        "range_days": None,
        "device": "all",
        "metrics": {key: None for key in GA4_METRIC_KEYS},
        "previous": {key: None for key in GA4_METRIC_KEYS},
        "deltas": {key: None for key in GA4_METRIC_KEYS},
        "pages": [],
        "collection_start": None,
    }


def _ga4_request(
    credentials_path: str,
    property_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import service_account

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/analytics.readonly"],
    )
    credentials.refresh(GoogleRequest())
    property_name = property_id if property_id.startswith("properties/") else f"properties/{property_id}"
    endpoint = f"https://analyticsdata.googleapis.com/v1beta/{property_name}:runReport"
    call = request.Request(
        endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(call, timeout=15) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise ValueError("GA4 returned a non-object response")
    return value


def _ga4_derived(values: dict[str, int | float | None]) -> dict[str, int | float | None]:
    """Add the figures we work out rather than ask for.

    Returning users is `activeUsers - newUsers` from the same window and the same
    response, so the subtraction is between two numbers GA4 measured together. If
    either half is missing the answer is missing too -- a returning-user count of
    zero and an unmeasured one are opposite facts, and this file never conflates
    them.
    """
    active = values.get("active_users")
    new = values.get("new_users")
    returning: int | float | None = None
    if active is not None and new is not None:
        returning = max(active - new, 0)
    return {**values, "returning_users": returning}


def _ga4_values(report: dict[str, Any]) -> dict[str, int | float | None]:
    rows = report.get("rows")
    if not isinstance(rows, list) or not rows:
        return {key: None for key in GA4_METRIC_KEYS}
    values = rows[0].get("metricValues", []) if isinstance(rows[0], dict) else []
    return _ga4_derived(
        {
            key: _number(values[index].get("value"))
            if index < len(values) and isinstance(values[index], dict)
            else None
            for index, (key, _) in enumerate(GA4_SUMMARY_METRICS)
        }
    )


def _fetch_ga4(days: int, device: str) -> dict[str, Any]:
    credentials_path = os.getenv("GA4_CREDENTIALS_PATH", "").strip()
    property_id = os.getenv("GA4_PROPERTY_ID", "").strip()
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    previous_end = start - dt.timedelta(days=1)
    previous_start = previous_end - dt.timedelta(days=days - 1)
    metrics = [{"name": name} for _, name in GA4_SUMMARY_METRICS]

    def payload(date_start: dt.date, date_end: dt.date) -> dict[str, Any]:
        value: dict[str, Any] = {
            "dateRanges": [{"startDate": date_start.isoformat(), "endDate": date_end.isoformat()}],
            "metrics": metrics,
            "limit": "1",
        }
        if device != "all":
            value["dimensionFilter"] = {
                "filter": {
                    "fieldName": "deviceCategory",
                    "stringFilter": {"matchType": "EXACT", "value": device},
                }
            }
        return value

    current = _ga4_values(_ga4_request(credentials_path, property_id, payload(start, end)))
    previous = _ga4_values(
        _ga4_request(credentials_path, property_id, payload(previous_start, previous_end))
    )
    has_current = any(value is not None for value in current.values())
    return {
        "status": "ready" if has_current else "collecting",
        "message": "" if has_current else "No Google Analytics data is available for this range yet.",
        "required_variables": list(GA4_REQUIRED_VARIABLES),
        "range_days": days,
        "device": device,
        "metrics": current,
        "previous": previous,
        "deltas": {name: _delta(current[name], previous[name]) for name in current},
    }


def ga4_summary(days: int = 28, device: str = "all") -> dict[str, Any]:
    if days not in {7, 28, 90}:
        days = 28
    if device not in {"all", "desktop", "mobile", "tablet"}:
        device = "all"
    config = {name: os.getenv(name, "").strip() for name in GA4_REQUIRED_VARIABLES}
    missing = [name for name, value in config.items() if not value]
    if missing or not _truthy(config.get("GA4_TAG_INSTALLED", "")):
        result = _empty_ga4("Google Analytics is not connected yet")
        result["range_days"] = days
        result["device"] = device
        result["missing_variables"] = missing or ["GA4_TAG_INSTALLED"]
        return result
    key = tuple(config[name] for name in GA4_REQUIRED_VARIABLES) + (str(days), device)
    now = time.monotonic()
    with _cache_lock:
        cached = _ga4_cache.get(key)
        if cached and cached[0] > now:
            return dict(cached[1])
    try:
        result = _fetch_ga4(days, device)
    except (ImportError, OSError) as exc:
        result = _empty_ga4(
            f"Google Analytics reader is unavailable: {type(exc).__name__}.",
            status="unavailable",
        )
        result["range_days"] = days
        result["device"] = device
    except (error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        result = _empty_ga4(
            f"Google Analytics read failed: {type(exc).__name__}.",
            status="error",
        )
        result["range_days"] = days
        result["device"] = device
    except Exception as exc:  # provider failures must not blank the console
        result = _empty_ga4(
            f"Google Analytics read failed: {type(exc).__name__}.",
            status="error",
        )
        result["range_days"] = days
        result["device"] = device
    with _cache_lock:
        _ga4_cache[key] = (now + CACHE_SECONDS, dict(result))
    return result


def _ga4_detail_payloads(days: int, device: str) -> tuple[dict[str, Any], dict[str, Any]]:
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    pages: dict[str, Any] = {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": "pagePath"}],
        # activeUsers is appended rather than inserted: `_ga4_page_rows` reads
        # values back by position, so a new metric in the middle would shift every
        # column after it onto its neighbour's number.
        "metrics": [
            {"name": "screenPageViews"},
            {"name": "sessions"},
            {"name": "engagementRate"},
            {"name": "activeUsers"},
        ],
        "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
        "limit": "25",
    }
    collection_start: dict[str, Any] = {
        "dateRanges": [{"startDate": "2005-01-01", "endDate": end.isoformat()}],
        "dimensions": [{"name": "date"}],
        "metrics": [{"name": "sessions"}],
        "orderBys": [{"dimension": {"dimensionName": "date"}, "desc": False}],
        "limit": "1",
    }
    if device != "all":
        device_filter = {
            "filter": {
                "fieldName": "deviceCategory",
                "stringFilter": {"matchType": "EXACT", "value": device},
            }
        }
        pages["dimensionFilter"] = device_filter
        collection_start["dimensionFilter"] = device_filter
    return pages, collection_start


def _ga4_page_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    rows = report.get("rows") if isinstance(report, dict) else None
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        dimensions = row.get("dimensionValues")
        metrics = row.get("metricValues")
        if not isinstance(dimensions, list) or not dimensions or not isinstance(dimensions[0], dict):
            continue
        page = str(dimensions[0].get("value") or "").strip()
        if not page:
            continue
        metric_values = metrics if isinstance(metrics, list) else []
        output.append({
            "page": page,
            "screen_page_views": _number(metric_values[0].get("value"))
            if len(metric_values) > 0 and isinstance(metric_values[0], dict) else None,
            "sessions": _number(metric_values[1].get("value"))
            if len(metric_values) > 1 and isinstance(metric_values[1], dict) else None,
            "engagement_rate": _number(metric_values[2].get("value"))
            if len(metric_values) > 2 and isinstance(metric_values[2], dict) else None,
            "active_users": _number(metric_values[3].get("value"))
            if len(metric_values) > 3 and isinstance(metric_values[3], dict) else None,
        })
    return output


def _ga4_collection_start(report: dict[str, Any]) -> str | None:
    rows = report.get("rows") if isinstance(report, dict) else None
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return None
    dimensions = rows[0].get("dimensionValues")
    if not isinstance(dimensions, list) or not dimensions or not isinstance(dimensions[0], dict):
        return None
    value = str(dimensions[0].get("value") or "")
    try:
        return dt.datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def ga4_technical_summary(days: int = 28, device: str = "all") -> dict[str, Any]:
    base = ga4_summary(days, device)
    result = {**base, "pages": [], "collection_start": None}
    if base.get("status") not in {"ready", "collecting"}:
        return result
    config = {name: os.getenv(name, "").strip() for name in GA4_REQUIRED_VARIABLES}
    key = tuple(config[name] for name in GA4_REQUIRED_VARIABLES) + (str(days), device, "technical")
    now = time.monotonic()
    with _cache_lock:
        cached = _ga4_detail_cache.get(key)
        if cached and cached[0] > now:
            return {**result, **cached[1]}
    credentials_path = config["GA4_CREDENTIALS_PATH"]
    property_id = config["GA4_PROPERTY_ID"]
    page_payload, start_payload = _ga4_detail_payloads(days, device)
    try:
        detail = {
            "pages": _ga4_page_rows(
                _ga4_request(credentials_path, property_id, page_payload)
            ),
            "collection_start": _ga4_collection_start(
                _ga4_request(credentials_path, property_id, start_payload)
            ),
        }
    except Exception as exc:  # detail failure must not blank summary metrics
        detail = {
            "pages": [],
            "collection_start": None,
            "detail_message": f"Google Analytics detail read failed: {type(exc).__name__}.",
        }
    with _cache_lock:
        _ga4_detail_cache[key] = (now + CACHE_SECONDS, dict(detail))
    return {**result, **detail}


def _fetch_google_search_trends(days: int) -> tuple[list[dict[str, Any]], str]:
    credentials_path = os.getenv("GSC_CREDENTIALS_PATH", "").strip()
    property_name = os.getenv("GSC_PROPERTY", "").strip()
    if not credentials_path or not property_name:
        return [], "Google Search is not connected."
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
    )
    service = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    previous_end = start - dt.timedelta(days=1)
    previous_start = previous_end - dt.timedelta(days=days - 1)

    def query(date_start: dt.date, date_end: dt.date) -> list[dict[str, Any]]:
        result = service.searchanalytics().query(
            siteUrl=property_name,
            body={
                "startDate": date_start.isoformat(),
                "endDate": date_end.isoformat(),
                "dimensions": ["query"],
                "rowLimit": 20,
            },
        ).execute()
        rows = result.get("rows", []) if isinstance(result, dict) else []
        return [row for row in rows if isinstance(row, dict)]

    current_rows = query(start, end)
    previous_rows = query(previous_start, previous_end)
    previous = {
        row.get("keys", [""])[0]: row
        for row in previous_rows
        if isinstance(row.get("keys"), list) and row.get("keys")
    }
    rows: list[dict[str, Any]] = []
    for row in current_rows:
        keys = row.get("keys")
        if not isinstance(keys, list) or not keys or not isinstance(keys[0], str):
            continue
        title = keys[0].strip()
        if not title:
            continue
        current_value = _number(row.get("impressions"))
        prior = previous.get(title)
        previous_value = _number(prior.get("impressions")) if prior else None
        rows.append(
            {
                "title": title,
                "source": "Google Search",
                "metric": "impressions",
                "current": current_value,
                "previous": previous_value,
                "delta": _delta(current_value, previous_value),
                "summary": f"{current_value:g} impressions" if current_value is not None else "",
            }
        )
    return rows, "" if rows else "Google Search is connected but returned no query trends."


def google_search_trends(days: int = 7) -> tuple[list[dict[str, Any]], str]:
    if days not in {7, 28, 90}:
        days = 7
    config = (
        os.getenv("GSC_CREDENTIALS_PATH", "").strip(),
        os.getenv("GSC_PROPERTY", "").strip(),
        str(days),
    )
    if not config[0] or not config[1]:
        return [], "Google Search is not connected."
    now = time.monotonic()
    with _cache_lock:
        cached = _gsc_trend_cache.get(config)
        if cached and cached[0] > now:
            rows, message = cached[1]
            return list(rows), message
    try:
        result = _fetch_google_search_trends(days)
    except (ImportError, OSError) as exc:
        result = ([], f"Google Search trends are unavailable: {type(exc).__name__}.")
    except Exception as exc:  # provider failures must not blank other sections
        result = ([], f"Google Search trends read failed: {type(exc).__name__}.")
    with _cache_lock:
        _gsc_trend_cache[config] = (now + CACHE_SECONDS, result)
    rows, message = result
    return list(rows), message


def _collector_rows(
    path: Path,
    source: str,
    connected: bool,
) -> list[dict[str, Any]]:
    if not connected:
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []
    source_rows = value if isinstance(value, list) else value.get("items", []) if isinstance(value, dict) else []
    rows: list[dict[str, Any]] = []
    for row in source_rows:
        if not isinstance(row, dict) or not isinstance(row.get("title"), str):
            continue
        rows.append({**row, "source": source})
    return rows


def trending_rows(days: int = 7) -> tuple[list[dict[str, Any]], list[str]]:
    google_rows, google_message = google_search_trends(days)
    x_rows = _collector_rows(
        X_TRENDS_FILE,
        "X",
        bool(os.getenv("X_BEARER_TOKEN", "").strip()),
    )
    facebook_rows = _collector_rows(
        FACEBOOK_TRENDS_FILE,
        "Facebook",
        bool(os.getenv("FACEBOOK_ACCESS_TOKEN", "").strip())
        and bool(os.getenv("FACEBOOK_PAGE_ID", "").strip()),
    )
    messages = [google_message] if google_message else []
    if not os.getenv("X_BEARER_TOKEN", "").strip():
        messages.append("X is not connected.")
    if not (
        os.getenv("FACEBOOK_ACCESS_TOKEN", "").strip()
        and os.getenv("FACEBOOK_PAGE_ID", "").strip()
    ):
        messages.append("Facebook is not connected.")
    return google_rows + x_rows + facebook_rows, messages


# --------------------------------------------------------------- traffic sources

#: How a raw GA4 `sessionSource` becomes a channel a human recognises.
#:
#: Two kinds of value arrive here and both matter. A referral carries the host
#: that sent it (`lnkd.in`, `t.co`, `l.instagram.com`), and a share from our own
#: ShareBar carries the `utm_source` we stamped on it (`linkedin`, `x`,
#: `whatsapp`). Matching is on substring so both land in the same bucket, which
#: is the whole point: "LinkedIn sent 40 sessions" is the answer, not "lnkd.in
#: sent 22 and linkedin.com sent 18".
TRAFFIC_SOURCES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Google", ("google", "googlesyndication", "googleads")),
    ("LinkedIn", ("linkedin", "lnkd.in")),
    ("X", ("twitter", "t.co", "x.com", "utm_source=x")),
    ("Facebook", ("facebook", "fb.com", "fb.me", "m.facebook")),
    ("Instagram", ("instagram", "ig.me")),
    ("WhatsApp", ("whatsapp", "wa.me", "chat.whatsapp")),
    # One row rather than five: at this volume "Bing 3, DuckDuckGo 2, Ecosia 1"
    # is noise, and the decision it informs is the same for all of them.
    ("Other search", ("bing", "msn", "duckduckgo", "yahoo", "ecosia", "brave")),
    # An email service provider stamps its own name on the link it rewrites, so
    # the source alone identifies the channel before any medium is consulted.
    ("Email", ("mailchimp", "sendgrid", "mailerlite", "campaign-archive")),
)

#: Mediums that name a channel the source cannot. Consulted only after the
#: substring table above, because the source is the more specific answer: a
#: LinkedIn newsletter is LinkedIn traffic that happened to arrive by email, and
#: filing it under Email would lose the channel that actually earned the visit.
#:
#: `Referral` is last on purpose. Every mapped host above also arrives with
#: medium `referral`, so a referral rule consulted any earlier would swallow
#: LinkedIn, Facebook and the rest into one undifferentiated row.
MEDIUM_CHANNELS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Organic search", ("organic",)),
    ("Email", ("email", "e-mail", "newsletter")),
    ("Referral", ("referral",)),
)

#: GA4 reports an unattributed session as `(direct)`. It is a real answer, not a
#: gap, and gets its own row rather than being folded into Other.
DIRECT_SOURCES = frozenset({"(direct)", "(none)", "direct", ""})


def classify_source(source: str, medium: str = "") -> str:
    """Bucket one GA4 session source into a channel name.

    `Direct` is checked first because `(direct)` would otherwise never match a
    substring rule. The source is then tried against `TRAFFIC_SOURCES` and only
    afterwards the medium against `MEDIUM_CHANNELS`, because the source is the
    more specific of the two answers. `Other` is returned rather than guessed at
    — an unmapped referrer named honestly is more useful than one filed under
    the wrong logo.
    """
    value = (source or "").strip().casefold()
    if value in DIRECT_SOURCES:
        return "Direct"
    for label, needles in TRAFFIC_SOURCES:
        if any(needle in value for needle in needles):
            return label
    channel = (medium or "").strip().casefold()
    for label, needles in MEDIUM_CHANNELS:
        if channel in needles:
            return label
    return "Other"


def _ga4_rows(
    report: dict[str, Any], dimensions: Sequence[str], metrics: Sequence[str]
) -> list[dict[str, Any]]:
    """Read a GA4 report into plain dicts, skipping anything malformed.

    Unmeasured stays None rather than becoming 0, the same rule the rest of this
    module follows: a metric GA4 did not return and a metric that is genuinely
    zero are different answers and the console renders them differently.
    """
    output: list[dict[str, Any]] = []
    rows = report.get("rows") if isinstance(report, dict) else None
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        dimension_values = row.get("dimensionValues")
        metric_values = row.get("metricValues")
        if not isinstance(dimension_values, list) or len(dimension_values) < len(dimensions):
            continue
        item: dict[str, Any] = {}
        for index, name in enumerate(dimensions):
            cell = dimension_values[index]
            item[name] = str(cell.get("value") or "").strip() if isinstance(cell, dict) else ""
        values = metric_values if isinstance(metric_values, list) else []
        for index, name in enumerate(metrics):
            cell = values[index] if index < len(values) else None
            item[name] = _number(cell.get("value")) if isinstance(cell, dict) else None
        output.append(item)
    return output


def _audience_payload(
    days: int,
    device: str,
    dimensions: Sequence[str],
    metrics: Sequence[str],
    *,
    limit: int = 25,
    order_by: str = "sessions",
    previous: bool = False,
) -> dict[str, Any]:
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    if previous:
        # The window immediately before this one, same length. `ga4_summary`
        # builds its comparison the same way; two different definitions of
        # "previous" would let a tile and a table disagree about the same move.
        end = start - dt.timedelta(days=1)
        start = end - dt.timedelta(days=days - 1)
    payload: dict[str, Any] = {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "dimensions": [{"name": name} for name in dimensions],
        "metrics": [{"name": name} for name in metrics],
        "orderBys": [{"metric": {"metricName": order_by}, "desc": True}],
        "limit": str(limit),
    }
    if device != "all":
        payload["dimensionFilter"] = {
            "filter": {
                "fieldName": "deviceCategory",
                "stringFilter": {"matchType": "EXACT", "value": device},
            }
        }
    return payload


def _ga4_read(
    credentials_path: str,
    property_id: str,
    days: int,
    device: str,
    dimensions: Sequence[str],
    metrics: Sequence[str],
    *,
    limit: int = 25,
    order_by: str = "sessions",
    previous: bool = False,
) -> list[dict[str, Any]]:
    """One GA4 report, read into plain dicts keyed by their GA4 names.

    This was a closure inside `ga4_audience` for as long as that was the only
    reader asking for dimensioned rows. It is module level now because
    `ga4_geography` asks the same question of different dimensions, and two
    copies of the request/parse pair would be two places for the window, the
    device filter or the ordering to drift apart.
    """
    report = _ga4_request(
        credentials_path,
        property_id,
        _audience_payload(
            days,
            device,
            dimensions,
            metrics,
            limit=limit,
            order_by=order_by,
            previous=previous,
        ),
    )
    return _ga4_rows(report, dimensions, metrics)


def _empty_audience(days: int, device: str, base: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": base.get("status", "not_connected"),
        "message": base.get("message", ""),
        "required_variables": list(GA4_REQUIRED_VARIABLES),
        "missing_variables": base.get("missing_variables", []),
        "range_days": days,
        "device": device,
        "traffic_sources": [],
        "previous_traffic_sources": [],
        "first_user_sources": [],
        "devices": [],
        "browsers": [],
        "landing_pages": [],
        "search_terms": [],
    }


def _fold_sources(
    rows: Sequence[dict[str, Any]],
    *,
    source_key: str = "sessionSource",
    medium_key: str = "sessionMedium",
) -> list[dict[str, Any]]:
    """Collapse raw sources into channels, keeping the referrers behind each one.

    `examples` is not decoration. When a channel looks wrong the first question
    is always "what actually matched", and the answer has to be on the row rather
    than in someone's re-run of the query.

    Only additive metrics are summed. Engagement rate and views-per-session are
    ratios, and averaging a ratio across rows weights a 3-session referrer the
    same as a 300-session one; both are rebuilt here from the counts that GA4
    measured (`engagedSessions`, `screenPageViews`) over the sessions in the
    folded bucket. This is the same reasoning `ceo_analytics._totals` applies to
    Search Console CTR.

    The dimension keys are parameters because first-touch attribution asks the
    identical question of `firstUserSource`/`firstUserMedium`, and one folding
    rule for both is what keeps the two tables comparable.
    """
    folded: dict[str, dict[str, Any]] = {}
    for row in rows:
        label = classify_source(str(row.get(source_key, "")), str(row.get(medium_key, "")))
        bucket = folded.setdefault(
            label,
            {
                "source": label,
                "sessions": 0,
                "active_users": 0,
                "engaged_sessions": 0,
                "screen_page_views": 0,
                "examples": [],
            },
        )
        bucket["sessions"] += int(row.get("sessions") or 0)
        bucket["active_users"] += int(row.get("activeUsers") or 0)
        bucket["engaged_sessions"] += int(row.get("engagedSessions") or 0)
        bucket["screen_page_views"] += int(row.get("screenPageViews") or 0)
        raw = str(row.get(source_key, "")).strip()
        if raw and raw not in bucket["examples"] and len(bucket["examples"]) < 4:
            bucket["examples"].append(raw)
    total = sum(bucket["sessions"] for bucket in folded.values())
    ordered = sorted(folded.values(), key=lambda bucket: -bucket["sessions"])
    for bucket in ordered:
        sessions = bucket["sessions"]
        bucket["share"] = round(sessions * 100 / total, 1) if total else None
        bucket["engagement_rate"] = (
            bucket["engaged_sessions"] / sessions if sessions else None
        )
        bucket["views_per_session"] = (
            round(bucket["screen_page_views"] / sessions, 2) if sessions else None
        )
    return ordered


def ga4_audience(days: int = 28, device: str = "all") -> dict[str, Any]:
    """Which channel, on what device, onto which page — what the tiles cannot say.

    Six reports in one call, cached together for `CACHE_SECONDS`, because they
    are always read together and six independent caches would let the panels
    disagree about which window they are describing.

    Geography used to live here and now lives in `ga4_geography`, which needs
    three levels and two windows of its own. One reader owning a subject is what
    keeps a country total and the cities inside it describing the same sessions.

    `search_terms` is deliberately not GA4's `searchTerm`, which reports on-site
    search this website does not have. The search terms a marketer means are the
    Google queries that produced impressions, and those come from Search Console
    — `ceo_analytics` already has them and the console renders them there.
    """
    if days not in {7, 28, 90}:
        days = 28
    if device not in {"all", "desktop", "mobile", "tablet"}:
        device = "all"
    base = ga4_summary(days, device)
    if base.get("status") not in {"ready", "collecting"}:
        return _empty_audience(days, device, base)

    config = {name: os.getenv(name, "").strip() for name in GA4_REQUIRED_VARIABLES}
    key = tuple(config[name] for name in GA4_REQUIRED_VARIABLES) + (str(days), device, "audience")
    now = time.monotonic()
    with _cache_lock:
        cached = _ga4_audience_cache.get(key)
        if cached and cached[0] > now:
            return dict(cached[1])

    credentials_path = config["GA4_CREDENTIALS_PATH"]
    property_id = config["GA4_PROPERTY_ID"]
    result = _empty_audience(days, device, base)
    result["status"] = base.get("status", "ready")

    def read(
        dimensions: Sequence[str],
        metrics: Sequence[str],
        *,
        limit: int = 25,
        previous: bool = False,
    ) -> list[dict[str, Any]]:
        return _ga4_read(
            credentials_path,
            property_id,
            days,
            device,
            dimensions,
            metrics,
            limit=limit,
            previous=previous,
        )

    channel_metrics = ("sessions", "activeUsers", "engagedSessions", "screenPageViews")
    try:
        result["traffic_sources"] = _fold_sources(
            read(("sessionSource", "sessionMedium"), channel_metrics, limit=50)
        )
        # The same fold over the window before this one. A channel's share is
        # only a decision once you know which way it moved, and the alternative
        # -- asking the browser to remember last week -- would compare two
        # windows nobody chose together.
        result["previous_traffic_sources"] = _fold_sources(
            read(("sessionSource", "sessionMedium"), channel_metrics, limit=50, previous=True)
        )
        # First touch answers a different question from session source: which
        # channel *recruited* a user, rather than which one delivered this visit.
        # Direct and organic search routinely collect credit for work another
        # channel did, and only the two side by side show it.
        result["first_user_sources"] = _fold_sources(
            read(("firstUserSource", "firstUserMedium"), channel_metrics, limit=50),
            source_key="firstUserSource",
            medium_key="firstUserMedium",
        )
        result["devices"] = [
            {
                "device": row["deviceCategory"],
                "sessions": row["sessions"],
                "engagement_rate": row["engagementRate"],
            }
            for row in read(("deviceCategory",), ("sessions", "engagementRate"), limit=8)
            if row["deviceCategory"]
        ]
        result["browsers"] = [
            {
                "browser": row["browser"],
                "operating_system": row["operatingSystem"],
                "sessions": row["sessions"],
            }
            for row in read(("browser", "operatingSystem"), ("sessions",), limit=10)
            if row["browser"]
        ]
        result["landing_pages"] = [
            {
                "page": row["landingPage"],
                "sessions": row["sessions"],
                "engagement_rate": row["engagementRate"],
                "bounces": row["bounceRate"],
                "bounce_rate": row["bounceRate"],
            }
            for row in read(
                ("landingPage",), ("sessions", "engagementRate", "bounceRate"), limit=15
            )
            if row["landingPage"]
        ]
    except Exception as exc:  # a detail failure must not blank the summary tiles
        result = _empty_audience(days, device, base)
        result["status"] = "error"
        result["message"] = f"Google Analytics audience read failed: {type(exc).__name__}."
        return result

    with _cache_lock:
        _ga4_audience_cache[key] = (now + CACHE_SECONDS, dict(result))
    return result


#: Countries this business sells into. Everything else is not wrong, it is
#: unexplained -- and an unexplained country is the one thing on this tab worth
#: interrupting a CMO for, because it moves every site-wide rate above it.
EXPECTED_MARKETS = frozenset({"India"})

#: GA4 answers "we could not resolve this" with `(not set)`. The row is dropped
#: from a flat list, but never from the tree: a region removed from under its
#: country makes the regions stop summing to the country, and a total that does
#: not add up is worse than a level named honestly as unresolved.
UNRESOLVED_PLACE = "Not reported"


def _place(value: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {"(not set)", "(not provided)"}:
        return UNRESOLVED_PLACE
    return cleaned


def _rate(engaged: int, sessions: int) -> float | None:
    """Engagement as GA4 reports it: a proportion, not a percentage."""
    return engaged / sessions if sessions else None


def _share(part: int, whole: int) -> float | None:
    return round(part * 100 / whole, 1) if whole else None


def _fold_places(rows: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Roll country/region/city rows into one tree, summing only what is additive.

    Sessions, engaged sessions and views are counts and add up. `activeUsers`
    does not: GA4 de-duplicates a visitor within whatever grouping it was asked
    for, so a user who browsed from two cities is one user at country level and
    two if you add the city rows. Visitors therefore come from the country-level
    report, which GA4 de-duplicated itself, and the tree carries sessions and an
    engagement rate rebuilt from the counts underneath it.
    """
    tree: dict[str, dict[str, Any]] = {}
    for row in rows:
        country = _place(str(row.get("country", "")))
        region = _place(str(row.get("region", "")))
        city = _place(str(row.get("city", "")))
        sessions = int(row.get("sessions") or 0)
        engaged = int(row.get("engagedSessions") or 0)
        node = tree.setdefault(country, {"sessions": 0, "engaged": 0, "regions": {}})
        node["sessions"] += sessions
        node["engaged"] += engaged
        area = node["regions"].setdefault(region, {"sessions": 0, "engaged": 0, "cities": {}})
        area["sessions"] += sessions
        area["engaged"] += engaged
        town = area["cities"].setdefault(city, {"sessions": 0, "engaged": 0})
        town["sessions"] += sessions
        town["engaged"] += engaged
    return tree


def _country_rows(
    totals: Sequence[dict[str, Any]],
    tree: dict[str, dict[str, Any]],
    previous: dict[str, int],
) -> list[dict[str, Any]]:
    """One row per country, with the regions and cities inside it.

    `sessions` and `active_users` are GA4's own country-level figures. The
    regions hanging off each row are the tree's, and they sum to the tree's
    country total rather than to GA4's -- the two are the same sessions counted
    once each, but a sampled or thresholded row can make them differ by one, and
    a drill-down that silently disagreed with the row above it would be the
    harder bug to find. `tree_sessions` is carried so the console can say so.
    """
    total = sum(int(row.get("sessions") or 0) for row in totals)
    output: list[dict[str, Any]] = []
    for row in totals:
        name = _place(str(row.get("country", "")))
        node = tree.get(name, {"sessions": 0, "engaged": 0, "regions": {}})
        sessions = row.get("sessions")
        was = previous.get(name)
        regions = []
        for region_name, area in sorted(
            node["regions"].items(), key=lambda item: -item[1]["sessions"]
        ):
            cities = [
                {
                    "city": city_name,
                    "sessions": town["sessions"],
                    "engagement_rate": _rate(town["engaged"], town["sessions"]),
                    "share": _share(town["sessions"], area["sessions"]),
                }
                for city_name, town in sorted(
                    area["cities"].items(), key=lambda item: -item[1]["sessions"]
                )
            ]
            regions.append(
                {
                    "region": region_name,
                    "sessions": area["sessions"],
                    "engagement_rate": _rate(area["engaged"], area["sessions"]),
                    "share": _share(area["sessions"], node["sessions"]),
                    "cities": cities,
                }
            )
        output.append(
            {
                "country": name,
                "sessions": sessions,
                "active_users": row.get("activeUsers"),
                "engagement_rate": row.get("engagementRate"),
                "share": _share(int(sessions or 0), total),
                "expected": name in EXPECTED_MARKETS,
                # None, not 0: a country GA4 never reported last window and one
                # it reported as zero are different answers, and only the second
                # supports "this is new".
                "previous_sessions": was,
                "delta_sessions": (int(sessions or 0) - was) if was is not None else None,
                "tree_sessions": node["sessions"],
                "regions": regions,
            }
        )
    return output


def _fold_country_sources(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Country x traffic source, folded per country by the one channel rule.

    `_fold_sources` is reused rather than reimplemented so a channel is named and
    a rate rebuilt exactly as the site-wide table does it. A cross-tab whose
    "LinkedIn" meant something narrower than the row above would be worse than
    no cross-tab.
    """
    by_country: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_country.setdefault(_place(str(row.get("country", ""))), []).append(row)
    output = []
    for name, country_rows in by_country.items():
        channels = _fold_sources(country_rows)
        output.append(
            {
                "country": name,
                "sessions": sum(channel["sessions"] for channel in channels),
                "channels": channels,
            }
        )
    output.sort(key=lambda item: -item["sessions"])
    return output


def _fold_country_channels(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Country x GA4's own default channel group."""
    by_country: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        name = _place(str(row.get("country", "")))
        group = str(row.get("sessionDefaultChannelGroup", "")).strip() or "Unassigned"
        bucket = by_country.setdefault(name, {}).setdefault(
            group, {"channel": group, "sessions": 0, "engaged": 0}
        )
        bucket["sessions"] += int(row.get("sessions") or 0)
        bucket["engaged"] += int(row.get("engagedSessions") or 0)
    output = []
    for name, groups in by_country.items():
        channels = sorted(groups.values(), key=lambda item: -item["sessions"])
        total = sum(channel["sessions"] for channel in channels)
        for channel in channels:
            channel["share"] = _share(channel["sessions"], total)
            channel["engagement_rate"] = _rate(channel["engaged"], channel["sessions"])
        output.append({"country": name, "sessions": total, "channels": channels})
    output.sort(key=lambda item: -item["sessions"])
    return output


def _empty_geography(days: int, device: str, base: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": base.get("status", "not_connected"),
        "message": base.get("message", ""),
        "required_variables": list(GA4_REQUIRED_VARIABLES),
        "missing_variables": base.get("missing_variables", []),
        "range_days": days,
        "device": device,
        "countries": [],
        "country_sources": [],
        "country_channels": [],
        "has_previous": False,
    }


def ga4_geography(days: int = 28, device: str = "all") -> dict[str, Any]:
    """Where the sessions came from, three levels deep and two ways across.

    Separate from `ga4_audience` and failing on its own, the way `ga4_events`
    is: this is five reports, two of them cross-tabs at a cardinality GA4 can
    threshold or reject, and a rejection here must not take the channel table
    and the device panel down with it.

    The two cross-tabs answer deliberately different questions. `country_sources`
    uses `classify_source`, which is source-shaped -- LinkedIn, WhatsApp, the
    names of the places we post. `country_channels` uses GA4's own
    `sessionDefaultChannelGroup`, which is spend-shaped -- Organic Social,
    Referral, Email, Paid Search. Where the two disagree, the disagreement is the
    finding: it is usually a share that arrived untagged.
    """
    if days not in {7, 28, 90}:
        days = 28
    if device not in {"all", "desktop", "mobile", "tablet"}:
        device = "all"
    base = ga4_summary(days, device)
    if base.get("status") not in {"ready", "collecting"}:
        return _empty_geography(days, device, base)

    config = {name: os.getenv(name, "").strip() for name in GA4_REQUIRED_VARIABLES}
    key = tuple(config[name] for name in GA4_REQUIRED_VARIABLES) + (str(days), device, "geography")
    now = time.monotonic()
    with _cache_lock:
        cached = _ga4_geography_cache.get(key)
        if cached and cached[0] > now:
            return dict(cached[1])

    credentials_path = config["GA4_CREDENTIALS_PATH"]
    property_id = config["GA4_PROPERTY_ID"]
    result = _empty_geography(days, device, base)
    result["status"] = base.get("status", "ready")

    def read(
        dimensions: Sequence[str],
        metrics: Sequence[str],
        *,
        limit: int = 25,
        previous: bool = False,
    ) -> list[dict[str, Any]]:
        return _ga4_read(
            credentials_path,
            property_id,
            days,
            device,
            dimensions,
            metrics,
            limit=limit,
            previous=previous,
        )

    try:
        totals = [
            row
            for row in read(("country",), ("sessions", "activeUsers", "engagementRate"), limit=25)
            if row["country"]
        ]
        tree = _fold_places(
            read(("country", "region", "city"), ("sessions", "engagedSessions"), limit=200)
        )
        previous_rows = read(("country",), ("sessions",), limit=25, previous=True)
        previous = {
            _place(str(row.get("country", ""))): int(row.get("sessions") or 0)
            for row in previous_rows
            if row.get("country")
        }
        result["countries"] = _country_rows(totals, tree, previous)
        result["has_previous"] = bool(previous_rows)
        result["country_sources"] = _fold_country_sources(
            read(
                ("country", "sessionSource", "sessionMedium"),
                ("sessions", "activeUsers", "engagedSessions", "screenPageViews"),
                limit=200,
            )
        )
        result["country_channels"] = _fold_country_channels(
            read(
                ("country", "sessionDefaultChannelGroup"),
                ("sessions", "engagedSessions"),
                limit=100,
            )
        )
    except Exception as exc:  # a geography failure must not blank the other panels
        result = _empty_geography(days, device, base)
        result["status"] = "error"
        result["message"] = f"Google Analytics geography read failed: {type(exc).__name__}."
        return result

    with _cache_lock:
        _ga4_geography_cache[key] = (now + CACHE_SECONDS, dict(result))
    return result


# The steps of the calculator funnel, in order, as (label, GA4 event name).
#
# This is the website's only revenue path: a phone-verified financing enquiry
# that ends as a row in `calcLeads`. Naming the steps here rather than in the
# browser means the drop-off between them is computed once, server-side, from
# one response -- two caches expiring independently would otherwise let a later
# step show more sessions than an earlier one.
GA4_FUNNEL_STEPS: tuple[tuple[str, str], ...] = (
    ("Opened the calculator", "calculator_start"),
    ("Asked for an OTP", "otp_requested"),
    ("Verified the number", "otp_verified"),
    ("Became a lead", "generate_lead"),
)
# Events that mark real intent, whether or not GA4 admin has been told to treat
# them as key events yet.
GA4_INTENT_EVENTS: tuple[str, ...] = (
    "generate_lead",
    "otp_verified",
    "whatsapp_click",
    "deck_request",
    "contact_submit",
)


def _empty_events(days: int, device: str, base: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": base.get("status", "not_connected"),
        "message": base.get("message", ""),
        "required_variables": list(GA4_REQUIRED_VARIABLES),
        "missing_variables": base.get("missing_variables", []),
        "range_days": days,
        "device": device,
        "events": [],
        "funnel": [],
        "scroll_depth": [],
        "scroll_message": "",
        "key_events": None,
        "session_key_event_rate": None,
        "key_event_message": "",
        "instrumented": False,
    }


def _funnel_from_counts(counts: dict[str, int | float | None]) -> list[dict[str, Any]]:
    """Turn per-event counts into ordered steps with step-to-step retention.

    An event GA4 has never seen is absent from the response, and absent is not
    zero: "nobody reached this step" and "this step was never instrumented" are
    opposite findings, and only the first is a marketing problem. A step with no
    row therefore carries `count: None` and `instrumented: False`, and the
    retention against it is `None` rather than a 0% that would read as a total
    collapse of the funnel.
    """
    steps: list[dict[str, Any]] = []
    previous: int | float | None = None
    for label, event_name in GA4_FUNNEL_STEPS:
        count = counts.get(event_name)
        retention: float | None = None
        if count is not None and previous is not None and previous:
            retention = round(count * 100 / previous, 1)
        steps.append({
            "step": label,
            "event": event_name,
            "count": count,
            "instrumented": count is not None,
            "retention": retention,
        })
        if count is not None:
            previous = count
    return steps


def ga4_events(days: int = 28, device: str = "all") -> dict[str, Any]:
    """What visitors actually did, and how far they got.

    Separate from `ga4_summary` on purpose. GA4 renamed the conversion metrics
    (`conversions` -> `keyEvents`, `sessionConversionRate` ->
    `sessionKeyEventRate`) and a property can answer to either name depending on
    when it was created. Asking for the wrong one is a 400 for the whole request,
    so this asks in its own request, tries both names, and reports which -- a
    rejected metric name here cannot blank the summary tiles, which is the same
    containment `ga4_technical_summary` uses for its page table.
    """
    if days not in {7, 28, 90}:
        days = 28
    if device not in {"all", "desktop", "mobile", "tablet"}:
        device = "all"
    base = ga4_summary(days, device)
    if base.get("status") not in {"ready", "collecting"}:
        return _empty_events(days, device, base)

    config = {name: os.getenv(name, "").strip() for name in GA4_REQUIRED_VARIABLES}
    key = tuple(config[name] for name in GA4_REQUIRED_VARIABLES) + (str(days), device, "events")
    now = time.monotonic()
    with _cache_lock:
        cached = _ga4_events_cache.get(key)
        if cached and cached[0] > now:
            return dict(cached[1])

    credentials_path = config["GA4_CREDENTIALS_PATH"]
    property_id = config["GA4_PROPERTY_ID"]
    result = _empty_events(days, device, base)
    result["status"] = base.get("status", "ready")

    try:
        rows = _ga4_rows(
            _ga4_request(
                credentials_path,
                property_id,
                _audience_payload(
                    days,
                    device,
                    ("eventName",),
                    ("eventCount", "totalUsers"),
                    limit=50,
                    order_by="eventCount",
                ),
            ),
            ("eventName",),
            ("eventCount", "totalUsers"),
        )
    except Exception as exc:  # an event failure must not blank the summary tiles
        result["status"] = "error"
        result["message"] = f"Google Analytics event read failed: {type(exc).__name__}."
        return result

    counts: dict[str, int | float | None] = {}
    events: list[dict[str, Any]] = []
    for row in rows:
        name = row.get("eventName") or ""
        if not name:
            continue
        counts[name] = row.get("eventCount")
        events.append({
            "event": name,
            "count": row.get("eventCount"),
            "users": row.get("totalUsers"),
            "intent": name in GA4_INTENT_EVENTS,
        })
    result["events"] = events
    result["funnel"] = _funnel_from_counts(counts)

    # How far down the page people actually got.
    #
    # GA4's enhanced measurement fires `scroll` once a visitor reaches 90% depth,
    # so this needs no code on the website -- it is already being collected. Read
    # against page views for the same page it answers the question a view count
    # cannot: a post that was opened and a post that was read are different
    # outcomes, and only one of them is worth commissioning more of.
    try:
        depth_rows = _ga4_rows(
            _ga4_request(
                credentials_path,
                property_id,
                _audience_payload(
                    days, device, ("pagePath", "eventName"),
                    ("eventCount",), limit=100, order_by="eventCount",
                ),
            ),
            ("pagePath", "eventName"),
            ("eventCount",),
        )
    except Exception as exc:  # a depth failure must not blank the funnel
        result["scroll_message"] = f"Google Analytics scroll read failed: {type(exc).__name__}."
        depth_rows = []
    views: dict[str, int | float | None] = {}
    reached: dict[str, int | float | None] = {}
    for row in depth_rows:
        page = row.get("pagePath") or ""
        if not page:
            continue
        if row.get("eventName") == "page_view":
            views[page] = row.get("eventCount")
        elif row.get("eventName") == "scroll":
            reached[page] = row.get("eventCount")
    depth = []
    for page, view_count in views.items():
        end = reached.get(page)
        # A page with no scroll row was viewed and never finished. That is a
        # measured zero, not an unmeasured one: the scroll event is collected
        # site-wide, so its absence for a page GA4 did report views for means
        # nobody reached the bottom.
        finished = end if end is not None else 0
        share = (
            round(finished * 100 / view_count, 1)
            if view_count not in (None, 0) else None
        )
        depth.append({
            "page": page,
            "views": view_count,
            "reached_end": finished,
            "share": share,
        })
    depth.sort(key=lambda item: -(item["views"] or 0))
    result["scroll_depth"] = depth[:15]
    # Enhanced measurement supplies `page_view` on its own, so the presence of a
    # page_view proves the tag works and proves nothing about instrumentation.
    result["instrumented"] = any(name in counts for name in GA4_INTENT_EVENTS)

    for metric_pair in (("keyEvents", "sessionKeyEventRate"), ("conversions", "sessionConversionRate")):
        try:
            totals = _ga4_values_named(
                _ga4_request(
                    credentials_path,
                    property_id,
                    _totals_payload(days, device, metric_pair),
                ),
                metric_pair,
            )
        except Exception:
            continue
        result["key_events"] = totals.get(metric_pair[0])
        result["session_key_event_rate"] = totals.get(metric_pair[1])
        break
    else:
        result["key_event_message"] = (
            "This property reported neither keyEvents nor conversions. "
            "Key events are configured in Google Analytics admin, not here."
        )

    with _cache_lock:
        _ga4_events_cache[key] = (now + CACHE_SECONDS, dict(result))
    return result


def _totals_payload(days: int, device: str, metrics: Sequence[str]) -> dict[str, Any]:
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=days - 1)
    payload: dict[str, Any] = {
        "dateRanges": [{"startDate": start.isoformat(), "endDate": end.isoformat()}],
        "metrics": [{"name": name} for name in metrics],
        "limit": "1",
    }
    if device != "all":
        payload["dimensionFilter"] = {
            "filter": {
                "fieldName": "deviceCategory",
                "stringFilter": {"matchType": "EXACT", "value": device},
            }
        }
    return payload


def _ga4_values_named(
    report: dict[str, Any], metrics: Sequence[str]
) -> dict[str, int | float | None]:
    rows = report.get("rows") if isinstance(report, dict) else None
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return {name: None for name in metrics}
    values = rows[0].get("metricValues")
    values = values if isinstance(values, list) else []
    return {
        name: _number(values[index].get("value"))
        if index < len(values) and isinstance(values[index], dict)
        else None
        for index, name in enumerate(metrics)
    }
