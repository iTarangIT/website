from __future__ import annotations

from pathlib import Path
from typing import Any

import ceo_artifacts
import dashboard_server
from cmo_runtime import decisions

PROFILE_DIR = dashboard_server.PROFILE_DIR
TASKS_FILE = dashboard_server.TASKS_FILE


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


def read_board(tasks_file: Path = TASKS_FILE, profile_dir: Path = PROFILE_DIR) -> dict[str, Any]:
    text = tasks_file.read_text(encoding="utf-8")
    tasks = dashboard_server.parse_tasks(text)
    topics: list[dict[str, Any]] = []
    blogs: list[dict[str, Any]] = []
    for task in tasks:
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
        if str(task.get("skill", task.get("owner", ""))).casefold() == "content":
            (blogs if task["artifact_path"] else topics).append(task)
    return {"tasks": tasks, "topics": topics, "blogs": blogs}
