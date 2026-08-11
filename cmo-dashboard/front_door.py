from __future__ import annotations

import datetime as dt
import json
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import console_auth
from front_door_page import page_bytes

PROFILE_DIR = Path(__file__).resolve().parent.parent
LOGIN_LOG = PROFILE_DIR / "logs" / "console-auth.log"


def handles(path: str) -> bool:
    return urlparse(path).path in {"/", "/api/session"}


def _send(handler: Any, status: int, content_type: str, body: bytes) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _page() -> bytes:
    return page_bytes()


def _record_login(email: str, role: str) -> None:
    LOGIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "email": email,
        "role": role,
    }
    with LOGIN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def dispatch(handler: Any, method: str) -> bool:
    path = urlparse(handler.path).path
    if not handles(path):
        return False
    if method != "GET":
        body = json.dumps({"error": "method not allowed"}, separators=(",", ":")).encode("utf-8")
        _send(handler, HTTPStatus.METHOD_NOT_ALLOWED, "application/json; charset=utf-8", body)
        return True
    if path == "/":
        _send(handler, HTTPStatus.OK, "text/html; charset=utf-8", _page())
        return True
    identity = console_auth.session_identity(handler)
    if identity is None:
        return True
    email, role = identity
    _record_login(email, role)
    payload = json.dumps(
        {"email": email, "role": role, "console": f"/{role}"},
        separators=(",", ":"),
    ).encode("utf-8")
    _send(handler, HTTPStatus.OK, "application/json; charset=utf-8", payload)
    return True
