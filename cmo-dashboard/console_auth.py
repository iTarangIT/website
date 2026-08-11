from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from http import HTTPStatus
from typing import Any
from urllib import error, request

CACHE_SECONDS = 60
CACHE_LIMIT = 256
_token_cache: OrderedDict[str, tuple[float, str]] = OrderedDict()
_token_cache_lock = threading.Lock()


def supabase_browser_config() -> dict[str, str]:
    """Read public browser auth configuration at request time."""
    return {
        "url": os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""),
        "anon_key": os.getenv("SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""),
    }


def _write(handler: Any, status: int, message: str) -> None:
    body = json.dumps({"error": message}, separators=(",", ":")).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _supabase_get_user(token: str, url: str, anon_key: str) -> str:
    endpoint = url.rstrip("/") + "/auth/v1/user"
    call = request.Request(
        endpoint,
        headers={"apikey": anon_key, "Authorization": f"Bearer {token}"},
        method="GET",
    )
    try:
        with request.urlopen(call, timeout=5) as response:
            payload = json.loads(response.read())
    except error.HTTPError as exc:
        raise PermissionError("Supabase rejected the bearer token") from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise ConnectionError("Supabase is unreachable") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConnectionError("Supabase returned an unreadable response") from exc
    email = payload.get("email") if isinstance(payload, dict) else None
    if not isinstance(email, str) or not email.strip():
        raise PermissionError("Supabase user response has no email")
    return email.strip()


def _verified_email(token: str, url: str, anon_key: str) -> str:
    key = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = time.monotonic()
    with _token_cache_lock:
        cached = _token_cache.get(key)
        if cached and cached[0] > now:
            _token_cache.move_to_end(key)
            return cached[1]
        if cached:
            del _token_cache[key]
    email = _supabase_get_user(token, url, anon_key)
    with _token_cache_lock:
        _token_cache[key] = (now + CACHE_SECONDS, email)
        _token_cache.move_to_end(key)
        while len(_token_cache) > CACHE_LIMIT:
            _token_cache.popitem(last=False)
    return email


def authorize(handler: Any, required_role: str) -> tuple[str, str] | None:
    """Authorize one exact Supabase account for one console role."""
    header = handler.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        _write(handler, HTTPStatus.UNAUTHORIZED, "bearer token required")
        return None
    token = header[7:]
    if not token or len(token) > 4096 or any(char.isspace() for char in token):
        _write(handler, HTTPStatus.UNAUTHORIZED, "invalid bearer token")
        return None

    config = supabase_browser_config()
    if not config["url"] or not config["anon_key"]:
        _write(handler, HTTPStatus.SERVICE_UNAVAILABLE, "Supabase auth configuration is unavailable")
        return None
    variable = {"ceo": "CMO_CEO_EMAIL", "tech": "CMO_TECH_EMAIL"}.get(required_role)
    if variable is None:
        _write(handler, HTTPStatus.FORBIDDEN, "unknown console role")
        return None
    allowed = os.getenv(variable, "").strip()
    if not allowed:
        _write(handler, HTTPStatus.SERVICE_UNAVAILABLE, f"{required_role} role is not configured")
        return None
    try:
        email = _verified_email(token, config["url"], config["anon_key"])
    except PermissionError:
        _write(handler, HTTPStatus.UNAUTHORIZED, "Supabase rejected the bearer token")
        return None
    except ConnectionError:
        _write(handler, HTTPStatus.BAD_GATEWAY, "Supabase is unreachable")
        return None
    if email.casefold() != allowed.casefold():
        _write(handler, HTTPStatus.FORBIDDEN, "account is not allowed for this console")
        return None
    return email, required_role


def session_identity(handler: Any) -> tuple[str, str] | None:
    """Verify a bearer token and map its email to exactly one server-owned role."""
    header = handler.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        _write(handler, HTTPStatus.UNAUTHORIZED, "bearer token required")
        return None
    token = header[7:]
    if not token or len(token) > 4096 or any(char.isspace() for char in token):
        _write(handler, HTTPStatus.UNAUTHORIZED, "invalid bearer token")
        return None
    config = supabase_browser_config()
    if not config["url"] or not config["anon_key"]:
        _write(handler, HTTPStatus.SERVICE_UNAVAILABLE, "Supabase auth configuration is unavailable")
        return None
    try:
        email = _verified_email(token, config["url"], config["anon_key"])
    except PermissionError:
        _write(handler, HTTPStatus.UNAUTHORIZED, "Supabase rejected the bearer token")
        return None
    except ConnectionError:
        _write(handler, HTTPStatus.BAD_GATEWAY, "Supabase is unreachable")
        return None

    variables = {"ceo": "CMO_CEO_EMAIL", "tech": "CMO_TECH_EMAIL"}
    configured: dict[str, set[str]] = {}
    missing: list[str] = []
    for role, variable in variables.items():
        raw = os.getenv(variable, "").strip()
        if not raw:
            missing.append(variable)
            configured[role] = set()
        else:
            configured[role] = {
                item.strip().casefold() for item in raw.split(",") if item.strip()
            }
    matching = [role for role, addresses in configured.items() if email.casefold() in addresses]
    if len(matching) == 1:
        return email, matching[0]
    if len(matching) > 1:
        _write(handler, HTTPStatus.SERVICE_UNAVAILABLE, "account is assigned to more than one console role")
        return None
    if missing:
        _write(handler, HTTPStatus.SERVICE_UNAVAILABLE, f"console role configuration is unavailable: {', '.join(missing)}")
        return None
    _write(handler, HTTPStatus.FORBIDDEN, "This account does not have a console. Ask Apoorv for access.")
    return None
