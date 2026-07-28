#!/usr/bin/env python3
"""Run one owner-facing Kanban orchestration cycle.

The cmo-watchdog invokes this script every 60 minutes.  State used to avoid
redispatching a busy owner and to record explicit human approvals lives under
state/, never in the board's task-card fields.
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from preview_metrics import (  # noqa: E402
    METRICS_DIR,
    capture_metrics,
    compare,
    live_url,
    weekly_summary,
)

PROFILE = Path(os.environ.get("CMO_DASHBOARD_PROFILE_DIR", "/opt/data/profiles/itarang_cmo"))
BOARD = PROFILE / "tasks.md"
LOG = PROFILE / "logs/hourly-cycle.log"
STATE_DIR = PROFILE / "state"
ACTIVE = STATE_DIR / "hourly-active.json"
APPROVALS = STATE_DIR / "human-approvals.json"
LOCK = STATE_DIR / "tasks.lock"
TMUX = PROFILE / "bin/tmux"
TARGET = os.environ.get("CMO_DISCORD_TARGET", "discord:1526833186657796153")
ROLES = {"social", "seo", "ads", "content", "ops"}
STATUSES = {"Backlog", "In Progress", "CMO Review", "Human Approval", "Completed"}


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def stamp(value: dt.datetime | None = None) -> str:
    return (value or now()).isoformat()


def log(message: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp()} {message}\n")


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def parse_tasks(text: str) -> list[dict]:
    sections = list(re.finditer(r"(?m)^## (.+?)\s*$", text))
    tasks: list[dict] = []
    for index, section in enumerate(sections):
        section_name = section.group(1).strip()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        body = text[section.end():end]
        matches = list(re.finditer(r"(?m)^### (TASK-[0-9]+) — (.+?)\s*$", body))
        for task_index, match in enumerate(matches):
            card_end = matches[task_index + 1].start() if task_index + 1 < len(matches) else len(body)
            card = body[match.start():card_end]
            fields = {}
            for field in ("Title", "Owner", "Priority", "Status", "Start date", "Completed date", "Objective", "Latest summary", "Last updated", "Human decision", "Human decision by", "Human decision at", "Human decision comment", "Change type", "Affected pages", "SEO elements", "Change commit", "Agent summary 1", "Agent summary 2", "Agent summary 3"):
                found = re.search(rf"(?m)^- {re.escape(field)}:\s*(.*?)\s*$", card)
                if found:
                    fields[field] = found.group(1).strip()
            tasks.append({"id": match.group(1), "title": match.group(2).strip(), "section": section_name,
                          "start": section.end() + match.start(), "end": section.end() + card_end,
                          "card": card, "fields": fields})
    return tasks


def card_for(text: str, task: dict) -> str:
    return text[task["start"]:task["end"]]


def replace_card(text: str, task: dict, card: str) -> str:
    return text[:task["start"]] + card + text[task["end"]:]


def field(card: str, name: str, value: str) -> str:
    pattern = rf"(?m)^- {re.escape(name)}:\s*.*?$"
    line = f"- {name}: {value}"
    if re.search(pattern, card):
        return re.sub(pattern, line, card, count=1)
    return card.rstrip() + "\n" + line + "\n"


def move_card(text: str, task: dict, destination: str, summary: str | None = None) -> str:
    card = task["card"]
    card = field(card, "Status", destination)
    if destination == "In Progress" and task["fields"].get("Start date") in {None, "", "not started"}:
        card = field(card, "Start date", now().date().isoformat())
    if destination == "Completed":
        card = field(card, "Completed date", now().date().isoformat())
    if summary is not None:
        card = field(card, "Latest summary", summary)
    card = field(card, "Last updated", stamp())
    card = card.strip() + "\n\n"
    source_start = task["start"]
    source_end = task["end"]
    text = text[:source_start] + text[source_end:]
    marker = f"## {destination}\n"
    insert = text.find(marker)
    if insert < 0:
        raise RuntimeError(f"tasks.md has no {destination} section")
    insert += len(marker)
    rest = text[insert:]
    if rest.lstrip().startswith("_No tasks._"):
        leading = len(rest) - len(rest.lstrip())
        empty_end = insert + leading + len("_No tasks._")
        text = text[:insert] + "\n" + card + text[empty_end:]
    else:
        text = text[:insert] + "\n" + card + text[insert:]
    return text


def update_in_place(text: str, task: dict, status: str | None = None, summary: str | None = None) -> str:
    card = task["card"]
    if status:
        card = field(card, "Status", status)
    if summary is not None:
        card = field(card, "Latest summary", summary)
    card = field(card, "Last updated", stamp())
    return replace_card(text, task, card)


def board_timestamp(text: str) -> str:
    line = f"Last cycle ran: {stamp()}"
    if re.search(r"(?m)^Last cycle ran:.*$", text):
        return re.sub(r"(?m)^Last cycle ran:.*$", line, text, count=1)
    marker = "Last updated:"
    match = re.search(r"(?m)^Last updated:.*$", text)
    if match:
        return text[:match.end()] + "\n" + line + text[match.end():]
    return text.rstrip() + "\n\n" + line + "\n"


def owner_free(owner: str, active: dict) -> bool:
    return owner in ROLES and owner not in {item.get("owner") for item in active.values()}


def dispatch(task: dict) -> str:
    owner = task["fields"].get("Owner", "").lower()
    unique = now().strftime("%Y%m%dT%H%M%S")
    prompt_path = PROFILE / "dispatch" / owner / f"{task['id']}.hourly-{unique}.prompt"
    criteria = re.findall(r"(?m)^  - (.+)$", task["card"])
    website_instruction = ""
    if is_website_change(task):
        website_instruction = (
            "This is an authorized branch-only website implementation. Baseline evidence has already been captured. "
            "Implement on cmo-changes, commit and push that branch, but never merge or publish main. "
            "Your final line must be compact JSON exactly shaped as "
            "{\"commit\":\"<hash>\",\"look\":[\"<line 1>\",\"<line 2>\",\"<line 3>\"]}. "
            "The three lines must tell a business reviewer exactly what to inspect visually.\n"
        )
    prompt = (f"You are the {owner} specialist dispatched by itarang_cmo.\n\n"
              f"Task ID: {task['id']}\nTask title: {task['title']}\n"
              f"Objective: {task['fields'].get('Objective', '')}\n"
              f"Acceptance criteria:\n" + "\n".join(f"- {item}" for item in criteria) + "\n\n"
              + website_instruction +
              "Do not publish, spend money, contact customers, or make other external changes without explicit human approval. "
              "For a review-only task, produce the requested concise deliverable and update tasks.md to CMO Review with one concise Latest summary. "
              "For a human-approved implementation task, implement only the approved action, work on branch cmo-changes, push it, and return the resulting commit hash. "
              + ("Return the required compact JSON as the final line." if is_website_change(task) else "Return only one concise summary sentence."))
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(prompt, encoding="utf-8")
    subprocess.run([str(TMUX), "send-keys", "-t", f"cmo-{owner}", f"run {prompt_path}", "Enter"], check=True, timeout=30)
    return str(prompt_path)


def result_ready(task_id: str, owner: str, dispatched_at: str) -> str | None:
    threshold = dt.datetime.fromisoformat(dispatched_at).timestamp()
    candidates = [
        PROFILE / "results" / owner / f"{task_id}.hourly.summary",
        PROFILE / "results" / owner / f"{task_id}.dashboard-approval.summary",
        PROFILE / "results" / owner / f"{task_id}.summary",
    ]
    fresh = [path for path in candidates if path.exists() and path.stat().st_mtime > threshold]
    if not fresh:
        return None
    result = max(fresh, key=lambda path: path.stat().st_mtime)
    value = result.read_text(encoding="utf-8").strip()
    return value or None


def explicit_approval(task_id: str, data: dict) -> bool:
    value = data.get(task_id)
    if isinstance(value, dict):
        return bool(value.get("approved"))
    return value is True or value == "approved"


def human_approved(task: dict, approvals: dict) -> bool:
    decision = task["fields"].get("Human decision", "").lower()
    return decision == "approve" or explicit_approval(task["id"], approvals)


def safe_review(task: dict) -> bool:
    card = task["card"].lower()
    no_publication = "do not publish" in card or "publishing actions" in card or "do not make" in card and "publishing" in card
    no_external = "external" in card and ("no " in card or "do not " in card)
    no_website = "website" in card and ("no " in card or "do not " in card)
    return no_publication and no_external and no_website


def commit_hash(summary: str) -> str | None:
    match = re.search(r"\b[0-9a-f]{7,40}\b", summary.lower())
    return match.group(0) if match else None


def is_website_change(task: dict) -> bool:
    return task.get("fields", {}).get("Change type", "").strip().lower() == "website"


def parse_implementation_result(summary: str) -> dict:
    try:
        value = json.loads(summary)
    except json.JSONDecodeError as exc:
        raise ValueError("implementation result must be compact JSON") from exc
    commit = str(value.get("commit", "")).lower()
    look = value.get("look")
    if not re.fullmatch(r"[0-9a-f]{7,40}", commit):
        raise ValueError("implementation result needs a commit hash")
    if not isinstance(look, list) or len(look) != 3 or any(not str(item).strip() for item in look):
        raise ValueError("implementation result needs exactly three review lines")
    return {"commit": commit, "look": [str(item).strip() for item in look]}


def metric_summary(rows: list[dict]) -> str:
    def delta(value):
        return f"+{value}" if isinstance(value, (int, float)) and value > 0 else str(value)
    return "; ".join(
        f"{row['metric']}: {row['before']} → {row['after']} ({delta(row['delta'])})" for row in rows
    )


def merged_into_main(commit: str) -> bool:
    repo = os.environ.get("CMO_DASHBOARD_GIT_REPO", str(Path(__file__).resolve().parents[2]))
    subprocess.run(["git", "-C", repo, "fetch", "origin", "main"], check=False, timeout=90,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", commit, "origin/main"],
                            check=False, timeout=10)
    return result.returncode == 0


def metric_table(rows: list[dict]) -> str:
    lines = ["Metric | Before | After | Delta"]
    for row in rows:
        lines.append(f"{row['metric']} | {row['before']} | {row['after']} | {row['delta']}")
    return "\n".join(lines)


def add_card_fields(text: str, task: dict, updates: dict[str, str]) -> str:
    card = task["card"]
    for name, value in updates.items():
        card = field(card, name, value)
    return replace_card(text, task, card)


def post_changes(changes: list[str]) -> None:
    if not changes:
        return
    message = "\n".join(changes)
    subprocess.run(["/opt/hermes/.venv/bin/hermes", "--profile", "itarang_cmo", "send", "--to", TARGET, message, "--quiet"], check=True, timeout=60)


def run_cycle() -> int:
    text = BOARD.read_text(encoding="utf-8")
    active = load_json(ACTIVE, {})
    approvals = load_json(APPROVALS, {})
    changes: list[str] = []

    # First accept completed worker handoffs into CMO Review.
    for task_id, item in list(active.items()):
        if item.get("preapproval_implementation"):
            ready = result_ready(task_id, item["owner"], item["dispatched_at"])
            if not ready:
                continue
            task = next((x for x in parse_tasks(text) if x["id"] == task_id), None)
            try:
                result = parse_implementation_result(ready)
            except ValueError as exc:
                if task:
                    text = update_in_place(text, task, status="In Progress", summary=f"Website handoff invalid: {exc}; retry required.")
                changes.append(f"{task_id}: website handoff invalid; retained for retry")
                active.pop(task_id, None)
                continue
            if task:
                text = add_card_fields(text, task, {
                    "Branch": "cmo-changes",
                    "Change commit": result["commit"],
                    "Agent summary 1": result["look"][0],
                    "Agent summary 2": result["look"][1],
                    "Agent summary 3": result["look"][2],
                })
                task = next(x for x in parse_tasks(text) if x["id"] == task_id)
                text = move_card(text, task, "CMO Review", "Website implementation committed on cmo-changes; ready for Gate 1 review.")
                changes.append(f"{task_id}: website implemented on cmo-changes; moved to CMO Review")
            active.pop(task_id, None)
            continue
        if item.get("implementation") or item.get("awaiting_merge"):
            continue
        ready = result_ready(task_id, item["owner"], item["dispatched_at"])
        if not ready:
            continue
        task = next((x for x in parse_tasks(text) if x["id"] == task_id), None)
        if task:
            if ready.startswith("Worker failed"):
                text = update_in_place(text, task, status="In Progress", summary=f"Worker failed; retry required: {ready[-500:]}")
                changes.append(f"{task_id}: worker failed; retained in In Progress for retry")
            else:
                text = move_card(text, task, "CMO Review", ready)
                changes.append(f"{task_id}: worker returned result; moved to CMO Review")
        active.pop(task_id, None)

    # Dispatch one or more backlog cards to currently free specialist sessions.
    # Reparse after every move: card offsets become stale when an earlier card
    # is removed from the same section.
    while True:
        task = next((x for x in parse_tasks(text)
                     if x["section"] == "Backlog" and x["fields"].get("Status") == "Backlog"
                     and owner_free(x["fields"].get("Owner", "").lower(), active)), None)
        if not task:
            break
        owner = task["fields"].get("Owner", "").lower()
        if is_website_change(task):
            try:
                baseline = capture_metrics(task, "baseline")
            except Exception as exc:
                changes.append(f"{task['id']}: baseline metrics failed; website implementation not dispatched")
                log(f"BASELINE_FAILED task={task['id']} error={type(exc).__name__}: {exc}")
                break
            if baseline.get("status") != "captured":
                changes.append(f"{task['id']}: baseline metrics unavailable; website implementation not dispatched")
                break
        prompt_path = dispatch(task)
        dispatched_at = stamp()
        text = move_card(text, task, "In Progress")
        active[task["id"]] = {"owner": owner, "dispatched_at": dispatched_at, "prompt": prompt_path,
                              "preapproval_implementation": is_website_change(task)}
        changes.append(f"{task['id']}: dispatched to {owner}; moved Backlog → In Progress")

    # Review every card that was in CMO Review at the start or arrived above.
    while True:
        task = next((x for x in parse_tasks(text)
                     if x["section"] == "CMO Review" and x["fields"].get("Status") == "CMO Review"), None)
        if not task:
            break
        summary = task["fields"].get("Latest summary", "")
        if is_website_change(task):
            required = [task["fields"].get("Change commit", "")] + [task["fields"].get(f"Agent summary {n}", "") for n in (1, 2, 3)]
            if any(not value for value in required):
                text = move_card(text, task, "In Progress", "Website review packet is incomplete; commit and three visual review lines are required.")
                changes.append(f"{task['id']}: incomplete website review packet returned to agent")
            else:
                text = move_card(text, task, "Human Approval", "Website change is implemented on cmo-changes; Gate 1 visual-preview approval required.")
                changes.append(f"{task['id']}: website change escalated CMO Review → Human Approval")
        elif safe_review(task) and summary and "awaiting dispatch" not in summary.lower():
            text = move_card(text, task, "Completed", f"CMO approved safe review work: {summary}")
            changes.append(f"{task['id']}: CMO review approved safe work; moved CMO Review → Completed")
        elif human_approved(task, approvals):
            owner = task["fields"].get("Owner", "").lower()
            if owner_free(owner, active):
                prompt_path = dispatch(task)
                text = move_card(text, task, "In Progress", "Human approval recorded; implementation dispatched.")
                active[task["id"]] = {"owner": owner, "dispatched_at": stamp(), "prompt": prompt_path, "implementation": True}
                changes.append(f"{task['id']}: human approval recorded; implementation dispatched to {owner}")
            else:
                break
        else:
            text = move_card(text, task, "Human Approval", "CMO review complete; exact action requires human approval.")
            changes.append(f"{task['id']}: escalated CMO Review → Human Approval")

    # Legacy/non-website approvals retain their existing implementation handoff.
    for task_id, item in list(active.items()):
        if not item.get("implementation"):
            continue
        ready = result_ready(task_id, item["owner"], item["dispatched_at"])
        if not ready:
            continue
        task = next((x for x in parse_tasks(text) if x["id"] == task_id), None)
        commit = commit_hash(ready)
        if task and commit:
            text = add_card_fields(text, task, {"Change commit": commit, "Change status": "Approved implementation completed."})
            task = next(x for x in parse_tasks(text) if x["id"] == task_id)
            text = move_card(text, task, "Completed", f"Approved implementation completed at commit {commit}.")
            changes.append(f"{task_id}: approved non-website implementation completed at {commit}")
            active.pop(task_id, None)
        elif task:
            text = move_card(text, task, "Human Approval", "Implementation result lacked a verifiable commit hash; awaiting retry.")
            changes.append(f"{task_id}: implementation returned without commit hash; returned to Human Approval")
            active.pop(task_id, None)

    # Gate 2 is satisfied only when the implementation commit is on origin/main.
    for task_id, item in list(active.items()):
        if not item.get("awaiting_merge") or not merged_into_main(item["commit"]):
            continue
        if not item.get("merge_detected_at"):
            item["merge_detected_at"] = stamp()
            changes.append(f"{task_id}: human merge detected; waiting for live deployment to settle")
            continue
        detected = dt.datetime.fromisoformat(item["merge_detected_at"])
        settle_seconds = int(os.environ.get("CMO_LIVE_SETTLE_SECONDS", "600"))
        if (now() - detected).total_seconds() < settle_seconds:
            continue
        task = next((x for x in parse_tasks(text) if x["id"] == task_id), None)
        if not task:
            continue
        live = capture_metrics(task, "live")
        if live.get("status") != "captured":
            changes.append(f"{task_id}: live measurement failed after merge; evidence retry retained")
            continue
        baseline_path = METRICS_DIR / f"{task_id}.baseline.json"
        baseline = json.loads(baseline_path.read_text(encoding="utf-8")) if baseline_path.exists() else {}
        rows = compare(baseline, live)
        evidence = metric_table(rows) if rows else "No comparable metrics returned."
        evidence_path = METRICS_DIR / f"{task_id}.live.json"
        text = add_card_fields(text, task, {
            "Live URL": live_url(),
            "Metrics evidence": str(evidence_path),
            "Metrics summary": metric_summary(rows),
            "Metrics table": evidence,
            "Change status": "Merged to main; live metrics captured.",
        })
        task = next(x for x in parse_tasks(text) if x["id"] == task_id)
        text = move_card(text, task, "Completed", "Merged to main; before/after evidence captured and attached.")
        changes.append(f"{task_id}: live deployment measured; task evidence\n{evidence}")
        active.pop(task_id, None)

    # Weekly cumulative impact is batched into this hourly cycle, not a new loop.
    week_marker = PROFILE / "state/last-website-impact-week"
    iso = now().date().isocalendar()
    week_key = f"{iso.year}-W{iso.week:02d}"
    marker = week_marker.read_text(encoding="utf-8").strip() if week_marker.exists() else ""
    if now().weekday() == 0 and marker != week_key:
        changes.append("Weekly website impact: " + json.dumps(weekly_summary(now().date() - dt.timedelta(days=1)), sort_keys=True))
        week_marker.parent.mkdir(parents=True, exist_ok=True)
        week_marker.write_text(week_key + "\n", encoding="utf-8")

    text = board_timestamp(text)
    BOARD.write_text(text, encoding="utf-8")
    save_json(ACTIVE, active)
    log(f"cycle changes={len(changes)} active={len(active)}")
    for change in changes:
        log(f"CHANGE {change}")
    try:
        post_changes(changes)
    except Exception as exc:
        log(f"DISCORD_FAILED error={type(exc).__name__}: {exc}")
        print(f"Discord post failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("\n".join(changes) if changes else "no changes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="run one cycle and exit")
    args = parser.parse_args()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with LOCK.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("hourly cycle already running", file=sys.stderr)
            return 0
        return run_cycle()


if __name__ == "__main__":
    raise SystemExit(main())
