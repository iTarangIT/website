#!/usr/bin/env python3
"""Daily Firecrawl SEO review and backlog updater for itarang_cmo.

The watchdog calls this with --due every cycle. It is deliberately clock-driven:
if the first cycle after 08:00 IST is late, the run is recorded as late rather
than silently skipped. --force bypasses the clock but not the one-attempt-per-day
guard.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

PROFILE = Path("/opt/data/profiles/itarang_cmo")
BOARD = PROFILE / "tasks.md"
TASKS_LOCK = PROFILE / "state/tasks.lock"
LOG = PROFILE / "logs/morning-review.log"
STATE = PROFILE / "state/morning-seo-last-run"
LOCK = PROFILE / "state/morning-seo.lock"
SPEND = PROFILE / "scripts/spend-tracker.py"
IST = ZoneInfo("Asia/Kolkata")

sys.path.insert(0, str(PROFILE))
from cmo_runtime.task_file import TaskFile, TaskFileError, validate_structure  # noqa: E402


def now_ist() -> dt.datetime:
    return dt.datetime.now(IST)


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{dt.datetime.now(dt.timezone.utc).isoformat()} {message}\n")


def load_profile_env() -> None:
    env_file = PROFILE / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key) and key not in os.environ:
            os.environ[key] = value.strip().strip("'\"")


def due(day: str) -> bool:
    if not STATE.exists():
        return True
    raw = STATE.read_text(encoding="utf-8").strip()
    try:
        marker = json.loads(raw)
    except (ValueError, TypeError):
        return raw != day
    return not isinstance(marker, dict) or marker.get("day") != day


def write_daily_marker(day: str, status: str, error: str | None = None) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    marker = {
        "day": day,
        "status": status,
        "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    if error:
        marker["error"] = error
    temporary = STATE.with_name(f".{STATE.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(marker, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(temporary, STATE)


def firecrawl() -> list[dict]:
    key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if not key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set (set it in the profile .env or watchdog environment)")
    base = os.environ.get("FIRECRAWL_API_URL", "https://api.firecrawl.dev").rstrip("/")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "url": "https://itarang.com",
        "limit": 20,
        "scrapeOptions": {"formats": ["markdown", "html"], "onlyMainContent": False},
    }
    task_id = f"morning-seo-{now_ist().date().isoformat()}"
    pages_fetched = 0
    estimated_credits = 0
    status = "failed"
    attempted = False
    try:
        request = Request(f"{base}/v1/crawl", data=json.dumps(payload).encode(), headers=headers, method="POST")
        attempted = True
        with urlopen(request, timeout=60) as response:
            started = json.load(response)
        crawl_id = started.get("id") or started.get("jobId")
        if not crawl_id:
            raise RuntimeError(f"Firecrawl did not return a crawl id: {started}")
        deadline = time.time() + 600
        while time.time() < deadline:
            request = Request(f"{base}/v1/crawl/{crawl_id}", headers=headers)
            with urlopen(request, timeout=60) as response:
                result = json.load(response)
            crawl_status = str(result.get("status", "")).lower()
            data = result.get("data", [])
            if isinstance(data, list):
                pages_fetched = len(data)
            if crawl_status == "completed":
                status = "completed"
                estimated_credits = max(1, pages_fetched)
                return data if isinstance(data, list) else []
            if crawl_status in {"failed", "cancelled", "canceled"}:
                raise RuntimeError(f"Firecrawl crawl {crawl_id} {crawl_status}: {result}")
            time.sleep(10)
        raise TimeoutError(f"Firecrawl crawl {crawl_id} exceeded 10 minutes")
    finally:
        if attempted:
            record_firecrawl(
                task_id=task_id,
                pages_fetched=pages_fetched,
                estimated_credits=max(1, estimated_credits or pages_fetched),
                status=status,
            )


def board_context() -> str:
    return BOARD.read_text(encoding="utf-8") if BOARD.exists() else ""


def spend_line() -> str:
    result = subprocess.run([str(SPEND), "morning"], text=True, capture_output=True, check=True, timeout=30)
    return result.stdout.strip()


def spend_paused() -> bool:
    return subprocess.run([str(SPEND), "paused"], check=False, timeout=30).returncode == 0


def record_external(provider: str, model: str, task_id: str) -> None:
    subprocess.run([str(SPEND), "record", "--provider", provider, "--model", model, "--task-id", task_id, "--cost", "none", "--status", "unknown"], check=False, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def record_firecrawl(*, task_id: str, pages_fetched: int, estimated_credits: int, status: str) -> None:
    subprocess.run(
        [
            str(SPEND), "record",
            "--provider", "firecrawl",
            "--model", "crawl-api",
            "--task-id", task_id,
            "--cost", "none",
            "--status", status,
            "--pages-fetched", str(pages_fetched),
            "--estimated-credits", str(estimated_credits),
            "--credit-day", now_ist().date().isoformat(),
        ],
        check=False,
        timeout=30,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def analyze(pages: list[dict], board: str) -> list[dict]:
    compact = []
    for page in pages:
        compact.append({
            "url": page.get("url"),
            "title": page.get("metadata", {}).get("title"),
            "description": page.get("metadata", {}).get("description"),
            "markdown": (page.get("markdown") or "")[:5000],
            "html": (page.get("html") or "")[:2000],
        })
    prompt = f"""You are the iTarang CMO SEO analyst. Review this Firecrawl crawl of https://itarang.com and propose no more than 5 HIGH-VALUE, non-duplicate backlog tasks. Focus on title/meta/heading/internal-link gaps, page speed/structure, missing pages, and content gaps for India's e-rickshaw and lithium-battery search audience. Use only evidence from the crawl plus reasonable search-intent knowledge. Do not propose publishing or website changes without owner approval.

Return ONLY a JSON array of objects with exactly: title, owner (seo or content), priority (high/medium/low), objective, acceptance_criteria (array of strings). Make each title specific enough for duplicate matching.

Existing board (skip anything represented here, including completed work):
{board[:16000]}

Crawl data:
{json.dumps(compact, ensure_ascii=False)[:50000]}
"""
    usage_file = PROFILE / "state/last-morning-usage.json"
    command = ["/opt/hermes/.venv/bin/hermes", "--profile", "itarang_cmo", "-z", prompt, "--usage-file", str(usage_file)]
    result = subprocess.run(command, text=True, capture_output=True, timeout=600, check=True)
    try:
        usage = json.loads(usage_file.read_text(encoding="utf-8"))
        cost = usage.get("estimated_cost_usd")
        subprocess.run([str(SPEND), "record", "--provider", str(usage.get("provider") or "unknown"), "--model", str(usage.get("model") or "unknown"), "--task-id", str(usage.get("session_id") or "morning-seo"), "--cost", "none" if cost is None else str(cost), "--status", str(usage.get("cost_status") or "estimated")], check=False, timeout=30, stdout=subprocess.DEVNULL)
    except Exception:
        log("SPEND_TRACKING_WARNING usage report unavailable")
    text = result.stdout.strip()
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        raise RuntimeError(f"SEO analyst returned no JSON array: {text[-1000:]}")
    data = json.loads(match.group(0))
    if not isinstance(data, list):
        raise RuntimeError("SEO analyst JSON was not an array")
    return data[:5]


def normalized(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def add_tasks(suggestions: list[dict], board: str, day: str) -> tuple[str, list[dict]]:
    existing = normalized(board)
    selected = []
    for item in suggestions:
        title = str(item.get("title", "")).strip()
        owner = str(item.get("owner", "")).strip().lower()
        if not title or owner not in {"seo", "content"} or normalized(title) in existing:
            continue
        if any(normalized(title) in normalized(x["title"]) or normalized(x["title"]) in normalized(title) for x in selected):
            continue
        selected.append({
            "title": title,
            "owner": owner,
            "priority": str(item.get("priority", "medium")).lower() if str(item.get("priority", "medium")).lower() in {"high", "medium", "low"} else "medium",
            "objective": str(item.get("objective", "")).strip(),
            "acceptance_criteria": [str(x).strip() for x in item.get("acceptance_criteria", []) if str(x).strip()],
        })
    if not selected:
        return board, []
    ids = [int(x) for x in re.findall(r"TASK-(\d+)", board)]
    next_id = max(ids, default=0) + 1
    cards = []
    for item in selected:
        task_id = f"TASK-{next_id:03d}"
        next_id += 1
        criteria = item["acceptance_criteria"] or ["Document the evidence, implementation steps, and validation result."]
        cards.append(f"""### {task_id} — {item['title']}\n\n- ID: {task_id}\n- Title: {item['title']}\n- Owner: {item['owner']}\n- Priority: {item['priority']}\n- Status: Backlog\n- Start date: not started\n- Completed date: not completed\n- Objective: {item['objective']}\n- Acceptance criteria:\n""" + "".join(f"  - {c}\n" for c in criteria) + "- Latest summary: Added by the daily Firecrawl SEO review; awaiting dispatch.\n")
        item["id"] = task_id
    block = "\n".join(cards)
    marker = "## Backlog\n"
    pos = board.find(marker)
    if pos < 0:
        raise RuntimeError("tasks.md has no Backlog section")
    insert_at = pos + len(marker)
    if board[insert_at:].lstrip().startswith("_No tasks._"):
        end = insert_at + len(board[insert_at:]) - len(board[insert_at:].lstrip()) + len("_No tasks._")
        board = board[:insert_at] + "\n" + block + board[end:]
    else:
        board = board[:insert_at] + "\n" + block + board[insert_at:]
    return board, selected


def commit_tasks(suggestions: list[dict], day: str) -> list[dict]:
    """Re-read, mutate, validate, and atomically replace the board under its shared lock."""
    TASKS_LOCK.parent.mkdir(parents=True, exist_ok=True)
    TASKS_LOCK.touch(exist_ok=True)
    task_file = TaskFile(BOARD, lock_path=TASKS_LOCK)
    with TASKS_LOCK.open("r+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        original = BOARD.read_text(encoding="utf-8")
        candidate, added = add_tasks(suggestions, original, day)
        if not added:
            return []
        issues = task_file._validate_candidate(candidate)
        if issues:
            detail = "; ".join(issue.message for issue in issues)
            raise TaskFileError(f"morning SEO update would make tasks.md invalid: {detail}")
        task_file._atomic_write(candidate)
        if BOARD.read_text(encoding="utf-8") != candidate or validate_structure(BOARD):
            task_file._atomic_write(original)
            raise TaskFileError("morning SEO update verification failed; original tasks.md restored")
        return added


def post(summary: str) -> None:
    log(f"LOG_ONLY notification={json.dumps(summary, ensure_ascii=False)}")


def run(force: bool = False) -> int:
    load_profile_env()
    current = now_ist()
    day = current.date().isoformat()
    if not force and (current.hour, current.minute) < (8, 0):
        return 0
    if not due(day):
        return 0
    write_daily_marker(day, "attempted")
    scheduled = current.replace(hour=8, minute=0, second=0, microsecond=0)
    log(f"START scheduled={scheduled.isoformat()} fired={current.isoformat()} late_seconds={max(0, int((current-scheduled).total_seconds()))}")
    try:
        if spend_paused():
            message = f"Morning SEO review ({day} IST) paused: API spend budget is at or above $50.\n{spend_line()}"
            post(message)
            log("PAUSED reason=monthly_spend_budget")
            write_daily_marker(day, "paused")
            return 0
        pages = firecrawl()
        board = board_context()
        suggestions = analyze(pages, board)
        added = commit_tasks(suggestions, day)
        lines = [f"Morning SEO review ({day} IST): {len(added)} task(s) added to Backlog.", spend_line()]
        lines.extend(f"- {x['id']}: {x['title']} [{x['owner']}, {x['priority']}]" for x in added)
        if not added:
            lines.append("- no new issues found")
        message = "\n".join(lines)
        if current.weekday() == 0:
            weekly = subprocess.run([str(SPEND), "weekly"], text=True, capture_output=True, check=False, timeout=60)
            if weekly.stdout.strip():
                message += "\n" + weekly.stdout.strip()
        post(message)
        write_daily_marker(day, "success")
        log(f"SUCCESS pages={len(pages)} tasks_added={len(added)} delivery=log-only")
        print(message)
        return 0
    except Exception as exc:
        write_daily_marker(day, "failed", f"{type(exc).__name__}: {exc}")
        failure_message = f"Morning SEO review ({day} IST) could not run: {type(exc).__name__}: {exc}"
        try:
            post(failure_message)
            log(f"FAILED error={type(exc).__name__}: {exc} failure_log=written")
        except Exception as log_exc:
            log(f"FAILED error={type(exc).__name__}: {exc} failure_log=failed:{type(log_exc).__name__}")
        print(f"Morning SEO job failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--due", action="store_true", help="run only at/after 08:00 IST and once per day")
    parser.add_argument("--force", action="store_true", help="run before 08:00 for an operator test; still limited to one attempt per day")
    args = parser.parse_args()
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return run(force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
