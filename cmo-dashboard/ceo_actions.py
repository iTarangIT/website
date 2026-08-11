from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def _task(tasks_path: Path, task_id: str) -> dict[str, str]:
    import dashboard_server
    from cmo_runtime.task_file import TaskFileError

    match = next(
        (item for item in dashboard_server.parse_tasks(tasks_path.read_text(encoding="utf-8")) if item["id"] == task_id),
        None,
    )
    if match is None:
        raise TaskFileError(f"task not found: {task_id}")
    return match


def request_revision(profile_dir: Path, task_id: str, comment: str, requester: str) -> int:
    """Record a non-decision revision request while leaving the card in its lane."""
    from cmo_runtime.task_file import TaskFile, TaskFileError
    from cmo_runtime.decisions import is_decided

    comment = comment.strip()
    if not comment or "\n" in comment or "\r" in comment:
        raise TaskFileError("revision comment must be a non-empty single line")
    if is_decided(profile_dir, task_id):
        raise TaskFileError("revision request is refused because a human decision already exists")
    task_file = TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock")
    task = _task(task_file.path, task_id)
    current = str(task.get("revision_round", "0"))
    round_number = int(current) + 1 if re.fullmatch(r"\d+", current) else 1
    task_file.set_board_fields(
        task_id,
        {
            "Revision round": str(round_number),
            f"Approval thread {round_number} rejection": f"{requester}: {comment}",
            "Change status": "revision requested",
        },
    )
    return round_number


def greenlight_topic(profile_dir: Path, task_id: str, approver: str) -> None:
    """Record topic interest as notes, never as a human decision."""
    set_topic_stage(profile_dir, task_id, "approved", approver)


def set_topic_stage(profile_dir: Path, task_id: str, stage: str, actor: str) -> None:
    """Record topic approval or decline as board notes, never as authority."""
    from cmo_runtime.task_file import TaskFile, TaskFileError

    stage = stage.strip().casefold()
    if stage not in {"approved", "declined"}:
        raise TaskFileError("topic stage must be approved or declined")
    actor = actor.strip()
    if not actor or "\n" in actor or "\r" in actor:
        raise TaskFileError("topic actor must be a non-empty single line")
    task_file = TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock")
    task = _task(task_file.path, task_id)
    if str(task.get("skill", task.get("owner", ""))).casefold() != "content":
        raise TaskFileError("topic action requires a content card")
    import console_board

    if console_board.artifact_for(task, profile_dir) is not None:
        raise TaskFileError("a card with an artifact is a blog, not a topic")
    fields = {"Topic stage": stage}
    fields["Topic approved by" if stage == "approved" else "Topic declined by"] = actor
    task_file.set_board_fields(
        task_id,
        fields,
    )


def add_topics(profile_dir: Path, titles: list[Any], actor: str) -> dict[str, Any]:
    """Validate a complete batch, then add every non-duplicate card in one locked write."""
    from cmo_runtime.task_file import TaskFile, TaskFileError, utc_timestamp

    if not isinstance(titles, list) or not 1 <= len(titles) <= 25:
        raise TaskFileError("topic batch must contain 1 to 25 lines")
    actor = actor.strip()
    if not actor or "\n" in actor or "\r" in actor:
        raise TaskFileError("topic submitter must be a non-empty single line")
    clean: list[str] = []
    for index, value in enumerate(titles, 1):
        if not isinstance(value, str):
            raise TaskFileError(f"topic {index} must be text")
        title = value.strip()
        if not 3 <= len(title) <= 180 or "\n" in title or "\r" in title:
            raise TaskFileError(f"topic {index} must be one line between 3 and 180 characters")
        clean.append(title)

    tasks_path = profile_dir / "tasks.md"
    tasks = __import__("dashboard_server").parse_tasks(tasks_path.read_text(encoding="utf-8"))
    existing = {str(task.get("title", "")).strip().casefold() for task in tasks}
    seen: set[str] = set()
    accepted: list[str] = []
    skipped: list[dict[str, str]] = []
    for title in clean:
        key = title.casefold()
        if key in existing:
            skipped.append({"title": title, "reason": "already exists on the board"})
        elif key in seen:
            skipped.append({"title": title, "reason": "duplicate within this batch"})
        else:
            seen.add(key)
            accepted.append(title)

    numeric_ids = [
        int(match.group(1))
        for task in tasks
        if (match := re.fullmatch(r"TASK-([0-9]+)", str(task.get("id", ""))))
    ]
    next_id = max(numeric_ids, default=0) + 1
    timestamp = utc_timestamp()
    cards: list[str] = []
    added: list[dict[str, str]] = []
    for offset, title in enumerate(accepted):
        task_id = f"TASK-{next_id + offset:03d}"
        cards.append(
            f"""### {task_id} — {title}

- ID: {task_id}
- Title: {title}
- Owner: content
- Skill: content
- Priority: medium
- Status: Backlog
- Start date: not started
- Completed date: not completed
- Objective: Research and write a sourced, plain-language article from this CEO-submitted topic: {title}.
- Acceptance criteria:
  - Preserve the CEO's topic wording as the writing instruction.
  - Retain real source pages, URLs and dates in the research brief.
  - Produce the article and any explanatory SVG beneath artifacts/.
  - Do not publish or change the website without both human gates.
- Latest summary: Topic submitted from the CEO Console and queued for research-first writing; no separate topic approval is required.
- Description: CEO-submitted content topic queued for research and writing; no article artifact exists yet.
- Attachment: none
- Metric: Search impressions for the published blog page, measured by the Google Search Console Search Analytics API after publication; no uplift is claimed before a live baseline exists.
- Tag: action to be taken by: cmo
- Topic stage: proposed
- Topic submitted by: {actor}
- Change status: queued
- Last updated: {timestamp}
- Updated: {timestamp}"""
        )
        added.append({"id": task_id, "title": title})
    if cards:
        TaskFile(tasks_path, lock_path=profile_dir / "state" / "tasks.lock").add_board_cards(
            cards,
            section="Backlog",
        )
    return {"added": added, "skipped": skipped}


def read_watchlist(profile_dir: Path) -> list[str]:
    path = profile_dir / "state" / "ceo-watchlist.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def update_watchlist(profile_dir: Path, keyword: str, action: str) -> list[str]:
    """Update a private console watchlist without touching tasks.md."""
    from cmo_runtime.task_file import TaskFileError

    keyword = keyword.strip()
    action = action.strip().casefold()
    if not 2 <= len(keyword) <= 120 or "\n" in keyword or "\r" in keyword:
        raise TaskFileError("watchlist keyword must be one line between 2 and 120 characters")
    if action not in {"add", "remove"}:
        raise TaskFileError("watchlist action must be add or remove")
    state_dir = profile_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "ceo-watchlist.json"
    lock_path = state_dir / "ceo-watchlist.lock"
    lock_path.touch(exist_ok=True)
    with lock_path.open("r+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        items = read_watchlist(profile_dir)
        by_key = {item.casefold(): item for item in items}
        if action == "add":
            by_key.setdefault(keyword.casefold(), keyword)
        else:
            by_key.pop(keyword.casefold(), None)
        updated = list(by_key.values())
        descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=state_dir)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(updated, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    return updated
