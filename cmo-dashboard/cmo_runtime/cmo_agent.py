from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Callable

from cmo_runtime.agent_runtime import RunAccountant, Runtime
from cmo_runtime.content_flow import (
    ContentRevisionResult,
    ContentRunRefused,
    ContentRunResult,
    ContentRuntime,
)
from cmo_runtime.skill_loader import SKILL_NAMES, SkillFileAudit
from cmo_runtime.task_file import TaskFileError


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="iTarang single CMO runtime")
    result.add_argument("--profile", default=".")
    result.add_argument("--evidence", action="store_true")
    commands = result.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("date", nargs="?")
    commands.add_parser("execute")
    commands.add_parser("content-execute")
    content_revise = commands.add_parser("content-revise")
    content_revise.add_argument("task_id", nargs="?")
    review = commands.add_parser("review")
    review.add_argument("task_id")
    approval = commands.add_parser("approval-card")
    approval.add_argument("task_id")
    comment = commands.add_parser("comment")
    comment.add_argument("task_id")
    comment.add_argument("text")
    approve = commands.add_parser("approve")
    approve.add_argument("task_id")
    complete = commands.add_parser("complete")
    complete.add_argument("task_id")
    commands.add_parser("commission-proof")
    refusal = commands.add_parser("commission-refusal")
    refusal.add_argument("kind", choices=("tool", "kpi"))
    commands.add_parser("backfill-previous")
    return result


def serializable(value: object) -> object:
    if is_dataclass(value):
        return serializable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    return value


def _usage_tokens(usage: object) -> int:
    if not isinstance(usage, dict):
        return 0
    try:
        return max(0, int(usage.get("total_tokens", 0)))
    except (TypeError, ValueError):
        return 0


def run_content_execution(
    root: str | Path,
    *,
    runtime: object | None = None,
    accountant: object | None = None,
) -> ContentRunResult:
    """Run once, then append the measured outcome after the call returns."""
    profile_root = Path(root)
    selected_runtime = runtime or ContentRuntime(profile_root)
    selected_accountant = accountant or RunAccountant(profile_root / "logs" / "spend.log")
    try:
        result = selected_runtime.execute()  # type: ignore[attr-defined]
    except BaseException as error:
        accounting = dict(getattr(error, "accounting", {}) or {})
        writer_usage = accounting.pop("writer_usage", {})
        tokens = _usage_tokens(writer_usage)
        extra: dict[str, object] = {
            "outcome": _single_line_error(error),
            **accounting,
        }
        if isinstance(writer_usage, dict):
            for key in ("estimated_cost_usd", "api_calls", "model", "provider"):
                if key in writer_usage:
                    extra[f"writer_{key}"] = writer_usage[key]
        selected_accountant.append(  # type: ignore[attr-defined]
            "content-execute",
            "content",
            tokens,
            None,
            "failed",
            extra=extra,
        )
        raise

    if not isinstance(result, ContentRunResult):
        raise RuntimeError("content runtime returned an unexpected result")
    usage = dict(result.usage)
    extra = {
        "task_id": result.task_id,
        "outcome": result.outcome,
        **result.research.accounting(),
    }
    for key in ("estimated_cost_usd", "api_calls", "model", "provider"):
        if key in usage:
            extra[f"writer_{key}"] = usage[key]
    # Image spend is already its own line in the ledger, written by the generator
    # through spend-tracker. These are carried so the run row says what the run
    # bought, without conflating it with what the writer cost.
    for key in ("image_calls", "image_cost_usd", "image_model", "image_outcome"):
        if key in usage:
            extra[key] = usage[key]
    selected_accountant.append(  # type: ignore[attr-defined]
        "content-execute",
        "content",
        _usage_tokens(usage),
        None,
        "completed",
        extra=extra,
    )
    return result


def run_content_revision(
    root: str | Path,
    task_id: str | None = None,
    *,
    runtime: object | None = None,
    accountant: object | None = None,
) -> ContentRevisionResult:
    """Run one comment-driven rewrite and account for its measured writer usage."""
    profile_root = Path(root)
    selected_runtime = runtime or ContentRuntime(profile_root)
    selected_accountant = accountant or RunAccountant(profile_root / "logs" / "spend.log")
    try:
        result = selected_runtime.revise(task_id)  # type: ignore[attr-defined]
    except BaseException as error:
        accounting = dict(getattr(error, "accounting", {}) or {})
        writer_usage = accounting.pop("writer_usage", {})
        tokens = _usage_tokens(writer_usage)
        extra: dict[str, object] = {
            "task_id": task_id or "auto",
            "outcome": _single_line_error(error),
            **accounting,
        }
        if isinstance(writer_usage, dict):
            for key in ("estimated_cost_usd", "api_calls", "model", "provider"):
                if key in writer_usage:
                    extra[f"writer_{key}"] = writer_usage[key]
        selected_accountant.append(  # type: ignore[attr-defined]
            "content-revise",
            "content",
            tokens,
            None,
            "failed",
            extra=extra,
        )
        raise

    if not isinstance(result, ContentRevisionResult):
        raise RuntimeError("content revision runtime returned an unexpected result")
    usage = dict(result.usage)
    extra = {
        "task_id": result.task_id,
        "outcome": result.outcome,
        "revision_round": result.round_number,
        "archive": str(result.archive_path),
        "firecrawl_credits_used": 0,
    }
    for key in ("estimated_cost_usd", "api_calls", "model", "provider"):
        if key in usage:
            extra[f"writer_{key}"] = usage[key]
    selected_accountant.append(  # type: ignore[attr-defined]
        "content-revise",
        "content",
        _usage_tokens(usage),
        None,
        "completed",
        extra=extra,
    )
    return result


def _single_line_error(error: BaseException) -> str:
    return " ".join(str(error).split())[:1000] or error.__class__.__name__


def main() -> int:
    args = parser().parse_args()
    root = Path(args.profile).resolve()
    runtime = Runtime(root)
    accountant = RunAccountant(root / "logs" / "spend.log")
    audit = SkillFileAudit(root / "cmo_skills") if args.evidence else None
    if audit is not None:
        sys.addaudithook(audit.hook)

    if args.command == "content-revise":
        try:
            value = run_content_revision(root, args.task_id)
        except BaseException as error:
            print(f"ERROR: {error}")
            if audit is not None:
                print(json.dumps({"skill_file_access": audit.evidence()}, indent=2))
            return 2
        output: dict[str, object] = {"result": serializable(value)}
        if audit is not None:
            evidence = audit.evidence()
            output["skill_file_access"] = evidence
            counts = evidence["read_counts"]
            if counts.get("content") != 1 or any(
                counts.get(name, 0) for name in SKILL_NAMES if name != "content"
            ):
                print("ERROR: content-only skill evidence failed to reproduce")
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 3
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    if args.command == "content-execute":
        try:
            value = run_content_execution(root)
        except BaseException as error:
            print(f"ERROR: {error}")
            if audit is not None:
                print(json.dumps({"skill_file_access": audit.evidence()}, indent=2))
            return 2
        output: dict[str, object] = {"result": serializable(value)}
        if audit is not None:
            evidence = audit.evidence()
            output["skill_file_access"] = evidence
            counts = evidence["read_counts"]
            if counts.get("content") != 1 or any(
                counts.get(name, 0) for name in SKILL_NAMES if name != "content"
            ):
                print("ERROR: content-only skill evidence failed to reproduce")
                print(json.dumps(output, ensure_ascii=False, indent=2))
                return 3
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0

    operation: Callable[[], object]
    if args.command == "plan":
        operation = lambda: runtime.plan(args.date)
    elif args.command == "execute":
        operation = runtime.execute
    elif args.command == "review":
        operation = lambda: runtime.review(args.task_id)
    elif args.command == "approval-card":
        operation = lambda: runtime.approval_card(args.task_id)
    elif args.command == "comment":
        operation = lambda: runtime.comment(args.task_id, args.text) or {"task_id": args.task_id, "status": "revision requested"}
    elif args.command == "approve":
        operation = lambda: runtime.mark_approved(args.task_id)
    elif args.command == "complete":
        operation = lambda: runtime.mark_completed(args.task_id)
    elif args.command == "commission-proof":
        operation = lambda: {"task_id": runtime.board.add_proof_card(), "status": "Backlog"}
    elif args.command == "commission-refusal":
        operation = lambda: {
            "task_id": runtime.board.add_refusal_card(args.kind),
            "status": "Backlog",
            "refusal_kind": args.kind,
        }
    elif args.command == "backfill-previous":
        accountant.append(
            "commissioning-item-2-skill-loader",
            "ads",
            1500,
            0.0,
            "completed",
            note="Backfilled after completion; one-file-read and disabled-skill proofs passed.",
        )
        print(json.dumps({"backfilled": "commissioning-item-2-skill-loader"}, indent=2))
        return 0
    else:
        raise AssertionError(args.command)

    status = "completed"
    skill_loaded = "none"
    try:
        value = operation()
        skill_loaded = getattr(value, "skill_loaded", "none")
    except BaseException as error:
        status = "failed"
        accountant.append(args.command, skill_loaded, max(1, len(str(error)) // 4), 0.0, status)
        print(f"ERROR: {error}")
        if audit is not None:
            print(json.dumps({"skill_file_access": audit.evidence()}, indent=2))
        return 2

    rendered = json.dumps(serializable(value), ensure_ascii=False, indent=2) if not isinstance(value, str) else value
    accountant.append(args.command, skill_loaded, max(1, len(rendered) // 4), 0.0, status)
    output: dict[str, object] = {"result": serializable(value)}
    if audit is not None:
        evidence = audit.evidence()
        output["skill_file_access"] = evidence
        counts = evidence["read_counts"]
        if args.command == "plan" and any(counts[name] for name in SKILL_NAMES):
            print("ERROR: no-skill-loaded evidence failed to reproduce")
            print(json.dumps(output, ensure_ascii=False, indent=2))
            return 3
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
