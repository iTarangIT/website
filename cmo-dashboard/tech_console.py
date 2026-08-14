from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import analytics_readers
import dashboard_server
import console_auth
import console_board
from cmo_runtime.decisions import DecisionConflict, DecisionError, DecisionStore
from tech_page import render_page

PROFILE_DIR = dashboard_server.PROFILE_DIR
CMO_SKILLS_DIR: Path | None = None
SPEND_LOG = PROFILE_DIR / "logs" / "spend.log"
APPROVAL_LOG = PROFILE_DIR / "logs" / "approvals.log"
LOGIN_LOG = PROFILE_DIR / "logs" / "console-auth.log"
ELEVENLABS_LOG = PROFILE_DIR / "logs" / "elevenlabs-usage.jsonl"
DATABASE_HEALTH = PROFILE_DIR / "state" / "database-health.json"
CALLING_USAGE = PROFILE_DIR / "logs" / "calling-usage.jsonl"
CRM_USAGE = PROFILE_DIR / "logs" / "crm-usage.jsonl"
LOG_NAMES = frozenset({"hourly-cycle.log", "morning-review.log"})
LANE_NAMES = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")


def handles(path: str) -> bool:
    route = urlparse(path).path
    return route == "/tech" or route.startswith("/tech/")


def _send(handler: Any, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _shell(handler: Any) -> None:
    body = render_page()
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _payload(handler: Any) -> dict[str, Any]:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError as exc:
        raise ValueError("invalid content length") from exc
    if length < 1 or length > 65536:
        raise ValueError("invalid request size")
    value = json.loads(handler.rfile.read(length))
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def _read_json_lines(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _direct_rupee(row: dict[str, Any]) -> float | int | None:
    for key in ("rupee_cost", "cost_inr", "actual_cost_inr"):
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
    return None


def spend_state() -> dict[str, Any]:
    ledger = _read_json_lines(SPEND_LOG)
    today = dt.datetime.now(dt.timezone.utc).date()
    normalized = []
    run_rows = []
    providers: dict[str, dict[str, int]] = defaultdict(lambda: {"calls": 0, "unmeasured": 0})
    daily_rupees = 0.0
    today_unmeasured = 0
    firecrawl_today: list[int | float] = []
    firecrawl_month: list[int | float] = []
    firecrawl_today_unmeasured = 0
    firecrawl_month_unmeasured = 0
    for row in ledger:
        cost = _direct_rupee(row)
        stamp = str(row.get("date") or row.get("timestamp") or "")
        try:
            row_date = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()
        except ValueError:
            row_date = None
        provider_name = row.get("provider")
        normalized.append({
            "date": stamp or None,
            "run_type": row.get("run_type"),
            "skill": row.get("skill", row.get("skill_used", row.get("skill_loaded"))),
            "tokens": row.get("tokens", row.get("approximate_tokens")),
            "rupee_cost": cost,
            "provider": provider_name,
            "task_id": row.get("task_id"),
        })
        is_call = row.get("record_type") == "call" or (
            not row.get("record_type") and provider_name is not None
        )
        if is_call:
            provider = str(row.get("provider") or "unknown")
            providers[provider]["calls"] += 1
            if cost is None:
                providers[provider]["unmeasured"] += 1
            if provider.casefold() == "firecrawl":
                measured_credits = next(
                    (
                        row.get(key)
                        for key in ("credits_consumed", "firecrawl_credits", "actual_credits")
                        if isinstance(row.get(key), (int, float)) and not isinstance(row.get(key), bool)
                    ),
                    None,
                )
                in_month = bool(row_date and row_date.year == today.year and row_date.month == today.month)
                if row_date == today:
                    if measured_credits is None:
                        firecrawl_today_unmeasured += 1
                    else:
                        firecrawl_today.append(measured_credits)
                if in_month:
                    if measured_credits is None:
                        firecrawl_month_unmeasured += 1
                    else:
                        firecrawl_month.append(measured_credits)
        if row.get("record_type") == "run" or row.get("run_type"):
            if row_date == today:
                if cost is None:
                    today_unmeasured += 1
                else:
                    daily_rupees += float(cost)
            run_rows.append({
                "date": stamp or None,
                "run_type": row.get("run_type"),
                "skill": row.get("skill", row.get("skill_used", row.get("skill_loaded"))),
                "tokens": row.get("tokens", row.get("approximate_tokens")),
                "rupee_cost": cost,
                "provider": row.get("provider"),
                "task_id": row.get("task_id"),
            })

    firecrawl_today_value = sum(firecrawl_today) if firecrawl_today and not firecrawl_today_unmeasured else None
    firecrawl_month_value = sum(firecrawl_month) if firecrawl_month and not firecrawl_month_unmeasured else None
    if daily_rupees > 300:
        daily_halt_state = "HALT"
    elif today_unmeasured:
        daily_halt_state = "unmeasured"
    else:
        daily_halt_state = "clear"

    return {
        "rows": normalized,
        "runs": run_rows,
        "providers": dict(providers),
        "unmeasured": sum(1 for row in normalized if row["rupee_cost"] is None),
        "firecrawl": {
            "today": firecrawl_today_value,
            "month": firecrawl_month_value,
            "free_tier": 1000,
            "today_detail": (
                f"{firecrawl_today_unmeasured} Firecrawl call(s) lack measured credit usage"
                if firecrawl_today_unmeasured else "Measured credit fields from logs/spend.log"
            ),
            "month_detail": (
                f"{firecrawl_month_unmeasured} Firecrawl call(s) lack measured credit usage"
                if firecrawl_month_unmeasured else "Measured credit fields from logs/spend.log"
            ),
        },
        "daily_rupees": daily_rupees,
        "daily_halt": daily_rupees > 300,
        "daily_halt_state": daily_halt_state,
        "today_unmeasured": today_unmeasured,
    }


def _process_state() -> dict[str, Any]:
    gateway_pids = []
    proc = Path("/proc")
    if proc.is_dir():
        for candidate in proc.iterdir():
            if not candidate.name.isdigit():
                continue
            try:
                command = (candidate / "cmdline").read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
            except OSError:
                continue
            if "hermes" in command.casefold() and "gateway" in command.casefold():
                gateway_pids.append(int(candidate.name))
    return {
        "gateway": {"state": "running" if gateway_pids else "not observed", "pids": gateway_pids},
        "dashboard": {"state": "running", "pid": os.getpid()},
    }


def _skills() -> list[dict[str, Any]]:
    skills_dir = CMO_SKILLS_DIR or (PROFILE_DIR / "cmo_skills")
    skills: list[dict[str, Any]] = []
    for name in ("seo", "content", "social", "ads", "ops"):
        path = skills_dir / f"{name}.skill"
        text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        reason = None
        kpi_line = next((line for line in text.splitlines() if line.startswith("KPIS:")), "")
        if not path.is_file():
            reason = "CMO skill file not present"
        elif name == "ops" and "skill disabled" in text.casefold():
            reason = "disabled: objective and KPI set are not defined"
        elif name == "ads" and "draft-only" in text.casefold():
            reason = "draft-only: no approved paid budget and ceiling"
        elif name in {"seo", "content", "social"} and not kpi_line.removeprefix("KPIS:").strip():
            reason = "disabled: human-approved KPI set is not recorded"
        skills.append({
            "name": name,
            "files": [str(path.relative_to(PROFILE_DIR))] if path.is_file() else [],
            "disabled_reason": reason,
        })
    return skills


def runtime_state(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    process = _process_state()
    in_progress = next((task for task in tasks if task.get("section") == "In Progress"), None)
    spend_rows = _read_json_lines(SPEND_LOG)
    last_runs: dict[str, Any] = {"plan": None, "execute": None, "review": None}
    for row in spend_rows:
        if row.get("record_type") != "run":
            continue
        run_type = str(row.get("run_type") or "").casefold()
        if run_type in last_runs:
            last_runs[run_type] = {
                "timestamp": row.get("date", row.get("timestamp")),
                "skill": row.get("skill", row.get("skill_used", row.get("skill_loaded"))),
                "tokens": row.get("tokens", row.get("approximate_tokens")),
                "status": row.get("status"),
                "source": "logs/spend.log",
            }
    return {
        "current_run_type": (in_progress.get("run_type") or "execute") if in_progress else None,
        "in_progress_task": in_progress.get("id") if in_progress else None,
        "last_runs": last_runs,
        "skills": _skills(),
        **process,
    }


def _source_tile(
    name: str,
    path: Path,
    *,
    meaning: str,
    key: str | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        return {
            "name": name,
            "value": "no source connected",
            "detail": f"Missing source: {path.name}",
            "meaning": meaning,
            "source_connected": False,
        }
    rows = _read_json_lines(path)
    if key is None:
        return {
            "name": name,
            "value": str(len(rows)),
            "detail": f"Read from {path.name}; unit: recorded events",
            "meaning": meaning,
            "source_connected": True,
        }
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return {
            "name": name,
            "value": "no source connected",
            "detail": f"Missing measured source field: {path.name}:{key}",
            "meaning": meaning,
            "source_connected": False,
        }
    return {
        "name": name,
        "value": str(sum(values)),
        "detail": f"Read from {path.name}; unit: {key}",
        "meaning": meaning,
        "source_connected": True,
    }


def infrastructure_state(spend: dict[str, Any]) -> list[dict[str, Any]]:
    tiles = [
        _source_tile(
            "Number of logins", LOGIN_LOG,
            meaning="Successful console login events recorded by the authentication audit log.",
        ),
        _source_tile(
            "ElevenLabs usage", ELEVENLABS_LOG, key="characters",
            meaning="Characters submitted to ElevenLabs text-to-speech.",
        ),
    ]
    measured = [row["rupee_cost"] for row in spend["rows"] if row["rupee_cost"] is not None]
    tiles.append({
        "name": "Tech spend",
        "value": str(sum(measured)) if measured else "no source connected",
        "detail": "Rupee cost fields read from spend.log" if measured else "Missing measured source field: spend.log:rupee_cost",
        "meaning": "Measured rupee cost across technical ledger records.",
        "source_connected": bool(measured),
    })
    if DATABASE_HEALTH.is_file():
        try:
            value = json.loads(DATABASE_HEALTH.read_text(encoding="utf-8"))
            status = str(value.get("status", "")) if isinstance(value, dict) else ""
            if status:
                detail = "Read from database-health.json; unit: health status"
                connected = True
            else:
                status = "no source connected"
                detail = "Missing measured source field: database-health.json:status"
                connected = False
        except json.JSONDecodeError:
            status, detail, connected = "no source connected", "Invalid source: database-health.json", False
        tiles.append({
            "name": "Database health", "value": status, "detail": detail,
            "meaning": "Latest observed health status from the configured database probe.",
            "source_connected": connected,
        })
    else:
        tiles.append({
            "name": "Database health", "value": "no source connected",
            "detail": "Missing source: database-health.json",
            "meaning": "Latest observed health status from the configured database probe.",
            "source_connected": False,
        })
    tiles.extend([
        _source_tile(
            "Calling volume", CALLING_USAGE, key="calls",
            meaning="Completed calling operations recorded by the calling ledger.",
        ),
        _source_tile(
            "CRM usage", CRM_USAGE, key="operations",
            meaning="CRM operations recorded by a CRM usage ledger; CRM integration remains out of scope.",
        ),
    ])
    return tiles


def _approval_threads() -> dict[str, list[dict[str, Any]]]:
    threads: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in _read_json_lines(APPROVAL_LOG):
        task_id = str(event.get("task_id") or "")
        if task_id:
            threads[task_id].append(event)
    return threads


def state_payload() -> dict[str, Any]:
    tasks = console_board.read_board(PROFILE_DIR / "tasks.md", PROFILE_DIR)["tasks"]
    threads = _approval_threads()
    for task in tasks:
        task["approval_thread"] = threads.get(task["id"], [])
    board = {lane: [] for lane in LANE_NAMES}
    for task in tasks:
        board.setdefault(task.get("section", "Backlog"), []).append(task)
    spend = spend_state()
    return {
        "tasks": tasks,
        "board": board,
        "runtime": runtime_state(tasks),
        "spend": spend,
        "infrastructure": infrastructure_state(spend),
        "analytics": {
            "search_console": dashboard_server.gsc_summary(),
            "ga4": analytics_readers.ga4_technical_summary(),
        },
    }


def _validate() -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-m", "cmo_runtime.task_file", "--file", "tasks.md", "validate"],
        cwd=PROFILE_DIR, capture_output=True, text=True, timeout=30, check=False,
    )
    output = result.stdout.strip()
    try:
        parsed = json.loads(output) if output else []
        issues = parsed if isinstance(parsed, list) else [parsed]
    except json.JSONDecodeError:
        issues = [line for line in result.stdout.splitlines() if line.strip()]
    return {"exit_code": result.returncode, "issues": issues, "stderr": result.stderr.strip()}


def dispatch(handler: Any, method: str) -> bool:
    route = urlparse(handler.path)
    path = route.path
    if not handles(path):
        return False
    if method == "GET" and path in {"/tech", "/tech/"}:
        _shell(handler)
        return True
    if method == "GET" and path == "/tech/api/config":
        _send(handler, HTTPStatus.OK, console_auth.supabase_browser_config())
        return True
    identity = console_auth.authorize(handler, "tech")
    if identity is None:
        return True
    if method == "GET" and path == "/tech/api/state":
        _send(handler, HTTPStatus.OK, state_payload())
        return True
    if method == "GET" and path == "/tech/api/logs":
        name = parse_qs(route.query).get("name", [""])[0]
        if name not in LOG_NAMES:
            _send(handler, HTTPStatus.BAD_REQUEST, {"error": "unknown log"})
            return True
        log_path = PROFILE_DIR / "logs" / name
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-50:] if log_path.is_file() else []
        _send(handler, HTTPStatus.OK, {"name": name, "lines": lines})
        return True
    if method == "POST" and path in {"/tech/api/decision", "/tech/api/validate"} and os.getenv("CMO_DASHBOARD_PREVIEW") == "1":
        _send(handler, HTTPStatus.FORBIDDEN, {"error": "writes disabled in preview mode"})
        return True
    if method == "POST" and path == "/tech/api/validate":
        _send(handler, HTTPStatus.OK, _validate())
        return True
    if method == "POST" and path == "/tech/api/decision":
        try:
            body = _payload(handler)
            if body.get("decision") != "approve":
                raise ValueError("technical console accepts approve only")
            task_id = str(body.get("task_id", ""))
            board = console_board.read_board(PROFILE_DIR / "tasks.md", PROFILE_DIR)
            task = next((item for item in board["tasks"] if item["id"] == task_id), None)
            if task is None:
                raise ValueError("unknown task")
            commit = task.get("change_commit") or task.get("commit")
            result = DecisionStore(PROFILE_DIR).decide(
                task_id, "approve", surface="dashboard", approver_id=identity[0],
                card_commit=commit, current_commit=commit,
            )
            _send(handler, HTTPStatus.OK, {"status": result.status, "task_id": task_id})
        except ValueError as exc:
            _send(handler, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except DecisionConflict as exc:
            _send(handler, HTTPStatus.CONFLICT, {"error": str(exc)})
        except DecisionError as exc:
            _send(handler, HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
        return True
    _send(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})
    return True
