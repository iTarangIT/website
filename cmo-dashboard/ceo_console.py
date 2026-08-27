from __future__ import annotations

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
from cmo_runtime.console_db import ConsoleDBError
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
        competitor = competitors.CompetitorService(
            PROFILE_DIR, database=service.database
        ).latest()
    finally:
        service.database.close()
    return {
        "topics": topics,
        "blogs": board["blogs"],
        "trending": rows,
        "trending_messages": trend_messages,
        "watchlist": ceo_actions.read_watchlist(PROFILE_DIR),
        "research_queue": ceo_actions.read_research_queue(PROFILE_DIR),
        "analytics": {
            "search": ceo_analytics.cached_report(range_key, device, start=start, end=end),
            "search_console": dashboard_server.gsc_summary(),
            "ga4": analytics_readers.ga4_summary(range_days, device),
            "competitor": competitor,
        },
        "controls": {"range": range_key, "range_days": range_days, "device": device, "start": start, "end": end},
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
            check = ceo_blog_publish.preflight(PROFILE_DIR, task_id)
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
            image = ceo_artifacts.image_for(task, slot, PROFILE_DIR)
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
                elif path == "/ceo/api/blog-retry":
                    # Requeue a write that failed. Not a decision, not an approval,
                    # and refused outright on a card a human put on hold.
                    result = ceo_actions.retry_write(PROFILE_DIR, task_id, email)
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
    except (
        ValueError,
        json.JSONDecodeError,
        TaskFileError,
        ConsoleDBError,
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
