from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import ceo_artifacts
import dashboard_server
from cmo_runtime import decisions
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


def publish_fingerprint(task: dict[str, Any], profile_dir: Path = PROFILE_DIR) -> str:
    """A digest of exactly what a publish would put on the website.

    Recorded when Gate 1 is approved, recomputed when publish is offered. If the
    two differ, something about the card moved after it was approved and the
    button refuses — "approved" has to mean approved *of this*, not of the card
    that happens to be under that ID now.

    Deliberately narrow: the article bytes, the diagram bytes, and the three card
    fields that decide where the post lands. A `Latest summary` reworded by the
    hourly cycle is not a reason to refuse to publish.
    """
    digest = hashlib.sha256()
    article = artifact_for(task, profile_dir)
    digest.update((article.read_bytes() if article else b""))
    digest.update(b"\x00")
    for name in ("category", "attachment"):
        digest.update(str(task.get(name, "")).strip().encode("utf-8"))
        digest.update(b"\x00")
    for key in sorted(key for key in task if key.startswith("image_slot_")):
        reference = str(task.get(key, "")).strip()
        digest.update(f"{key}={reference}".encode("utf-8"))
        digest.update(b"\x00")
        candidate = (profile_dir / reference).resolve() if reference.startswith("artifacts/") else None
        try:
            if candidate is not None:
                candidate.relative_to((profile_dir / "artifacts").resolve())
                digest.update(candidate.read_bytes())
        except (OSError, ValueError):
            digest.update(b"<unreadable>")
        digest.update(b"\x00")
    return digest.hexdigest()


def read_board(tasks_file: Path = TASKS_FILE, profile_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    text = tasks_file.read_text(encoding="utf-8")
    tasks = dashboard_server.parse_tasks(text)
    heartbeat = worker_heartbeat(profile_dir)
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
        task["decision_status"] = "approved" if task["decision_approved"] else "awaiting decision"
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
            blogs.append(task)
    return {"tasks": tasks, "blogs": blogs}
