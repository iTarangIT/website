from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from datetime import UTC, date, datetime
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


#: What a cleared publish date is written as. The board writer refuses an empty
#: field value, and any non-date reads as "no plan" -- so this is a word a human
#: can read rather than a blank nobody can tell from a field that was never set.
NOT_SCHEDULED = "not scheduled"


def set_publish_date(profile_dir: Path, task_id: str, day: str, requester: str) -> dict[str, object]:
    """Write down the day an approved article is meant to go out.

    This is a plan, not a trigger. **Nothing on this box fires on it** — there is
    no cron here, and the watchdog that used to stand in for one was
    decommissioned; a date that published an article by itself would also be an
    agent reaching a publish path, which `SOUL.md` section 12 keeps in a human's
    hands. So the field is read by the console to say "Scheduled — 2 Sep", and
    the Publish button is still a press.

    Passing an empty day clears it, because a plan you cannot cancel is not a
    plan. `set_board_fields` refuses an empty value, so clearing writes
    `NOT_SCHEDULED` rather than a blank: `_scheduled_for` reads anything that is
    not a date as no plan, and a card that says "not scheduled" reads correctly
    to a human opening `tasks.md`. It records no decision and touches no
    lifecycle field.
    """
    from cmo_runtime.task_file import TaskFile, TaskFileError, utc_timestamp

    requester = requester.strip()
    if not requester:
        raise TaskFileError("a publish date requires an authenticated human")
    task = _task(profile_dir / "tasks.md", task_id)

    day = str(day or "").strip()
    if day:
        try:
            parsed = date.fromisoformat(day)
        except ValueError:
            raise TaskFileError("a publish date must be written as YYYY-MM-DD") from None
        if parsed < datetime.now(UTC).date():
            # A date already gone is not a schedule, and silently accepting one
            # would put a card in a state that reads as planned and is not.
            raise TaskFileError(f"{day} has already passed; pick a day from today onwards")
        day = parsed.isoformat()

    timestamp = utc_timestamp()
    TaskFile(profile_dir / "tasks.md", lock_path=profile_dir / "state" / "tasks.lock").set_board_fields(
        task_id,
        {
            "Publish at": day or NOT_SCHEDULED,
            "Latest summary": (
                f"Publish planned for {day} by {requester} at {timestamp}."
                if day
                else f"Publish date cleared by {requester} at {timestamp}."
            ),
        },
    )
    return {"ok": True, "task_id": task_id, "publish_at": day}


MAX_ARTICLE_BYTES = 512 * 1024



def _normalised(text: str) -> bytes:
    """The bytes an edit actually lands as: newlines settled, one trailing newline.

    Shared so that "is this different from what is on disk" is one question with one
    answer, rather than the saver's answer and the caller's.
    """
    body = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    return (body.rstrip() + "\n").encode("utf-8")


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
    encoded = _normalised(text)
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


#: The cap the topic pipeline already puts on a title, kept in step so a headline
#: a human types here cannot be longer than one the model proposed.
MAX_TITLE_CHARS = 180

#: The front-matter line the published page takes its heading from.
FRONT_MATTER_TITLE = re.compile(r"(?m)^title:[^\n]*$")

#: The article's own H1 — what the console reader shows. The publisher strips it and
#: uses the front-matter title instead, so the two must say the same thing.
BODY_H1 = re.compile(r"(?m)^#[ \t]+\S.*$")


def retitle_markdown(source: str, title: str) -> str:
    """The article with its front-matter `title:` and its H1 renamed, nothing else.

    Line surgery rather than a parse-and-rebuild. The header block is compared field
    by field on save — `check_edited_front_matter` refuses an edit that drops one —
    so every other line has to come back byte for byte, which reserialising a parsed
    dict does not guarantee.

    An article with no H1 does not grow one. The rule the header guard states applies
    here too: preserving what the writer left is not the same as inventing it.
    """
    import ceo_reader

    _metadata, front_matter, body = ceo_reader.split_source(source)
    if front_matter:
        front_matter, count = FRONT_MATTER_TITLE.subn(lambda _m: f"title: {title}", front_matter, count=1)
        if not count:
            raise _refusal("this article's front matter has no title line to change")
    return front_matter + BODY_H1.sub(lambda _m: f"# {title}", body, count=1)


def _refusal(message: str) -> Exception:
    from cmo_runtime.task_file import TaskFileError

    return TaskFileError(message)


def _clean_title(title: str) -> str:
    """Normalise a typed headline, or refuse it with the reason a human can act on."""
    import ceo_reader

    cleaned = " ".join(str(title or "").split())
    if not cleaned:
        raise _refusal("a title cannot be empty")
    if len(cleaned) > MAX_TITLE_CHARS:
        raise _refusal(f"a title cannot be longer than {MAX_TITLE_CHARS} characters")
    # The header is not YAML. `ceo_reader` strips surrounding quotes when it reads a
    # value back but `content_flow._frontmatter` and the publisher do not, so a
    # quoted title would show bare on this console and publish with the quotes still
    # on it. Refuse rather than silently pick one of the two readings.
    read_back = ceo_reader.strip_front_matter(f"---\ntitle: {cleaned}\n---\n")[0].get("title", "")
    if read_back != cleaned:
        raise _refusal("a title cannot start or end with a quote mark; type it as plain text")
    return cleaned


def rename_article(profile_dir: Path, task_id: str, title: str, editor: str) -> dict[str, object]:
    """Retitle an article everywhere it is named, as one recorded revision.

    A blog title is written down four times: the board card's heading and its
    mirrored `Title` field, the article's front-matter `title:` — which is what the
    published page's layout uses — and the article's H1, which is what this console
    renders. Nothing kept them in step, so the only honest rename moves all four.

    The article half goes through `save_article_edit` rather than writing the file
    here. That is deliberate: it already refuses an article a decision still covers,
    already archives the version being replaced as `<stem>.r<n>.md`, already writes
    the change into the approval thread under the name that made it, and already
    checks the header survived. A rename is an edit that happens to touch two lines,
    and giving it a second way into the artifact would mean two sets of those rules.

    The slug is not touched, so the page keeps its address.
    """
    import console_board
    from cmo_runtime.task_file import TaskFile

    title = _clean_title(title)
    tasks_path = profile_dir / "tasks.md"
    task = _task(tasks_path, task_id)
    article = console_board.artifact_for(task, profile_dir)
    if article is None:
        raise _refusal(f"{task_id} has no article to retitle")

    source = article.read_text(encoding="utf-8", errors="replace")
    renamed = retitle_markdown(source, title)
    # Asked the way `save_article_edit` asks it. Comparing the raw strings would call
    # a file whose only difference is trailing whitespace "changed", and the save
    # would then refuse it as unchanged — a rename that reports a failure it caused.
    article_changed = _normalised(renamed) != article.read_bytes()
    card_matches = str(task.get("title", "")).strip() == title

    # Unchanged means unchanged *everywhere*. Asking only about the article would
    # deadlock a retry after the board write below failed: the article would already
    # say the new title, so the second press would be refused and the card would keep
    # the old one forever.
    if not article_changed and card_matches:
        raise _refusal("the title is unchanged")

    result: dict[str, object] = {"ok": True, "task_id": task_id, "title": title}
    if article_changed:
        result.update(save_article_edit(profile_dir, task_id, renamed, editor))
        result["title"] = title

    # Not one transaction with the write above, and it cannot be — two files, two
    # locks. The article goes first because that is where the refusals live, and the
    # check above lets a human press Save again to finish a rename that got this far
    # and no further.
    try:
        TaskFile(tasks_path, lock_path=profile_dir / "state" / "tasks.lock").set_card_title(
            task_id, title
        )
    except Exception as error:
        raise _refusal(
            f"the article was retitled but the board card was not: {error}. "
            "Press Save again to finish renaming the card."
        ) from error
    return result


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
