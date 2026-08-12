from __future__ import annotations

import fcntl
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from cmo_runtime.task_file import TaskFile, TaskFileError, validate_structure


TASK_ID = re.compile(r"TASK-[0-9]+")
COMMIT_SHA = re.compile(r"[0-9a-fA-F]{7,40}")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
DECISIONS = {"approve", "send_back"}
SURFACES = {"discord", "dashboard"}


class DecisionError(RuntimeError):
    pass


class DecisionValidationError(DecisionError):
    pass


class DecisionConflict(DecisionError):
    pass


class BranchMovedError(DecisionError):
    pass


class DecisionPersistenceError(DecisionError):
    pass


@dataclass(frozen=True)
class DecisionResult:
    recorded: bool
    record: dict[str, str]


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class DecisionStore:
    """The single locked writer for human decisions from every surface."""

    def __init__(
        self,
        profile_dir: str | Path,
        *,
        timestamp: Callable[[], str] = utc_timestamp,
    ) -> None:
        self.profile_dir = Path(profile_dir)
        self.tasks_path = self.profile_dir / "tasks.md"
        self.lock_path = self.profile_dir / "state" / "tasks.lock"
        self.approvals_path = self.profile_dir / "state" / "human-approvals.json"
        self.log_path = self.profile_dir / "logs" / "approvals.log"
        self.timestamp = timestamp

    def decide(
        self,
        task_id: str,
        decision: str,
        *,
        approver_id: str,
        surface: str,
        card_commit_sha: str = "",
        commit_sha: str = "",
        send_back_text: str = "",
        publish_fingerprint: str = "",
    ) -> DecisionResult:
        """Record one human decision.

        `publish_fingerprint` is a digest of what is being approved — the article
        bytes, the diagram, and the card fields that decide where the post lands.
        Nothing here computes it and nothing here interprets it; the caller passes
        what it saw, and the publish path recomputes it later and refuses if the
        two differ. A surface that passes nothing records nothing, and a publish
        against that record fails closed rather than guessing.
        """
        task_id = task_id.strip()
        decision = decision.strip().lower().replace("-", "_").replace(" ", "_")
        approver_id = approver_id.strip()
        surface = surface.strip().lower()
        card_commit_sha = card_commit_sha.strip().lower()
        commit_sha = commit_sha.strip().lower()
        send_back_text = send_back_text.strip()
        publish_fingerprint = publish_fingerprint.strip().lower()
        if publish_fingerprint and not re.fullmatch(r"[0-9a-f]{64}", publish_fingerprint):
            raise DecisionValidationError("publish fingerprint must be a sha256 hex digest")
        self._validate_request(
            task_id,
            decision,
            approver_id,
            surface,
            card_commit_sha,
            commit_sha,
            send_back_text,
        )
        timestamp = self.timestamp()
        if not TIMESTAMP.fullmatch(timestamp):
            raise DecisionValidationError("timestamp must use YYYY-MM-DDTHH:MM:SSZ")

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            self._ensure_managed_file(self.approvals_path, "{}\n")
            self._ensure_managed_file(self.log_path, "")
            approvals = self._read_approvals()
            existing = approvals.get(task_id)
            if existing is not None:
                reason = self._existing_reason(existing)
                self._append_log_atomic(
                    self._attempt_record(
                        task_id,
                        decision,
                        approver_id,
                        surface,
                        timestamp,
                        commit_sha,
                        send_back_text,
                        outcome="refused",
                        reason=reason,
                    )
                )
                raise DecisionConflict(reason)

            board_text = self.tasks_path.read_text(encoding="utf-8")
            section = self._task_section(board_text, task_id)
            if section != "Human Approval":
                raise DecisionValidationError(
                    f"{task_id} is in {section}, not Human Approval"
                )

            is_website = self._task_field(board_text, task_id, "Change type").casefold() == "website"
            # Two shapes of website card, and they are approved at different moments.
            #
            # A card whose change already exists as a commit is approved *on that
            # commit*: the preview was built from it, so the SHAs must be there and
            # must agree. A blog card has no commit at Gate 1 — the article is
            # approved first and pushed afterwards — so there is nothing to pin it
            # to except a digest of what is being approved. Requiring a SHA there
            # made approving an article impossible; accepting neither would let a
            # card be approved with nothing identifying what was approved.
            if is_website and card_commit_sha:
                if not COMMIT_SHA.fullmatch(card_commit_sha) or not COMMIT_SHA.fullmatch(commit_sha):
                    raise DecisionValidationError(
                        "website approval requires card and decision commit SHAs"
                    )
            elif is_website and not publish_fingerprint:
                raise DecisionValidationError(
                    "a website card with no commit is approved on its artifact, which requires a "
                    "publish fingerprint"
                )

            if is_website and card_commit_sha != commit_sha:
                reason = (
                    f"branch moved from {card_commit_sha} to {commit_sha}; "
                    f"re-issue card with {commit_sha}"
                )
                event = self._attempt_record(
                    task_id,
                    decision,
                    approver_id,
                    surface,
                    timestamp,
                    commit_sha,
                    send_back_text,
                    outcome="void",
                    reason=reason,
                )
                event["card_commit_sha"] = card_commit_sha
                event["reissue_commit_sha"] = commit_sha
                self._append_log_atomic(event)
                raise BranchMovedError(reason)

            record = {
                "task_id": task_id,
                "decision": decision,
                "approver_id": approver_id,
                "surface": surface,
                "timestamp": timestamp,
                "commit_sha": commit_sha,
                "send_back_text": send_back_text,
                "publish_fingerprint": publish_fingerprint,
            }
            approvals[task_id] = record
            state_candidate = json.dumps(approvals, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            log_event: dict[str, str] = {**record, "outcome": "recorded"}
            log_candidate = self._log_candidate(log_event)
            board_candidate = self._decision_candidate(
                board_text,
                task_id,
                decision,
                approver_id,
                surface,
                timestamp,
                send_back_text,
                is_website,
            )
            self._commit_all(board_text, board_candidate, state_candidate, log_candidate)
            return DecisionResult(recorded=True, record=record)

    @staticmethod
    def _validate_request(
        task_id: str,
        decision: str,
        approver_id: str,
        surface: str,
        card_commit_sha: str,
        commit_sha: str,
        send_back_text: str,
    ) -> None:
        if not TASK_ID.fullmatch(task_id):
            raise DecisionValidationError("task ID must use TASK-<nnn>")
        if decision not in DECISIONS:
            raise DecisionValidationError("decision must be approve or send_back")
        if surface not in SURFACES:
            raise DecisionValidationError("surface must be discord or dashboard")
        if not approver_id or "\n" in approver_id or "\r" in approver_id:
            raise DecisionValidationError("approver ID must be a non-empty single line")
        if card_commit_sha and not COMMIT_SHA.fullmatch(card_commit_sha):
            raise DecisionValidationError("card commit SHA must contain 7-40 hexadecimal characters")
        if commit_sha and not COMMIT_SHA.fullmatch(commit_sha):
            raise DecisionValidationError("decision commit SHA must contain 7-40 hexadecimal characters")
        if "\n" in send_back_text or "\r" in send_back_text:
            raise DecisionValidationError("send-back text must be a single line")
        if decision == "send_back" and not send_back_text:
            raise DecisionValidationError("send-back text is required")
        if decision == "approve" and send_back_text:
            raise DecisionValidationError("approve cannot include send-back text")

    def _read_approvals(self) -> dict[str, dict[str, str]]:
        try:
            value = json.loads(self.approvals_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise DecisionPersistenceError(
                f"invalid approval state: {self.approvals_path}: {error}"
            ) from error
        if not isinstance(value, dict):
            raise DecisionPersistenceError("human approval state must be a JSON object")
        for task_id, record in value.items():
            if not isinstance(task_id, str) or not isinstance(record, dict):
                raise DecisionPersistenceError("human approval state contains a malformed record")
        return value

    @staticmethod
    def _existing_reason(existing: dict[str, str]) -> str:
        try:
            return (
                f"already decided by {existing['approver_id']} at "
                f"{existing['timestamp']} via {existing['surface']}"
            )
        except KeyError as error:
            raise DecisionPersistenceError(
                f"existing decision is missing required field: {error.args[0]}"
            ) from error

    @staticmethod
    def _attempt_record(
        task_id: str,
        decision: str,
        approver_id: str,
        surface: str,
        timestamp: str,
        commit_sha: str,
        send_back_text: str,
        *,
        outcome: str,
        reason: str,
    ) -> dict[str, str]:
        return {
            "task_id": task_id,
            "decision": decision,
            "approver_id": approver_id,
            "surface": surface,
            "timestamp": timestamp,
            "commit_sha": commit_sha,
            "send_back_text": send_back_text,
            "outcome": outcome,
            "reason": reason,
        }

    def _append_log_atomic(self, event: dict[str, str]) -> None:
        candidate = self._log_candidate(event)
        TaskFile(self.log_path, lock_path=self.lock_path)._atomic_write(candidate)
        if self.log_path.read_text(encoding="utf-8") != candidate:
            raise DecisionPersistenceError("approval log verification failed")

    def _log_candidate(self, event: dict[str, str]) -> str:
        original = self.log_path.read_text(encoding="utf-8")
        separator = "" if not original or original.endswith("\n") else "\n"
        return original + separator + json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"

    def _decision_candidate(
        self,
        board_text: str,
        task_id: str,
        decision: str,
        approver_id: str,
        surface: str,
        timestamp: str,
        send_back_text: str,
        is_website: bool,
    ) -> str:
        task_file = TaskFile(self.tasks_path, lock_path=self.lock_path)
        if decision == "send_back":
            target_section = "Backlog"
            change_status = "revision requested"
            latest_summary = f"Human send-back: {send_back_text}"
        elif is_website:
            target_section = "Human Approval"
            change_status = "awaiting Gate 2"
            latest_summary = "Human approved Gate 1 preview; awaiting human production merge and live evidence."
        else:
            target_section = "Completed"
            change_status = "completed"
            latest_summary = "Human approved; non-website work completed."
        candidate = task_file._moved_board(board_text, task_id, target_section, timestamp)
        heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", candidate)
        if heading is None:
            raise TaskFileError(f"task not found after move: {task_id}")
        boundary = re.search(r"(?m)^### |^## ", candidate[heading.end() :])
        end = heading.end() + (
            boundary.start() if boundary is not None else len(candidate) - heading.end()
        )
        card = candidate[heading.start() : end].strip()
        for name, value in (
            ("Change status", change_status),
            ("Human decision", "approve" if decision == "approve" else "send back"),
            ("Human decision by", approver_id),
            ("Human decision at", timestamp),
            ("Human decision surface", surface),
            ("Human decision comment", send_back_text or "Approved without comment."),
            (
                "Latest summary",
                latest_summary,
            ),
        ):
            card = task_file._set_board_field(card, name, value)
        if decision == "approve" and not is_website:
            card = task_file._set_board_field(card, "Completed date", timestamp)
        card = task_file._set_board_field(card, "Last updated", timestamp)
        card = task_file._set_board_field(card, "Updated", timestamp)
        candidate = candidate[: heading.start()] + card + "\n\n" + candidate[end:]
        issues = task_file._validate_candidate(candidate)
        if issues:
            detail = "; ".join(issue.message for issue in issues)
            raise TaskFileError(f"decision would make tasks.md invalid: {detail}")
        return candidate

    def _commit_all(
        self,
        board_original: str,
        board_candidate: str,
        state_candidate: str,
        log_candidate: str,
    ) -> None:
        originals = {
            self.tasks_path: board_original,
            self.approvals_path: self.approvals_path.read_text(encoding="utf-8"),
            self.log_path: self.log_path.read_text(encoding="utf-8"),
        }
        candidates = {
            self.tasks_path: board_candidate,
            self.approvals_path: state_candidate,
            self.log_path: log_candidate,
        }
        helpers = {
            path: TaskFile(path, lock_path=self.lock_path)
            for path in originals
        }
        changed: list[Path] = []
        try:
            for path in (self.tasks_path, self.approvals_path, self.log_path):
                if candidates[path] == originals[path]:
                    continue
                helpers[path]._atomic_write(candidates[path])
                changed.append(path)
                if path.read_text(encoding="utf-8") != candidates[path]:
                    raise DecisionPersistenceError(f"decision verification failed for {path}")
            if validate_structure(self.tasks_path):
                raise DecisionPersistenceError("decision left tasks.md structurally invalid")
        except BaseException as error:
            rollback_errors: list[str] = []
            for path in reversed(changed):
                try:
                    helpers[path]._atomic_write(originals[path])
                    if path.read_text(encoding="utf-8") != originals[path]:
                        raise OSError("restored content did not verify")
                except BaseException as rollback_error:
                    rollback_errors.append(f"{path}: {rollback_error}")
            if rollback_errors:
                raise DecisionPersistenceError(
                    f"decision failed ({error}); rollback failed: {'; '.join(rollback_errors)}"
                ) from error
            raise

    @staticmethod
    def _task_section(board_text: str, task_id: str) -> str:
        current_section = ""
        for line in board_text.splitlines():
            section = re.fullmatch(r"## (.+)", line)
            if section:
                current_section = section.group(1)
                continue
            if re.fullmatch(rf"### {re.escape(task_id)}(?:\s+—\s+.*?)?", line):
                return current_section
        raise DecisionValidationError(f"task not found: {task_id}")

    @staticmethod
    def _task_field(board_text: str, task_id: str, name: str) -> str:
        heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", board_text)
        if heading is None:
            raise DecisionValidationError(f"task not found: {task_id}")
        boundary = re.search(r"(?m)^### |^## ", board_text[heading.end() :])
        end = heading.end() + (
            boundary.start() if boundary is not None else len(board_text) - heading.end()
        )
        card = board_text[heading.start() : end]
        field = re.search(rf"(?m)^- {re.escape(name)}:\s*(.*?)\s*$", card)
        return field.group(1).strip() if field is not None else ""

    @staticmethod
    def _ensure_managed_file(path: Path, initial: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return
        try:
            os.write(descriptor, initial.encode("utf-8"))
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def decision_record(profile_dir: str | Path, task_id: str) -> dict[str, str] | None:
    """Read the single DecisionStore state without creating another approval source."""
    if not TASK_ID.fullmatch(task_id):
        raise DecisionValidationError("task ID must use TASK-<nnn>")
    path = Path(profile_dir) / "state" / "human-approvals.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as error:
        raise DecisionPersistenceError(f"invalid approval state: {path}: {error}") from error
    if not isinstance(value, dict):
        raise DecisionPersistenceError("human approval state must be a JSON object")
    record = value.get(task_id)
    if record is None:
        return None
    if not isinstance(record, dict):
        raise DecisionPersistenceError(f"human approval state contains a malformed record for {task_id}")
    return {str(name): str(field) for name, field in record.items()}


def is_approved(profile_dir: str | Path, task_id: str) -> bool:
    """Return true only for an approval recorded by DecisionStore."""
    record = decision_record(profile_dir, task_id)
    return record is not None and record.get("decision") == "approve"


def is_decided(profile_dir: str | Path, task_id: str) -> bool:
    """Return true after any first-writer-wins human decision."""
    return decision_record(profile_dir, task_id) is not None
