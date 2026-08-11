from __future__ import annotations

import json
import sys

from cmo_runtime.agent_runtime import decision_bullets


def _revision_requirement_failure(fields: dict[str, object], artifact: str) -> str | None:
    try:
        round_number = int(str(fields.get("Revision round", "0")))
    except ValueError:
        return None
    if round_number < 1:
        return None
    request = str(fields.get(f"Approval thread {round_number} rejection", ""))
    folded = request.casefold()
    if "remove" in folded and "youtube" in folded and "source" in folded:
        if "youtube.com/" in artifact.casefold() or "youtu.be/" in artifact.casefold():
            return "Human revision requires removal of the YouTube source, but the artifact still cites it."
    return None


def decide(payload: dict[str, object]) -> dict[str, object]:
    card = payload.get("card")
    artifact = payload.get("artifact")
    if not isinstance(card, dict) or not isinstance(artifact, str):
        raise ValueError("review worker accepts only card and artifact")
    fields = card.get("fields")
    task_id = card.get("task_id")
    if not isinstance(fields, dict) or not isinstance(task_id, str):
        raise ValueError("card payload is malformed")

    latest = str(fields.get("Latest summary", ""))
    metric = str(fields.get("Metric", "")).strip()
    revision_failure = _revision_requirement_failure(fields, artifact)
    if "requires a DECISION SUMMARY" in latest:
        outcome = "send-back"
        reason = "Decision summary is malformed: provide 3–5 concrete, business-facing decision bullets before escalation."
    elif "PENDING HUMAN DECISION:" in artifact:
        outcome = "flag"
        reason = artifact.split("PENDING HUMAN DECISION:", 1)[1].splitlines()[0].strip()
    elif not artifact:
        outcome = "send-back"
        reason = "Attachment is unavailable or empty; attach a reviewable artifact."
    elif revision_failure:
        outcome = "send-back"
        reason = revision_failure
    elif not metric or metric.lower() in {"none", "n/a", "unknown"}:
        outcome = "send-back"
        reason = "Metric is missing; state a measurable benefit before escalation."
    elif not 3 <= len(decision_bullets(artifact)) <= 5:
        outcome = "send-back"
        reason = "Artifact requires 3–5 concrete, business-facing decision bullets."
    else:
        outcome = "escalate"
        reason = "Artifact, metric, and decision bullets satisfy the review contract."

    return {
        "task_id": task_id,
        "outcome": outcome,
        "reason": reason,
        "evidence": {
            "fresh_process": True,
            "input_keys": sorted(payload),
            "transcript_received": False,
        },
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        print(json.dumps(decide(payload), ensure_ascii=False))
    except (ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
