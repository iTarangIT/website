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


def _decision_that_holds(profile_dir: Path, task: dict[str, str]) -> dict[str, str] | None:
    """The decision still covering this artifact, or None if none does.

    A current decision closes the article: editing it would change what was
    approved, and asking for changes to it would be asking about something already
    settled. Both stay refused, and that rule is unchanged.

    A decision whose fingerprint has gone stale covers nothing — the thing approved
    no longer exists. Approve-again alone would be a trap there: re-read a stale
    article, find something wrong, and the only control on screen approves it. So a
    stale decision reopens both.
    """
    import console_board
    from cmo_runtime.decisions import decision_is_stale, decision_record

    record = decision_record(profile_dir, task["id"])
    if record is None:
        return None
    if decision_is_stale(record, console_board.publish_fingerprint(task, profile_dir)):
        return None
    return record


def request_revision(profile_dir: Path, task_id: str, comment: str, requester: str) -> int:
    """Record a non-decision revision request while leaving the card in its lane."""
    from cmo_runtime.task_file import TaskFile, TaskFileError

    comment = comment.strip()
    if not comment or "\n" in comment or "\r" in comment:
        raise TaskFileError("revision comment must be a non-empty single line")
    task_file = TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock")
    task = _task(task_file.path, task_id)
    if _decision_that_holds(profile_dir, task) is not None:
        raise TaskFileError("revision request is refused because a human decision already exists")
    # A card that has not reached Human Approval has not been offered to anybody,
    # so there is nothing to ask changes to. This used to succeed: it set
    # `revision requested` on a card still in CMO Review, and once the content
    # worker existed that meant a rewrite started on an article its reader had
    # never seen. `DecisionStore` refuses the same lane for approvals; this makes
    # the two halves of the decision surface agree.
    section = str(task.get("board_section") or task.get("status", "")).strip()
    if section != "Human Approval":
        raise TaskFileError(
            f"{task_id} is in {section or 'an unknown lane'}, not Human Approval, so there is "
            "nothing to ask changes to yet"
        )
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


def retry_write(profile_dir: Path, task_id: str, requester: str) -> dict[str, object]:
    """Put a card the writer failed on back in the queue.

    The worker deliberately will not retry a failure by itself — nine attempts on
    TASK-084 failed in a row, and a loop that kept trying would have burned the
    budget without telling anyone. So the retry is a human's click, and this is
    all it does: clear `write failed` back to `queued` and say who asked.

    It refuses anything that is not a failed card. `blocked` means a human parked
    it, and clearing somebody's hold is not a retry. It records no decision.
    """
    from cmo_runtime.content_flow import WRITE_FAILED
    from cmo_runtime.task_file import TaskFile, TaskFileError, utc_timestamp

    requester = requester.strip()
    if not requester:
        raise TaskFileError("a retry requires an authenticated human")
    task = _task(profile_dir / "tasks.md", task_id)
    if str(task.get("board_section") or task.get("status", "")).strip() != "Backlog":
        raise TaskFileError(f"{task_id} is not in Backlog, so there is nothing to requeue")
    if str(task.get("change_status", "")).strip().casefold() != WRITE_FAILED:
        raise TaskFileError(
            f"{task_id} did not fail to be written, so it cannot be retried "
            "(a card a human put on hold is released by that human, not by a retry)"
        )
    timestamp = utc_timestamp()
    TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id,
        {
            "Change status": "queued",
            "Latest summary": f"Requeued by {requester} at {timestamp} after the previous write failed.",
        },
    )
    return {"ok": True, "task_id": task_id, "change_status": "queued", "requeued_at": timestamp}


MAX_ARTICLE_BYTES = 512 * 1024



def _next_revision(article: Path, current_round: int) -> int:
    """The first round number that has not already archived a version."""
    used = {current_round}
    for path in article.parent.glob(f"{article.stem}.r*{article.suffix}"):
        match = re.fullmatch(rf"{re.escape(article.stem)}\.r(\d+)", path.stem)
        if match:
            used.add(int(match.group(1)))
    return max(used) + 1


def save_article_edit(profile_dir: Path, task_id: str, text: str, editor: str) -> dict[str, object]:
    """Save a human's in-console rewrite as a new revision of the article.

    Same shape as a writer revision: the version being replaced is preserved as
    `<stem>.r<n>.md`, the round advances, and the event joins the approval thread.
    It records no decision — `DecisionStore` remains the only approval writer.
    """
    import console_board
    from cmo_runtime.task_file import TaskFile, TaskFileError

    editor = editor.strip()
    body = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not body.strip():
        raise TaskFileError("an edited article cannot be empty")
    encoded = (body.rstrip() + "\n").encode("utf-8")
    if len(encoded) > MAX_ARTICLE_BYTES:
        raise TaskFileError("the edited article exceeds the 512 KB limit")
    tasks_path = profile_dir / "tasks.md"
    task = _task(tasks_path, task_id)
    article = console_board.artifact_for(task, profile_dir)
    if article is None:
        raise TaskFileError(f"{task_id} has no article to edit")
    if _decision_that_holds(profile_dir, task) is not None:
        raise TaskFileError(
            "this article already carries a human decision; editing it would change "
            "what was approved. Ask for a revision instead."
        )
    if article.read_bytes() == encoded:
        raise TaskFileError("the article is unchanged")

    # An article's front matter is not prose — it carries the slug the page is
    # served at, the category page it is listed on, and the description the index
    # shows. An edit that damages it leaves an article that still reads perfectly
    # and can no longer be published at all, and until this check existed that only
    # surfaced at the publish preflight, after the article had been read and
    # approved on the broken version.
    #
    # The console is the only place a human can damage the header, so it is the
    # only place worth catching it. Preservation only: an article that never had
    # front matter is not made to grow some.
    from cmo_runtime.content_flow import ContentRunRefused, check_edited_front_matter

    try:
        check_edited_front_matter(article.read_text(encoding="utf-8", errors="replace"), body)
    except ContentRunRefused as error:
        raise TaskFileError(
            f"this edit breaks the article's front matter: {error}. "
            "Fix the block between the --- lines; the article cannot be published without it."
        ) from error

    current = str(task.get("revision_round", "0"))
    current_round = int(current) if re.fullmatch(r"\d+", current) else 0
    round_number = _next_revision(article, current_round)
    archive = article.with_name(f"{article.stem}.r{round_number}{article.suffix}")
    if archive.exists():
        raise TaskFileError(f"revision {round_number} is already archived")

    directory = article.parent
    previous = article.read_bytes()
    _atomic_write(archive, previous)
    try:
        _atomic_write(article, encoded)
    except OSError:
        archive.unlink(missing_ok=True)
        raise
    handle = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)

    TaskFile(tasks_path, lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id,
        {
            "Revision round": str(round_number),
            f"Revision {round_number} article archive": archive.relative_to(profile_dir).as_posix(),
            f"Approval thread {round_number} edit": (
                f"{editor} edited the article in the console; "
                f"the previous version is kept as {archive.name}"
            ),
        },
    )
    return {
        "ok": True,
        "revision_round": round_number,
        "archived_as": archive.name,
        "bytes": len(encoded),
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


# Topics no longer become board cards on submission. A rough subject is researched
# into candidate proposals in `cmo_runtime.topic_proposals`, and only an approved
# proposal mints a card. `add_topics` and `set_topic_stage` were the direct board
# writers that made an unvetted topic writable, and they are deliberately gone.


def read_research_queue(profile_dir: Path) -> list[dict[str, str]]:
    """Subjects sent over from Analytics, waiting for a research run in Topics."""
    path = profile_dir / "state" / "ceo-research-queue.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return []
    if not isinstance(value, list):
        return []
    rows = []
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("subject"), str):
            rows.append(
                {
                    "subject": item["subject"],
                    "reason": str(item.get("reason", "")),
                    "queued_by": str(item.get("queued_by", "")),
                }
            )
    return rows


def update_research_queue(
    profile_dir: Path,
    subject: str,
    action: str,
    *,
    reason: str = "",
    actor: str = "",
) -> list[dict[str, str]]:
    """Queue or drop an analytics subject. Queuing spends nothing and cards nothing."""
    from cmo_runtime.task_file import TaskFileError

    subject = " ".join(subject.split())
    action = action.strip().casefold()
    if not 2 <= len(subject) <= 180:
        raise TaskFileError("a research subject must be between 2 and 180 characters")
    if action not in {"add", "remove"}:
        raise TaskFileError("research queue action must be add or remove")
    state_dir = profile_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / "ceo-research-queue.json"
    lock_path = state_dir / "ceo-research-queue.lock"
    lock_path.touch(exist_ok=True)
    with lock_path.open("r+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle, fcntl.LOCK_EX)
        by_key = {item["subject"].casefold(): item for item in read_research_queue(profile_dir)}
        if action == "add":
            by_key.setdefault(
                subject.casefold(),
                {"subject": subject, "reason": " ".join(reason.split())[:400], "queued_by": actor},
            )
        else:
            by_key.pop(subject.casefold(), None)
        updated = list(by_key.values())
        _atomic_write(path, (json.dumps(updated, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return updated


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
