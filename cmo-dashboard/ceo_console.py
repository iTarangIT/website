from __future__ import annotations

import datetime as dt
import json
import mimetypes
import os
import re
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import ceo_actions
import ceo_analytics
import ceo_insights
import ceo_social
import console_auth
import dashboard_server
import analytics_readers
import ceo_artifacts
import ceo_blog_publish
import ceo_publish
import ceo_reader
import ceo_version
import console_board
from ceo_page import page_build_header, render_page
from cmo_runtime import competitors, news_radar, topic_proposals
from cmo_runtime.console_db import ConsoleDBError, norm_key, norm_tokens
from cmo_runtime.decisions import DecisionConflict, DecisionError, DecisionStore
from cmo_runtime.task_file import TaskFileError

PROFILE_DIR = dashboard_server.PROFILE_DIR
TASKS_FILE = dashboard_server.TASKS_FILE



def handles(path: str) -> bool:
    value = urlparse(path).path
    return value == "/ceo" or value.startswith("/ceo/")


def _json(handler: Any, status: int, payload: Any) -> None:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _bytes(
    handler: Any,
    status: int,
    content_type: str,
    body: bytes,
    extra_headers: dict[str, str] | None = None,
) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    for name, value in (extra_headers or {}).items():
        handler.send_header(name, value)
    handler.end_headers()
    handler.wfile.write(body)


def _body(handler: Any) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length < 0 or length > 65536:
        raise ValueError("request body is too large")
    value = json.loads(handler.rfile.read(length) or b"{}")
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def _authorized(handler: Any) -> tuple[str, str] | None:
    return console_auth.authorize(handler, "ceo")


def _task(task_id: str) -> dict[str, Any]:
    board = console_board.read_board(TASKS_FILE, PROFILE_DIR)
    task = next((item for item in board["tasks"] if item["id"] == task_id), None)
    if task is None:
        raise LookupError("task not found")
    return task


def _service() -> topic_proposals.TopicProposalService:
    """One short-lived service per request; the SQLite connection closes with it."""
    return topic_proposals.TopicProposalService(PROFILE_DIR)


def state_payload(
    range_key: str = "28",
    device: str = "all",
    *,
    start: str = "",
    end: str = "",
) -> dict[str, Any]:
    board = console_board.read_board(TASKS_FILE, PROFILE_DIR)
    # GA4 and the trend collectors only understand fixed windows; Search Console
    # takes the chip selection as it is, including "all" and a custom range.
    range_days = {"7": 7, "28": 28, "90": 90}.get(range_key, 28)
    trend_days = range_days
    rows, trend_messages = analytics_readers.trending_rows(trend_days)
    service = _service()
    try:
        # Read model only — every value here comes from the database or the board,
        # never from a live scrape at page load.
        topics = service.state()
    finally:
        service.database.close()
    _label_topics(topics, rows, trend_days)
    search = ceo_analytics.cached_report(range_key, device, start=start, end=end)
    ga4_detail = analytics_readers.ga4_technical_summary(range_days, device)
    # The join is done here, once, rather than in the browser: the two halves come
    # from two APIs on two cadences, and a client-side join would leave the
    # Blog performance table disagreeing with the tiles above it whenever one
    # cache expired before the other.
    posts = ceo_analytics.blog_performance(
        search,
        ga4_detail.get("pages") or [],
        titles=_blog_titles(board["blogs"]),
    )
    audience = analytics_readers.ga4_audience(range_days, device)
    geography = analytics_readers.ga4_geography(range_days, device)
    events = analytics_readers.ga4_events(range_days, device)
    pages = ga4_detail.get("pages") or []
    # The rules run here, on the server, for the same reason the blog join does:
    # they read five payloads that each carry their own cache, and a browser
    # running them would be reasoning across windows that expired apart.
    found = ceo_insights.findings(
        ga4=ga4_detail,
        audience=audience,
        geography=geography,
        events=events,
        pages=pages,
        posts=posts.get("posts") or [],
    )
    return {
        "topics": topics,
        "blogs": board["blogs"],
        "trending": rows,
        "trending_messages": trend_messages,
        "watchlist": ceo_actions.read_watchlist(PROFILE_DIR),
        "research_queue": ceo_actions.read_research_queue(PROFILE_DIR),
        "social": social_payload(board["blogs"]),
        "analytics": {
            "search": search,
            "search_console": dashboard_server.gsc_summary(),
            # `ga4_detail` is `ga4_summary` plus the page table and the collection
            # start, so reading it here saves a second summary round-trip. The page
            # rows stay on this side: they are the GA4 half of the blog join above,
            # and no panel renders them since "Which pages were read" was removed.
            "ga4": {name: value for name, value in ga4_detail.items() if name != "pages"},
            "ga4_audience": audience,
            "ga4_geography": geography,
            "ga4_events": events,
            # The page rows stopped at the server while they were only the GA4
            # half of the blog join. They are a panel again, and the join still
            # reads the same list — one request, two readers, one window.
            "pages": pages,
            "posts": posts,
            "insights": found,
            "summary": ceo_insights.executive_summary(
                found, ga4_detail, events, range_days=range_days
            ),
            "campaigns": ceo_insights.campaign_performance(audience, _crossposts_sent(range_days)),
        },
        "controls": {"range": range_key, "range_days": range_days, "device": device, "start": start, "end": end},
    }


def _crossposts_sent(range_days: int) -> list[dict[str, Any]]:
    """Posts Buffer accepted inside the analytics window.

    Its own connection, opened and closed here, because `state_payload` already
    opens one for the topic service and holding a second across that read would
    keep a write lock waiting on a report nobody is blocked on.
    """
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=range_days)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    service = _service()
    try:
        return service.database.crossposts_sent_since(since)
    except ConsoleDBError:
        # A campaign panel is not worth failing the whole tab for.
        return []
    finally:
        service.database.close()


#: Trend rows come from three places and only one of them measures a direction.
#: `_collector_rows` hands back whatever the X and Facebook collectors wrote, with
#: no delta and no defined metric, so "trending" cannot be true or false of them.
#: Only Google Search rows carry a measured previous period.
TRENDING_SOURCE = "Google Search"


def _trending_for(
    proposal: dict[str, Any], rows: list[dict[str, Any]], window_days: int
) -> dict[str, Any]:
    """The trend row this candidate is actually about, or `{}`.

    Deliberately hard to satisfy. A wrong "Trending" badge attaches a real,
    checkable number to the wrong subject, which is worse than showing nothing:
    the number invites a decision. Four conditions, each earning its place:

    * Google Search only -- the other collectors measure no direction (above).
    * A positive measured `delta`. `None` means the query is new this window and
      has no prior period, which reads as the most trending case and is exactly
      the one with no evidence behind it.
    * Every content word of the query appears in the candidate's title or
      keywords. Containment in that direction is the claim being made -- "this
      candidate is about that query" -- and it is whole tokens, never substrings,
      because substring matching is how `ev` matches `seven` and `development`.
    * Two content words at least, unless the titles match outright. A single word
      trending ("battery") is not evidence about any particular battery topic.

    Matching is against the title and keywords only. The subject is a long
    triager sentence and the outline is prose; both drag in enough generic words
    to make containment meaningless.

    There is no negative case. Search Console is asked for 20 rows, so absence
    from the list means "not in a 20-row sample", never "not trending" -- and no
    badge is the honest way to say that.
    """
    haystack = set(norm_tokens(str(proposal.get("title", ""))))
    for keyword in proposal.get("keywords") or []:
        haystack.update(norm_tokens(str(keyword)))
    if not haystack:
        return {}
    best: dict[str, Any] = {}
    for row in rows:
        if row.get("source") != TRENDING_SOURCE:
            continue
        delta = row.get("delta")
        if not isinstance(delta, (int, float)) or isinstance(delta, bool) or delta <= 0:
            continue
        title = str(row.get("title", ""))
        tokens = set(norm_tokens(title))
        if not tokens or not tokens <= haystack:
            continue
        if len(tokens) < 2 and norm_key(title) != norm_key(str(proposal.get("title", ""))):
            continue
        if not best or delta > best["delta"]:
            best = {
                "query": title,
                "source": TRENDING_SOURCE,
                "metric": str(row.get("metric", "") or ""),
                "current": row.get("current"),
                "delta": delta,
                "window_days": window_days,
            }
    return best


def _label_topics(topics: dict[str, Any], rows: list[dict[str, Any]], window_days: int) -> None:
    """Attach the trend match to each candidate, in place.

    The join happens here for the reason the blog join below does: both halves are
    already in hand, the trend rows are cached for five minutes and the topics are
    not, and a browser-side join would leave a badge disagreeing with the trends
    table on the same screen. It also keeps `TopicProposalService.state()` a pure
    database read, which the console's tests assert.
    """
    for group in ("proposals", "archived"):
        for proposal in topics.get(group) or []:
            match = _trending_for(proposal, rows, window_days)
            if match:
                proposal["trending"] = match


def _slug_of(blog: dict[str, Any]) -> str:
    """The article's slug, from its parsed front matter. Empty until it is written."""
    article = blog.get("article") or {}
    metadata = article.get("metadata") or {}
    return str(metadata.get("slug", "") or "").strip()


def _blog_titles(blogs: list[dict[str, Any]]) -> dict[str, str]:
    """slug -> the title the board shows, so an analytics row is not read as a URL."""
    return {slug: str(blog.get("title", "")) for blog in blogs if (slug := _slug_of(blog))}


def social_payload(blogs: list[dict[str, Any]]) -> dict[str, Any]:
    """What the Social tab renders: one row per published article, with its drafts.

    Read model only. Buffer is not called here — a page load must not depend on
    a third party being up, and the channel list is fetched by the preflight the
    Send button asks for, not by every three-second poll.
    """
    from cmo_runtime.console_db import ConsoleDB

    published = [blog for blog in blogs if (blog.get("blog") or {}).get("state") == "published"]
    database = ConsoleDB(PROFILE_DIR)
    try:
        articles = [
            {
                "task_id": blog["id"],
                "title": blog.get("title", ""),
                "slug": _slug_of(blog),
                "url": (blog.get("blog") or {}).get("url", ""),
                "drafts": database.crosspost_drafts(str(blog["id"])),
            }
            for blog in published
        ]
        counts = database.crosspost_summary()
    finally:
        database.close()
    return {
        "articles": articles,
        "counts": counts,
        "connected": ceo_social.BufferClient.configured(str(PROFILE_DIR)),
    }


def dispatch(handler: Any, method: str) -> bool:
    path = urlparse(handler.path).path
    if not handles(path):
        return False
    if method == "GET" and path in {"/ceo", "/ceo/"}:
        # The same build identity the footer shows, readable without a browser.
        body = render_page()
        _bytes(
            handler,
            HTTPStatus.OK,
            "text/html; charset=utf-8",
            body,
            extra_headers={"X-CMO-Build": page_build_header()},
        )
        return True
    if method == "GET" and path == "/ceo/api/config":
        _json(handler, HTTPStatus.OK, console_auth.supabase_browser_config())
        return True
    auth = _authorized(handler)
    if auth is None:
        return True
    email, _role = auth
    if method == "GET" and path == "/ceo/api/version":
        # Asked every few seconds by every open console, so it stays a handful of
        # stat calls: no board parse, no Search Console, no Firecrawl, no network.
        # The client refetches state only when this token moves.
        _json(handler, HTTPStatus.OK, ceo_version.version_payload(PROFILE_DIR))
        return True
    if method == "GET" and path == "/ceo/api/state":
        query = parse_qs(urlparse(handler.path).query)
        range_key = query.get("range", ["28"])[0].strip().casefold()
        if range_key not in set(ceo_analytics.RANGE_LABELS):
            range_key = "28"
        device = query.get("device", ["all"])[0]
        if device not in ceo_analytics.DEVICES:
            device = "all"
        _json(
            handler,
            HTTPStatus.OK,
            state_payload(
                range_key,
                device,
                start=query.get("start", [""])[0][:10],
                end=query.get("end", [""])[0][:10],
            ),
        )
        return True
    if method == "GET" and path == "/ceo/publish-check":
        # Reports eligibility and, only when eligible, mints this human's
        # single-use instruction. Reporting is not publishing.
        task_id = parse_qs(urlparse(handler.path).query).get("task", [""])[0]
        try:
            check = ceo_publish.preflight(PROFILE_DIR, task_id, github=ceo_publish.GitHubAPI())
        except ceo_publish.PublicationRefused as error:
            _json(handler, HTTPStatus.OK, {"eligible": False, "blockers": [str(error)]})
            return True
        payload = check.as_dict()
        payload["request_id"] = (
            ceo_publish.issue_request(PROFILE_DIR, task_id, actor=email, commit=check.commit)
            if check.eligible
            else ""
        )
        _json(handler, HTTPStatus.OK, payload)
        return True
    if method == "POST" and path == "/ceo/publish":
        body = _body(handler)
        try:
            outcome = ceo_publish.publish(
                PROFILE_DIR,
                str(body.get("task", "")),
                actor=email,
                role=_role,
                request_id=str(body.get("request_id", "")),
                github=ceo_publish.GitHubAPI(),
            )
        except ceo_publish.PublicationConflict as error:
            _json(handler, HTTPStatus.CONFLICT, {"error": str(error)})
            return True
        except (ceo_publish.PublicationRefused, TaskFileError) as error:
            _json(handler, HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return True
        _json(handler, HTTPStatus.OK, outcome)
        return True
    if method == "GET" and path == "/ceo/blog-publish-check":
        # Same shape as Gate 2's check, one step earlier in the chain: reports
        # eligibility to push the article to cmo-changes and, only when eligible,
        # mints this human's single-use instruction. Reporting is not publishing.
        task_id = parse_qs(urlparse(handler.path).query).get("task", [""])[0]
        try:
            # The console has one button, and pressing it records Gate 1 (see
            # `ceo_blog_publish.publish`). So the check asks whether this article
            # *can* be published, not whether someone already said it should be.
            check = ceo_blog_publish.preflight(PROFILE_DIR, task_id, require_approval=False)
        except ceo_blog_publish.PublicationRefused as error:
            _json(handler, HTTPStatus.OK, {"eligible": False, "blockers": [str(error)]})
            return True
        payload = check.as_dict()
        payload["request_id"] = (
            ceo_blog_publish.issue_request(PROFILE_DIR, task_id, actor=email, head=check.head)
            if check.eligible
            else ""
        )
        _json(handler, HTTPStatus.OK, payload)
        return True
    if method == "POST" and path == "/ceo/blog-publish":
        if os.getenv("CMO_DASHBOARD_PREVIEW", "").casefold() in {"1", "true", "yes"}:
            _json(handler, HTTPStatus.FORBIDDEN, {"error": "preview mode"})
            return True
        body = _body(handler)
        try:
            outcome = ceo_blog_publish.publish(
                PROFILE_DIR,
                str(body.get("task", "")),
                actor=email,
                role=_role,
                request_id=str(body.get("request_id", "")),
            )
        except ceo_blog_publish.PublicationConflict as error:
            _json(handler, HTTPStatus.CONFLICT, {"error": str(error)})
            return True
        except (ceo_blog_publish.PublicationRefused, TaskFileError) as error:
            _json(handler, HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return True
        _json(handler, HTTPStatus.OK, outcome)
        return True
    if method == "GET" and path == "/ceo/social-check":
        # Same preflight/instruction shape as the two publish gates, one step
        # further along: reports whether the drafts for a *live* article may be
        # queued in Buffer, and only then mints this human's single-use token.
        # This is the one route that talks to Buffer, so it is a click, never a poll.
        task_id = parse_qs(urlparse(handler.path).query).get("task", [""])[0]
        try:
            check = ceo_social.preflight(PROFILE_DIR, task_id)
        except ceo_publish.PublicationRefused as error:
            _json(handler, HTTPStatus.OK, {"eligible": False, "blockers": [str(error)]})
            return True
        payload = check.as_dict()
        payload["request_id"] = (
            ceo_social.issue_request(
                PROFILE_DIR,
                task_id,
                actor=email,
                fingerprint=check.fingerprint,
                platforms=check.sendable,
            )
            if check.eligible
            else ""
        )
        _json(handler, HTTPStatus.OK, payload)
        return True
    if method == "GET" and path == "/ceo/artifact":
        task_id = parse_qs(urlparse(handler.path).query).get("task", [""])[0]
        try:
            task = _task(task_id)
            if console_board.artifact_for(task, PROFILE_DIR) is None:
                raise FileNotFoundError
            content_type, body = dashboard_server.load_task_attachment(task_id, TASKS_FILE, PROFILE_DIR)
        except (LookupError, FileNotFoundError, ValueError, PermissionError):
            _json(handler, HTTPStatus.NOT_FOUND, {"error": "artifact is unavailable"})
            return True
        _bytes(handler, HTTPStatus.OK, content_type, body)
        return True
    if method == "GET" and path == "/ceo/image":
        query = parse_qs(urlparse(handler.path).query)
        task_id = query.get("task", [""])[0]
        slot = query.get("slot", [""])[0]
        try:
            task = _task(task_id)
            image = (
                ceo_artifacts.cover_for(task, PROFILE_DIR)
                if slot.casefold() == "cover"
                else ceo_artifacts.image_for(task, slot, PROFILE_DIR)
            )
            if image is None:
                raise FileNotFoundError
            body = image.read_bytes()
        except (LookupError, FileNotFoundError, OSError):
            _json(handler, HTTPStatus.NOT_FOUND, {"error": "image is unavailable"})
            return True
        content_type = mimetypes.guess_type(image.name)[0] or "application/octet-stream"
        _bytes(handler, HTTPStatus.OK, content_type, body)
        return True
    if method != "POST":
        _json(handler, HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method not allowed"})
        return True
    if os.getenv("CMO_DASHBOARD_PREVIEW", "").casefold() in {"1", "true", "yes"}:
        _json(handler, HTTPStatus.FORBIDDEN, {"error": "preview mode"})
        return True
    try:
        if path == "/ceo/api/upload":
            query = parse_qs(urlparse(handler.path).query)
            task_id = query.get("task", [""])[0]
            slot = query.get("slot", [""])[0]
            filename = handler.headers.get("X-Filename", "")
            length = int(handler.headers.get("Content-Length", "0"))
            if length < 0 or length > ceo_artifacts.MAX_UPLOAD_BYTES:
                raise TaskFileError("image exceeds the 5 MB upload limit")
            destination = ceo_artifacts.save_upload(
                PROFILE_DIR,
                task_id,
                slot,
                filename,
                handler.rfile.read(length),
            )
            result = {"ok": True, "filename": destination.name, "slot": slot}
        elif path == "/ceo/api/generate-image":
            payload = _body(handler)
            result = ceo_artifacts.generate_image(
                PROFILE_DIR,
                str(payload.get("task_id", "")),
                str(payload.get("slot", "")),
                str(payload.get("scene", "")),
                alt_text=str(payload.get("alt", "")),
            )
        elif path in {
            "/ceo/api/propose",
            "/ceo/api/proposal/approve",
            "/ceo/api/proposal/suggest",
            "/ceo/api/proposal/reject",
            "/ceo/api/proposal/undo-rejection",
            "/ceo/api/proposal/archive",
            "/ceo/api/proposal/restore",
            "/ceo/api/competitor",
            "/ceo/api/radar/scan",
        }:
            payload = _body(handler)
            service = _service()
            try:
                if path == "/ceo/api/competitor":
                    # No console panel calls this any more -- "Which website do you
                    # want to replicate?" was removed from the Analytics tab. It is
                    # kept deliberately: analysing a domain is the only thing that
                    # writes the `competitors` table, and the news radar builds its
                    # standing competitor beat from that table. Deleting this would
                    # quietly drop that beat back to its generic fallback query.
                    result = competitors.CompetitorService(
                        PROFILE_DIR, database=service.database
                    ).analyse(str(payload.get("target", "")), email)
                elif path == "/ceo/api/propose":
                    run = service.propose(str(payload.get("subject", "")), email)
                    result = {"ok": True, **run.as_dict()}
                elif path == "/ceo/api/radar/scan":
                    # The same sweep the daily job runs, on demand. It refuses on
                    # its own budget floor, so a button press cannot spend the
                    # credits a manual subject would need.
                    sweep = news_radar.NewsRadar(
                        PROFILE_DIR, service=service, database=service.database
                    ).scan(email, mode="manual", dry_run=bool(payload.get("dry_run")))
                    result = {"ok": sweep.status == "completed", **sweep.as_dict()}
                else:
                    proposal_id = payload.get("proposal_id")
                    if not isinstance(proposal_id, int) or proposal_id <= 0:
                        raise ValueError("a positive proposal_id is required")
                    if path == "/ceo/api/proposal/approve":
                        result = service.approve(proposal_id, email)
                    elif path == "/ceo/api/proposal/suggest":
                        result = service.suggest_changes(
                            proposal_id, str(payload.get("comment", "")), email
                        )
                        result.pop("proposal", None)
                    elif path == "/ceo/api/proposal/reject":
                        result = service.reject(proposal_id, str(payload.get("reason", "")), email)
                    elif path == "/ceo/api/proposal/archive":
                        result = service.archive(proposal_id, email)
                    elif path == "/ceo/api/proposal/restore":
                        result = service.restore(proposal_id, email)
                    else:
                        result = service.undo_rejection(proposal_id, email)
            finally:
                service.database.close()
        elif path == "/ceo/api/article/preview":
            # The editor's live preview renders through the same reader the page
            # uses, so what he sees is exactly what will be served. Writes nothing.
            length = int(handler.headers.get("Content-Length", "0"))
            if length < 0 or length > ceo_actions.MAX_ARTICLE_BYTES + 4096:
                raise TaskFileError("the draft exceeds the 512 KB limit")
            payload = json.loads(handler.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("JSON object required")
            rendered = ceo_reader.render_article(str(payload.get("text", "")))
            result = {
                "ok": True,
                "html": rendered["html"],
                "review_notes_html": rendered["review_notes_html"],
                "review_note_titles": rendered["review_note_titles"],
            }
        elif path == "/ceo/api/article/edit":
            # A human rewriting a sentence. It archives the prior version and joins
            # the approval thread; it never touches DecisionStore.
            length = int(handler.headers.get("Content-Length", "0"))
            if length < 0 or length > ceo_actions.MAX_ARTICLE_BYTES + 4096:
                raise TaskFileError("the edited article exceeds the 512 KB limit")
            payload = json.loads(handler.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ValueError("JSON object required")
            task_id = str(payload.get("task_id", "")).strip()
            if not re.fullmatch(r"TASK-[0-9]+", task_id):
                raise ValueError("valid task_id is required")
            result = ceo_actions.save_article_edit(
                PROFILE_DIR, task_id, str(payload.get("text", "")), email
            )
        elif path == "/ceo/api/article/title":
            # Renaming the piece. One press moves the front-matter title the published
            # page uses, the article's own H1, and both copies of the title on the
            # board card — the four places a headline was written down and none of
            # them kept in step. It goes through the same revision and the same
            # refusals as any other edit to the article.
            payload = _body(handler)
            task_id = str(payload.get("task_id", "")).strip()
            if not re.fullmatch(r"TASK-[0-9]+", task_id):
                raise ValueError("valid task_id is required")
            result = ceo_actions.rename_article(
                PROFILE_DIR, task_id, str(payload.get("title", "")), email
            )
        else:
            payload = _body(handler)
            if path == "/ceo/api/watchlist":
                result = {
                    "ok": True,
                    "watchlist": ceo_actions.update_watchlist(
                        PROFILE_DIR,
                        str(payload.get("keyword", "")),
                        str(payload.get("action", "")),
                    ),
                }
            elif path == "/ceo/api/research-queue":
                # The Analytics → Topics bridge. Queuing spends no credits and
                # mints no board card; it only puts the subject in front of him.
                result = {
                    "ok": True,
                    "research_queue": ceo_actions.update_research_queue(
                        PROFILE_DIR,
                        str(payload.get("subject", "")),
                        str(payload.get("action", "")),
                        reason=str(payload.get("reason", "")),
                        actor=email,
                    ),
                }
            else:
                task_id = str(payload.get("task_id", "")).strip()
                if not re.fullmatch(r"TASK-[0-9]+", task_id):
                    raise ValueError("valid task_id is required")
                if path == "/ceo/api/revision":
                    round_number = ceo_actions.request_revision(
                        PROFILE_DIR,
                        task_id,
                        str(payload.get("comment", "")),
                        email,
                    )
                    result = {"ok": True, "revision_round": round_number}
                elif path == "/ceo/api/publish-date":
                    # A day a human wrote down, nothing more. No job reads it, and
                    # publishing is still a press -- see `set_publish_date`.
                    result = ceo_actions.set_publish_date(
                        PROFILE_DIR, task_id, str(payload.get("publish_at", "")), email
                    )
                elif path == "/ceo/api/blog-retry":
                    # Requeue a write that failed. Not a decision, not an approval,
                    # and refused outright on a card a human put on hold.
                    result = ceo_actions.retry_write(PROFILE_DIR, task_id, email)
                elif path == "/ceo/api/social/generate":
                    # Writes three drafts and stores them. Sends nothing: the copy
                    # exists so a human can read it before deciding to.
                    result = ceo_social.generate(PROFILE_DIR, task_id, actor=email)
                elif path == "/ceo/api/social/draft":
                    # A human's edit of one draft, checked against the platform's
                    # own limit here rather than discovered by Buffer later.
                    result = ceo_social.save_draft(
                        PROFILE_DIR,
                        task_id,
                        platform=str(payload.get("platform", "")),
                        body=str(payload.get("body", "")),
                        thread=[str(item) for item in payload.get("thread", []) or []],
                        actor=email,
                    )
                elif path == "/ceo/api/social/send":
                    # The one call that reaches Buffer. The instruction it consumes
                    # was minted by `/ceo/social-check` for this human and this
                    # article, and a partial send is reported as one.
                    result = ceo_social.send(
                        PROFILE_DIR,
                        task_id,
                        actor=email,
                        role=_role,
                        request_id=str(payload.get("request_id", "")),
                        platforms=[str(item) for item in payload.get("platforms", []) or []],
                    )
                elif path == "/ceo/api/decision":
                    decision = str(payload.get("decision", "")).strip()
                    task = _task(task_id)
                    commit = str(
                        task.get("commit_hash(es)", task.get("change_commit", task.get("commit", "")))
                    ).strip()
                    stored = DecisionStore(PROFILE_DIR).decide(
                        task_id,
                        decision,
                        approver_id=email,
                        surface="dashboard",
                        card_commit_sha=commit,
                        commit_sha=commit,
                        # What was approved, not merely that something was. Publish
                        # recomputes this and refuses if the card has moved since —
                        # and if it has, the components say which part moved.
                        publish_fingerprint=console_board.publish_fingerprint(task, PROFILE_DIR),
                        components=console_board.publish_component_record(task, PROFILE_DIR),
                    )
                    result = {"ok": stored.recorded}
                else:
                    _json(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return True
    except ceo_publish.PublicationConflict as exc:
        # A used instruction, a moved article, a post Buffer already holds. 409 so
        # the browser can say "read it again" rather than offer a blind retry.
        _json(handler, HTTPStatus.CONFLICT, {"error": str(exc)})
        return True
    except (
        ValueError,
        json.JSONDecodeError,
        TaskFileError,
        ConsoleDBError,
        ceo_publish.PublicationRefused,
        topic_proposals.ProposalRefused,
        news_radar.RadarRefused,
        competitors.CompetitorRefused,
    ) as exc:
        _json(handler, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        return True
    except LookupError as exc:
        _json(handler, HTTPStatus.NOT_FOUND, {"error": str(exc)})
        return True
    except DecisionConflict as exc:
        _json(handler, HTTPStatus.CONFLICT, {"error": str(exc)})
        return True
    except DecisionError as exc:
        _json(handler, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        return True
    _json(handler, HTTPStatus.OK, result)
    return True
