from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from cmo_runtime.decisions import (
    BranchMovedError,
    DecisionConflict,
    DecisionStore,
    DecisionValidationError,
)


APPROVAL_TARGET = "discord:1526833186657796153"
_PLACEHOLDERS = {"", "n/a", "na", "none", "not set", "not defined", "undecided", "tbd"}
_APPROVAL_WORDS = {"approve", "approved", "approval", "yes", "✅"}


class ApprovalCardError(RuntimeError):
    """The card cannot safely be emitted or resolved."""


@dataclass(frozen=True)
class EmissionResult:
    task_id: str
    message_id: str
    target: str


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextlib.contextmanager
def _lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _task_card(board: str, task_id: str) -> str:
    match = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", board)
    if match is None:
        raise ApprovalCardError(f"task not found: {task_id}")
    boundary = re.search(r"(?m)^### |^## ", board[match.end() :])
    end = match.end() + (boundary.start() if boundary else len(board) - match.end())
    return board[match.start() : end].strip()


def _field(card: str, name: str) -> str:
    match = re.search(rf"(?m)^- {re.escape(name)}:\s*(.*?)\s*$", card)
    return match.group(1).strip() if match else ""


def _list_field(card: str, name: str) -> list[str]:
    lines = card.splitlines()
    marker = f"- {name}:"
    for index, line in enumerate(lines):
        if line.strip() != marker:
            continue
        values: list[str] = []
        for candidate in lines[index + 1 :]:
            if candidate.startswith("  - "):
                value = candidate[4:].strip()
                if value:
                    values.append(value)
                continue
            break
        return values
    return []


def _default_sender(target: str, message: str) -> dict[str, Any]:
    from tools.send_message_tool import send_message_tool

    raw = send_message_tool({"action": "send", "target": target, "message": message})
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            raise ApprovalCardError(f"Discord sender returned invalid JSON: {error}") from error
    if isinstance(raw, dict):
        return raw
    raise ApprovalCardError("Discord sender returned an unsupported response")


def _default_media_validator(path: Path) -> bool:
    from gateway.platforms.base import BasePlatformAdapter

    expected = [(str(path), False)]
    return BasePlatformAdapter.filter_media_delivery_paths(expected) == expected


class ApprovalCardEmitter:
    def __init__(
        self,
        profile_dir: str | Path,
        *,
        sender: Callable[[str, str], dict[str, Any]] | None = None,
        media_validator: Callable[[Path], bool] | None = None,
    ) -> None:
        self.root = Path(profile_dir).resolve()
        self.tasks_path = self.root / "tasks.md"
        self.lock_path = self.root / "state" / "tasks.lock"
        self.registry_path = self.root / "state" / "approval-card.json"
        self.sender = sender or _default_sender
        self.media_validator = media_validator or _default_media_validator

    def emit(self, task_id: str) -> EmissionResult:
        with _lock(self.lock_path):
            registry = self._registry()
            active = registry.get("active")
            if isinstance(active, dict):
                raise ApprovalCardError(
                    f"approval card {active.get('task_id', 'unknown')} is already active; decide it before emitting another"
                )

            card = _task_card(self.tasks_path.read_text(encoding="utf-8"), task_id)
            if _field(card, "Status") != "Human Approval":
                raise ApprovalCardError(f"{task_id} is not in Human Approval")

            title = _field(card, "Title")
            bullets = _list_field(card, "Decision summary")
            metric = _field(card, "Metric")
            attachment_value = _field(card, "Attachment")
            is_website = _field(card, "Change type").casefold() == "website"
            commit_sha = _field(card, "Change commit")

            if metric.casefold() in _PLACEHOLDERS:
                raise ApprovalCardError("no measurable metric, no approval card")
            if not 3 <= len(bullets) <= 5:
                raise ApprovalCardError("approval card requires 3-5 decision bullets")
            if is_website and not re.fullmatch(r"[0-9a-fA-F]{7,40}", commit_sha):
                raise ApprovalCardError("approval card requires a valid Change commit")

            attachment = Path(attachment_value)
            if not attachment.is_absolute():
                attachment = self.root / attachment
            attachment = attachment.resolve()
            if not attachment.is_file():
                raise ApprovalCardError("attachment must be an existing file that Hermes can upload")
            if not self.media_validator(attachment):
                raise ApprovalCardError("attachment path is not allowed by Hermes MEDIA delivery")

            message = self._render(title, bullets, attachment, metric)
            response = self.sender(APPROVAL_TARGET, message)
            if response.get("error") or response.get("success") is False:
                raise ApprovalCardError(f"Discord delivery failed: {response.get('error') or response}")
            message_id = str(response.get("message_id") or "").strip()
            if not message_id:
                raise ApprovalCardError("Discord delivery returned no message ID")

            _atomic_json(
                self.registry_path,
                {
                    "active": {
                        "task_id": task_id,
                        "message_id": message_id,
                        "target": APPROVAL_TARGET,
                        "card_commit_sha": commit_sha,
                        "attachment": str(attachment),
                    }
                },
            )
            return EmissionResult(task_id=task_id, message_id=message_id, target=APPROVAL_TARGET)

    def _registry(self) -> dict[str, Any]:
        try:
            value = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {"active": None}
        except json.JSONDecodeError as error:
            raise ApprovalCardError(f"invalid approval-card state: {error}") from error
        if not isinstance(value, dict):
            raise ApprovalCardError("invalid approval-card state")
        return value

    @staticmethod
    def _render(title: str, bullets: list[str], attachment: Path, metric: str) -> str:
        description = "\n".join(f"  - {bullet}" for bullet in bullets)
        return "\n".join(
            (
                f"TASK NAME:    {title}",
                "DESCRIPTION:",
                description,
                f"ATTACHMENT:   {attachment.name} (attached to this Discord card)",
                f"MEDIA:{attachment}",
                f"WHAT IT HELPS: {metric}",
                "TAG:          pending",
            )
        )


class DiscordApprovalReplyHandler:
    def __init__(self, profile_dir: str | Path, *, approver_id: str) -> None:
        self.root = Path(profile_dir).resolve()
        self.approver_id = str(approver_id).strip()
        if not self.approver_id:
            raise ApprovalCardError("Discord approver ID is required")
        self.registry_path = self.root / "state" / "approval-card.json"
        self.lock_path = self.root / "state" / "tasks.lock"

    def handle(self, event: Any) -> dict[str, str] | None:
        source = getattr(event, "source", None)
        platform = getattr(source, "platform", None) if source is not None else None
        platform_name = getattr(platform, "value", platform)
        if source is None or platform_name != "discord":
            return None
        if str(getattr(source, "chat_id", "")) != APPROVAL_TARGET.split(":", 1)[1]:
            return None

        active = self._active()
        if active is None:
            return None
        if str(getattr(event, "reply_to_message_id", "")) != str(active.get("message_id", "")):
            return None
        if getattr(event, "reply_to_is_own_message", None) is False:
            return None
        if str(getattr(source, "user_id", "")) != self.approver_id:
            return {"action": "skip", "reason": "approval-card-unauthorized"}

        comment = str(getattr(event, "text", "")).strip()
        if not comment:
            return {"action": "skip", "reason": "approval-card-empty-reply"}
        decision = "approve" if comment.casefold() in _APPROVAL_WORDS else "send_back"
        reason = "" if decision == "approve" else comment
        store = DecisionStore(self.root)
        current_commit_sha = self._current_commit(str(active["task_id"]))
        try:
            store.decide(
                str(active["task_id"]),
                decision,
                approver_id=self.approver_id,
                surface="discord",
                card_commit_sha=str(active["card_commit_sha"]),
                commit_sha=current_commit_sha,
                send_back_text=reason,
            )
        except BranchMovedError:
            self._resolve_active(active, "reissue-required")
            return {"action": "skip", "reason": "approval-card-reissue-required"}
        except (DecisionConflict, DecisionValidationError):
            self._resolve_active(active, "superseded")
            return {"action": "skip", "reason": "approval-card-first-decision-won"}
        self._resolve_active(active, decision)
        return {"action": "skip", "reason": "approval-card-decided"}

    def _current_commit(self, task_id: str) -> str:
        card = _task_card((self.root / "tasks.md").read_text(encoding="utf-8"), task_id)
        return _field(card, "Change commit")

    def _active(self) -> dict[str, Any] | None:
        with _lock(self.lock_path):
            try:
                value = json.loads(self.registry_path.read_text(encoding="utf-8"))
            except FileNotFoundError:
                return None
            active = value.get("active") if isinstance(value, dict) else None
            return dict(active) if isinstance(active, dict) else None

    def _resolve_active(self, active: dict[str, Any], outcome: str) -> None:
        with _lock(self.lock_path):
            try:
                registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                registry = {}
            current = registry.get("active") if isinstance(registry, dict) else None
            if isinstance(current, dict) and current.get("message_id") == active.get("message_id"):
                registry["active"] = None
                registry["last_resolved"] = {**active, "outcome": outcome}
                _atomic_json(self.registry_path, registry)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit one manually-authorized iTarang approval card")
    parser.add_argument("task_id")
    parser.add_argument("--profile-dir", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    result = ApprovalCardEmitter(args.profile_dir).emit(args.task_id)
    print(json.dumps(result.__dict__, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
