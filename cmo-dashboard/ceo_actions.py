from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from pathlib import Path


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


# Topics no longer become board cards on submission. A rough subject is researched
# into candidate proposals in `cmo_runtime.topic_proposals`, and only an approved
# proposal mints a card. `add_topics` and `set_topic_stage` were the direct board
# writers that made an unvetted topic writable, and they are deliberately gone.


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
