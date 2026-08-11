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
import console_auth
import dashboard_server
import analytics_readers
import ceo_artifacts
import ceo_publish
import console_board
from ceo_page import render_page
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


def _bytes(handler: Any, status: int, content_type: str, body: bytes) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
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


def state_payload(range_days: int = 28, device: str = "all") -> dict[str, Any]:
    board = console_board.read_board(TASKS_FILE, PROFILE_DIR)
    trend_days = range_days if range_days in {7, 28, 90} else 7
    rows, trend_messages = analytics_readers.trending_rows(trend_days)
    return {
        "topics": board["topics"],
        "blogs": board["blogs"],
        "trending": rows,
        "trending_messages": trend_messages,
        "watchlist": ceo_actions.read_watchlist(PROFILE_DIR),
        "analytics": {
            "search_console": dashboard_server.gsc_summary(),
            "ga4": analytics_readers.ga4_summary(range_days, device),
        },
        "controls": {"range_days": range_days, "device": device},
    }


def dispatch(handler: Any, method: str) -> bool:
    path = urlparse(handler.path).path
    if not handles(path):
        return False
    if method == "GET" and path in {"/ceo", "/ceo/"}:
        _bytes(handler, HTTPStatus.OK, "text/html; charset=utf-8", render_page())
        return True
    if method == "GET" and path == "/ceo/api/config":
        _json(handler, HTTPStatus.OK, console_auth.supabase_browser_config())
        return True
    auth = _authorized(handler)
    if auth is None:
        return True
    email, _role = auth
    if method == "GET" and path == "/ceo/api/state":
        query = parse_qs(urlparse(handler.path).query)
        try:
            range_days = int(query.get("range", ["28"])[0])
        except ValueError:
            range_days = 28
        if range_days not in {7, 28, 90}:
            range_days = 28
        device = query.get("device", ["all"])[0]
        if device not in {"all", "desktop", "mobile", "tablet"}:
            device = "all"
        _json(handler, HTTPStatus.OK, state_payload(range_days, device))
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
        else:
            payload = _body(handler)
            if path == "/ceo/api/topics":
                result = ceo_actions.add_topics(PROFILE_DIR, payload.get("topics"), email)
            elif path == "/ceo/api/watchlist":
                result = {
                    "ok": True,
                    "watchlist": ceo_actions.update_watchlist(
                        PROFILE_DIR,
                        str(payload.get("keyword", "")),
                        str(payload.get("action", "")),
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
                elif path in {"/ceo/api/topic-greenlight", "/ceo/api/topic-stage"}:
                    stage = "approved" if path.endswith("topic-greenlight") else str(payload.get("stage", ""))
                    ceo_actions.set_topic_stage(PROFILE_DIR, task_id, stage, email)
                    result = {"ok": True, "topic_stage": stage}
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
                    )
                    result = {"ok": stored.recorded}
                else:
                    _json(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return True
    except (ValueError, json.JSONDecodeError, TaskFileError) as exc:
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
