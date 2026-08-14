from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import ceo_artifacts
import dashboard_server
from cmo_runtime import decisions
from cmo_runtime.console_db import ConsoleDB, ConsoleDBError
from cmo_runtime.content_flow import (
    BLOCKING_CHANGE_STATUSES,
    NON_ARTICLE_WORK_TYPES,
    WRITE_FAILED,
)

PROFILE_DIR = dashboard_server.PROFILE_DIR
TASKS_FILE = dashboard_server.TASKS_FILE

#: Where the content worker records what it is doing right now.
WORKER_HEARTBEAT = "state/content-worker.json"

#: The fixed preview `cmo-changes` deploys to. It does not change per commit.
PREVIEW_ORIGIN = "https://itarangwebsite.vercel.app"

#: The card field the publish click writes when the post is on `cmo-changes`.
PUBLISHED_STATUS = "published to cmo-changes"

def artifact_for(task: dict[str, Any], profile_dir: Path = PROFILE_DIR) -> Path | None:
    """Return a real card attachment only when it resolves beneath artifacts/."""
    path = dashboard_server._attachment_path(task, profile_dir)
    if path is None:
        return None
    try:
        path.resolve().relative_to((profile_dir / "artifacts").resolve())
    except ValueError:
        return None
    return path


def worker_heartbeat(profile_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    """What the content worker last said it was doing. Missing is not an error."""
    try:
        value = json.loads((profile_dir / WORKER_HEARTBEAT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _is_content(task: dict[str, Any]) -> bool:
    return str(task.get("skill", task.get("owner", ""))).casefold() == "content"


def _positive_round(task: dict[str, Any]) -> bool:
    """Whether this card carries a revision the writer can actually serve.

    The round is what names the comment being answered. Without one the worker
    refuses the card, so reading it as "Being rewritten" would promise a rewrite
    that is never going to arrive.
    """
    return bool(re.fullmatch(r"[1-9][0-9]*", str(task.get("revision_round", "")).strip()))


def blog_state(task: dict[str, Any], heartbeat: dict[str, Any] | None = None) -> dict[str, Any]:
    """What Sanchit sees on the Blogs tab for one card, and why.

    A card used to reach this tab only once it had an artifact, which meant the
    minutes between approving a topic and reading the article showed nothing at
    all — and a writer that failed nine times in a row showed nothing at all
    either. Every content card now has a state here, and the two that report
    trouble (`failed`, `held`) carry the reason in the words that were written
    onto the card, not a code.

    `label` is what the row says. `reason` is the line under it, when there is
    something to say. `retryable` is the only thing that puts a button on the row,
    and only a run that failed on its own is retryable — never a card a human held.
    """
    beat = heartbeat or {}
    section = str(task.get("board_section") or task.get("status") or "").strip()
    change = str(task.get("change_status", "")).strip().casefold()
    summary = str(task.get("latest_summary", "")).strip()
    approved = bool(task.get("decision_approved"))
    published_url = str(task.get("preview_url", "")).strip()

    def result(
        state: str,
        label: str,
        *,
        reason: str = "",
        retryable: bool = False,
        started_at: str = "",
        url: str = "",
    ) -> dict[str, Any]:
        return {
            "state": state,
            "label": label,
            "reason": reason,
            "retryable": retryable,
            "started_at": started_at,
            "url": url,
        }

    if change == PUBLISHED_STATUS or (published_url and approved and change.startswith("published")):
        return result("published", "Live on the site", url=published_url)
    if change == "executing revision":
        return result("rewriting", "Being rewritten", reason=summary)
    if change == "revision requested" and _positive_round(task):
        return result("rewriting", "Being rewritten", reason=summary)
    if section == "In Progress":
        # `execute()` writes the research brief onto the card before it calls the
        # writer, so the card itself says which half of the run is happening.
        started = (
            str(beat.get("started_at", ""))
            if str(beat.get("task_id", "")) == task.get("id")
            else str(task.get("updated", ""))
        )
        if str(task.get("research_reference") or "").strip():
            return result("writing", "Writing…", started_at=started)
        return result("researching", "Researching…", started_at=started)
    if change == WRITE_FAILED:
        return result(
            "failed",
            "Could not be written",
            reason=summary or "The writer stopped without saying why.",
            retryable=True,
        )
    if approved:
        return result("approved", "Approved")
    if section == "CMO Review":
        return result("checking", "Being checked", reason=summary)
    if section == "Human Approval":
        return result("awaiting_you", "Awaiting you")
    if section == "Backlog":
        # "Queued to be written" has to mean the worker will actually pick this
        # up. A commissioning card sat here reading "queued" while carrying a
        # change status the worker refuses — the tab was promising a write that
        # was never going to start, which is the same lie as showing "Being
        # rewritten" for a revision nothing can service.
        if change in BLOCKING_CHANGE_STATUSES or str(task.get("topic_stage", "")).strip().casefold() != "approved":
            return result("held", "On hold", reason=summary)
        return result("queued", "Queued to be written")
    return result("awaiting_you", "Awaiting you")


def publish_components(
    task: dict[str, Any], profile_dir: Path = PROFILE_DIR
) -> list[tuple[str, bytes, str]]:
    """Exactly what a publish would put on the website, part by part.

    Each entry is (name, the bytes that go into the fingerprint, something a human
    can read). The digest is taken over the bytes and nothing else, so splitting
    this out changes no decision — a fingerprint computed here is the same
    fingerprint as before, byte for byte.

    The reason for the split is that a digest can say *that* something changed and
    never *what*. When an approval goes stale, "the article changed" and "the
    category changed from financing to safety" are different messages, and only one
    of them tells you whether to look again.

    Deliberately narrow: the article, the diagram, and the three card fields that
    decide where the post lands. A `Latest summary` reworded by the hourly cycle is
    not a reason to refuse to publish.
    """
    parts: list[tuple[str, bytes, str]] = []

    article = artifact_for(task, profile_dir)
    body = article.read_bytes() if article else b""
    parts.append(("article", body, f"sha256:{hashlib.sha256(body).hexdigest()[:12]}"))

    for name in ("category", "attachment"):
        value = str(task.get(name, "")).strip()
        parts.append((name, value.encode("utf-8"), value or "(none)"))

    for key in sorted(key for key in task if key.startswith("image_slot_")):
        reference = str(task.get(key, "")).strip()
        candidate = (profile_dir / reference).resolve() if reference.startswith("artifacts/") else None
        image = b""
        try:
            if candidate is not None:
                candidate.relative_to((profile_dir / "artifacts").resolve())
                image = candidate.read_bytes()
        except (OSError, ValueError):
            image = b"<unreadable>"
        parts.append((
            key,
            f"{key}={reference}".encode("utf-8") + b"\x00" + image,
            f"{reference or '(none)'} sha256:{hashlib.sha256(image).hexdigest()[:12]}",
        ))
    return parts


def publish_fingerprint(task: dict[str, Any], profile_dir: Path = PROFILE_DIR) -> str:
    """One digest over `publish_components`, recorded when Gate 1 is approved.

    Recomputed when publish is offered. If the two differ, something about the card
    moved after it was approved — "approved" has to mean approved *of this*, not of
    whatever is under that ID now.
    """
    digest = hashlib.sha256()
    for _name, payload, _readable in publish_components(task, profile_dir):
        digest.update(payload)
        digest.update(b"\x00")
    return digest.hexdigest()


def publish_component_record(
    task: dict[str, Any], profile_dir: Path = PROFILE_DIR
) -> dict[str, str]:
    """The readable half of the components, flat, for the decision record.

    `decision_record` stringifies every value it reads back, so anything stored
    there has to be a flat string. These are what let a later staleness name the
    part that moved.
    """
    return {
        f"component_{name}": readable
        for name, _payload, readable in publish_components(task, profile_dir)
    }


#: Component name → how to say it to somebody who did not write the code.
COMPONENT_NAMES = {
    "article": "the article",
    "category": "the category",
    "attachment": "which file the card points at",
}


def describe_change(
    record: dict[str, str],
    task: dict[str, Any],
    profile_dir: Path = PROFILE_DIR,
) -> list[str]:
    """What moved since this decision, in sentences rather than digests.

    Compares the components recorded at approval with the ones measured now. A
    record made before components were kept cannot name anything, so it says so
    and points at what the card itself remembers — the thread entries and archived
    versions written after the decision, which is where the answer actually is.
    """
    current = publish_component_record(task, profile_dir)
    recorded = {name: value for name, value in record.items() if name.startswith("component_")}
    if not recorded:
        after = [
            f"{name.replace('_', ' ')}: {value}"
            for name, value in sorted(task.items())
            if str(name).startswith(("approval_thread_", "revision_")) and str(value).strip()
        ]
        return [
            "This approval predates the change record, so what moved was not captured.",
            *(["The card remembers: " + "; ".join(after)] if after else []),
        ]

    changes: list[str] = []
    for name in sorted(set(recorded) | set(current)):
        was, now = recorded.get(name, "(absent)"), current.get(name, "(absent)")
        if was == now:
            continue
        label = COMPONENT_NAMES.get(name[len("component_"):], name[len("component_"):])
        changes.append(
            f"{label} changed" if name == "component_article"
            else f"{label} changed from {was} to {now}"
        )
    return changes or ["Something in the publish inputs changed."]


def process_payload(database: ConsoleDB | None, task_id: str) -> list[dict[str, Any]]:
    """The recorded stages for one card, shaped for the Process tab.

    Reads rows and only rows. A stage the pipeline never recorded produces no
    entry — the tab has no notion of a stage that "should" be there, so it can
    never imply work that did not happen. The source list under research is built
    from `stage_fetches`, so a URL the article happens to cite but nothing ever
    fetched cannot appear here.
    """
    if database is None or not task_id:
        return []
    try:
        stages = database.stages_for_task(task_id)
    except (ConsoleDBError, sqlite3.Error):
        return []
    payload: list[dict[str, Any]] = []
    for stage in stages:
        fetches = stage.get("fetches", [])
        payload.append(
            {
                "stage": stage["stage"],
                "label": stage["label"],
                "ordinal": stage["ordinal"],
                "attempt": stage["attempt"],
                "status": stage["status"],
                "started_at": stage["started_at"],
                "ended_at": stage["ended_at"],
                "duration_ms": stage["duration_ms"],
                "summary": stage["summary"],
                "detail": stage["detail"],
                "fetches": [
                    {
                        "kind": item["kind"],
                        "outcome": item["outcome"],
                        "url": item["url"],
                        "query": item["query"],
                        "title": item["title"],
                        "published_date": item["published_date"],
                        "accessed_at": item["accessed_at"],
                        "message": item["message"],
                    }
                    for item in fetches
                ],
                "fetched": sum(
                    1 for item in fetches if item["outcome"] in ("fetched", "cached")
                ),
                "failed": sum(1 for item in fetches if item["outcome"] == "failed"),
            }
        )
    return payload


def read_board(tasks_file: Path = TASKS_FILE, profile_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    text = tasks_file.read_text(encoding="utf-8")
    tasks = dashboard_server.parse_tasks(text)
    heartbeat = worker_heartbeat(profile_dir)
    # One connection for the whole board read, not one per card. Opened lazily and
    # never allowed to take the board down with it: a console that cannot show the
    # process is still a console that shows the work.
    database: ConsoleDB | None = None
    try:
        database = ConsoleDB(profile_dir)
    except (ConsoleDBError, sqlite3.Error, OSError):
        database = None
    blogs: list[dict[str, Any]] = []
    for task in tasks:
        # `research_brief` is about to be replaced by the loaded document, and a
        # missing one becomes None — which `str()` turns into the truthy "None".
        # Keep the card's own reference under its own key; the Blogs tab reads it
        # to tell researching from writing.
        task["research_reference"] = str(task.get("research_brief", "")).strip()
        artifact = artifact_for(task, profile_dir)
        task["artifact_path"] = str(artifact or "")
        task["attachment_url"] = (
            f"/ceo/artifact?task={task['id']}" if task["artifact_path"] else ""
        )
        decision_summary = decisions.decision_record(profile_dir, task["id"])
        task["decision_summary"] = decision_summary
        task["decision_approved"] = bool(
            decision_summary and decision_summary.get("decision") == "approve"
        )
        # A decision whose artifact has moved covers nothing. Publish already
        # refuses it; the console has to say so and offer the way out, or the card
        # deadlocks between "already decided" and "the approval does not match".
        stale = False
        changed: list[str] = []
        if decision_summary:
            fingerprint = publish_fingerprint(task, profile_dir)
            stale = decisions.decision_is_stale(decision_summary, fingerprint)
            if stale:
                changed = describe_change(decision_summary, task, profile_dir)
        task["decision_stale"] = stale
        task["decision_change"] = changed
        task["decision_status"] = (
            "approval out of date" if stale
            else "approved" if task["decision_approved"]
            else "awaiting decision"
        )
        task["approval_thread"] = dashboard_server.approval_thread(task)
        task["research_brief"] = ceo_artifacts.text_reference(task, profile_dir)
        task["article"] = ceo_artifacts.artifact_payload(task, artifact, profile_dir) if artifact else None
        change_status = str(task.get("change_status", "")).strip()
        change_type = str(task.get("change_type", "")).strip().casefold()
        has_pipeline = change_type == "website" or any(
            task.get(name)
            for name in ("branch", "commit_url", "preview_url", "metrics_evidence")
        )
        waiting_on = ""
        if has_pipeline:
            if change_status.casefold() == "awaiting gate 2":
                waiting_on = "Waiting for a human to merge the approved commit to main (Gate 2)."
            elif task["decision_approved"]:
                waiting_on = "Gate 1 is recorded; production still waits for the human Gate 2 merge and live evidence."
            else:
                waiting_on = "Waiting for human preview approval (Gate 1); approval does not publish."
        task["publishing_pipeline"] = {
            "branch": str(task.get("branch", "")),
            "commit": str(task.get("commit_hash(es)", task.get("commit", ""))),
            "commit_url": str(task.get("commit_url", "")),
            "preview_url": str(task.get("preview_url", "")),
            "lighthouse_evidence": str(task.get("metrics_evidence", "")),
            "change_status": change_status,
            "waiting_on": waiting_on,
        } if has_pipeline else None
        # Every content card is a blog card, artifact or not. It used to take an
        # artifact to get here, which is exactly why a card being written, or one
        # whose nine writer attempts all failed, looked to Sanchit like nothing was
        # happening at all.
        #
        # The work type still matters. An internal board-state summary is written by
        # the content skill and lands in artifacts/ like an article does — and then
        # sits on the Blogs tab as a 61-word list of lane counts. The writer refuses
        # that work type through the same frozenset this imports, so the two cannot
        # disagree.
        work_type = str(task.get("work_type", "")).strip().casefold()
        if _is_content(task) and work_type not in NON_ARTICLE_WORK_TYPES:
            task["blog"] = blog_state(task, heartbeat)
            task["process"] = process_payload(database, task["id"])
            blogs.append(task)
    if database is not None:
        database.close()
    return {"tasks": tasks, "blogs": blogs}
