from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, TypeVar

from cmo_runtime.skill_loader import DisabledSkillError, SkillLoader
from cmo_runtime.task_file import (
    ActiveTaskError,
    BOARD_SECTIONS,
    TaskFile,
    TaskFileError,
    utc_timestamp,
    validate_structure,
)


class AuthorityError(TaskFileError):
    pass


class MetricRequiredError(TaskFileError):
    pass


@dataclass(frozen=True)
class BoardCard:
    task_id: str
    section: str
    text: str
    fields: dict[str, str]

    def field(self, name: str, default: str = "") -> str:
        return self.fields.get(name, default).strip()


@dataclass(frozen=True)
class PlanResult:
    date: str
    created: list[str]
    reason: str
    top_three: list[dict[str, str]]
    review_count: int
    backlog_count: int


@dataclass(frozen=True)
class ExecuteResult:
    task_id: str
    status: str
    skill_loaded: str
    artifact: str | None
    reason: str


@dataclass(frozen=True)
class ReviewResult:
    task_id: str
    outcome: str
    reason: str
    approval_card: str | None
    cold_context_evidence: dict[str, object]


def parse_cards(text: str) -> list[BoardCard]:
    section_matches = list(re.finditer(r"(?m)^## (Backlog|In Progress|CMO Review|Human Approval|Completed)\s*$", text))
    cards: list[BoardCard] = []
    for index, section_match in enumerate(section_matches):
        section = section_match.group(1)
        section_start = section_match.end()
        section_end = section_matches[index + 1].start() if index + 1 < len(section_matches) else len(text)
        section_text = text[section_start:section_end]
        headings = list(re.finditer(r"(?m)^### (TASK-\d+)(?:\s+—\s+.*?)?\s*$", section_text))
        for card_index, heading in enumerate(headings):
            card_start = heading.start()
            card_end = headings[card_index + 1].start() if card_index + 1 < len(headings) else len(section_text)
            card_text = section_text[card_start:card_end].strip()
            fields: dict[str, str] = {}
            for match in re.finditer(r"(?m)^- ([^:\n]+):\s*(.*)$", card_text):
                fields.setdefault(match.group(1), match.group(2))
            title_match = re.match(r"^### TASK-\d+(?:\s+—\s+(.*))?$", card_text.splitlines()[0])
            if "Title" not in fields and title_match and title_match.group(1):
                fields["Title"] = title_match.group(1)
            cards.append(BoardCard(heading.group(1), section, card_text, fields))
    return cards


def decision_bullets(artifact: str) -> list[str]:
    lines = artifact.splitlines()
    start = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().lower() in {
                "decision bullets:",
                "## decision bullets",
                "## decision bullets:",
            }
        ),
        None,
    )
    if start is None:
        return []
    bullets: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
        elif stripped and bullets:
            break
    return bullets


def render_approval_card(card: BoardCard, artifact_path: str, artifact: str) -> str:
    metric = card.field("Metric")
    if not metric or metric.lower() in {"none", "n/a", "unknown"}:
        raise MetricRequiredError(f"{card.task_id}: approval card requires a measurable Metric")
    bullets = decision_bullets(artifact)
    if not 3 <= len(bullets) <= 5:
        raise TaskFileError(f"{card.task_id}: approval card requires 3–5 decision bullets")
    description = "\n".join(f"  - {bullet}" for bullet in bullets)
    return (
        f"TASK NAME:    {card.field('Title')}\n"
        f"DESCRIPTION:\n{description}\n"
        f"ATTACHMENT:   {artifact_path}\n"
        f"METRIC:       {metric}\n"
        "TAG:          pending"
    )


class BoardStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.path = root / "tasks.md"
        self.task_file = TaskFile(self.path, lock_path=root / "state" / "tasks.lock")

    def cards(self) -> list[BoardCard]:
        return parse_cards(self.path.read_text(encoding="utf-8"))

    def get(self, task_id: str) -> BoardCard:
        card = next((item for item in self.cards() if item.task_id == task_id), None)
        if card is None:
            raise TaskFileError(f"task not found: {task_id}")
        return card

    def mutate(
        self,
        task_id: str,
        *,
        target_section: str | None = None,
        updates: dict[str, str] | None = None,
        updated: str | None = None,
    ) -> None:
        if target_section is not None and target_section not in BOARD_SECTIONS:
            raise TaskFileError(f"invalid target section: {target_section}")
        timestamp = updated or utc_timestamp()
        updates = dict(updates or {})
        for name, value in updates.items():
            if not value or "\n" in value or "\r" in value:
                raise TaskFileError(f"{name} must be a non-empty single line")

        lock_path = self.root / "state" / "tasks.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.touch(exist_ok=True)
        with lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", original)
            if heading is None:
                raise TaskFileError(f"task not found: {task_id}")
            boundary = re.search(r"(?m)^### |^## ", original[heading.end() :])
            end = heading.end() + (boundary.start() if boundary else len(original) - heading.end())
            card = original[heading.start() : end].strip()
            for name, value in updates.items():
                card = self.task_file._set_board_field(card, name, value)
            card = self.task_file._set_board_field(card, "Last updated", timestamp)
            card = self.task_file._set_board_field(card, "Updated", timestamp)
            candidate = original[: heading.start()] + card + "\n\n" + original[end:]
            if target_section is not None:
                candidate = self.task_file._moved_board(candidate, task_id, target_section, timestamp)
            issues = self.task_file._validate_candidate(candidate)
            if issues:
                raise TaskFileError("mutation would make tasks.md invalid: " + "; ".join(issue.message for issue in issues))
            self.task_file._atomic_write(candidate)
            if self.path.read_text(encoding="utf-8") != candidate or validate_structure(self.path):
                self.task_file._atomic_write(original)
                raise TaskFileError("mutation verification failed; original tasks.md restored")

    def add_proof_card(self) -> str:
        lock_path = self.root / "state" / "tasks.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.touch(exist_ok=True)
        with lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            highest = max((int(value) for value in re.findall(r"(?m)^### TASK-(\d+)", original)), default=65)
            task_id = f"TASK-{highest + 1:03d}"
            timestamp = utc_timestamp()
            card = f"""### {task_id} — Produce a verified internal board-state summary

- ID: {task_id}
- Title: Produce a verified internal board-state summary
- Owner: content
- Priority: critical
- Status: Backlog
- Start date: {timestamp[:10]}
- Completed date: not completed
- Objective: Produce a non-marketing, tool-free written summary from tasks.md alone.
- Acceptance criteria:
  - Report current counts for every lifecycle lane.
  - Cite tasks.md as the only source.
  - Include three business-readable decision bullets.
- Latest summary: Commissioning proof task; no marketing work is authorized.
- Last updated: {timestamp}
- Skill: content
- Description: Produce a non-marketing, tool-free written summary from tasks.md alone.
- Attachment: none
- Metric: One verified summary covering all five lifecycle lanes.
- Tag: action to be taken by: cmo
- Updated: {timestamp}
- Change status: commissioning proof
- Work type: internal-board-summary
- Required tool: none
- KPI gate: not-required"""
            marker = "## Backlog\n"
            insert_at = original.find(marker)
            if insert_at < 0:
                raise TaskFileError("Backlog section not found")
            insert_at += len(marker)
            candidate = original[:insert_at] + "\n" + card + "\n\n" + original[insert_at:]
            issues = self.task_file._validate_candidate(candidate)
            if issues:
                raise TaskFileError("proof card would make tasks.md invalid: " + "; ".join(issue.message for issue in issues))
            self.task_file._atomic_write(candidate)
            if self.path.read_text(encoding="utf-8") != candidate or validate_structure(self.path):
                self.task_file._atomic_write(original)
                raise TaskFileError("proof-card verification failed; original tasks.md restored")
            return task_id

    def add_refusal_card(self, kind: str) -> str:
        if kind == "tool":
            title = "Commission unavailable-tool refusal"
            skill = "content"
            required_tool = "unavailable-tool"
            kpi_gate = "approved"
            metric = "One unavailable-tool task blocked without a fabricated artifact."
        elif kind == "kpi":
            title = "Commission unapproved-KPI refusal"
            skill = "seo"
            required_tool = "none"
            kpi_gate = "pending"
            metric = "One task held for a human KPI decision without guessing."
        else:
            raise TaskFileError(f"unknown refusal kind: {kind}")

        lock_path = self.root / "state" / "tasks.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.touch(exist_ok=True)
        with lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            highest = max((int(value) for value in re.findall(r"(?m)^### TASK-(\d+)", original)), default=65)
            task_id = f"TASK-{highest + 1:03d}"
            timestamp = utc_timestamp()
            card = f"""### {task_id} — {title}

- ID: {task_id}
- Title: {title}
- Owner: {skill}
- Priority: critical
- Status: Backlog
- Start date: {timestamp[:10]}
- Completed date: not completed
- Objective: Verify the runtime refuses work when a required gate is unavailable.
- Acceptance criteria:
  - No work artifact is fabricated.
  - The refusal reason is written to this card.
- Latest summary: Commissioning refusal task; no domain work is authorized.
- Last updated: {timestamp}
- Skill: {skill}
- Description: Verify a required execution gate fails closed.
- Attachment: none
- Metric: {metric}
- Tag: action to be taken by: cmo
- Updated: {timestamp}
- Change status: commissioning proof
- Work type: internal-board-summary
- Required tool: {required_tool}
- KPI gate: {kpi_gate}"""
            marker = "## Backlog\n"
            insert_at = original.find(marker)
            if insert_at < 0:
                raise TaskFileError("Backlog section not found")
            insert_at += len(marker)
            candidate = original[:insert_at] + "\n" + card + "\n\n" + original[insert_at:]
            issues = self.task_file._validate_candidate(candidate)
            if issues:
                raise TaskFileError("refusal card would make tasks.md invalid: " + "; ".join(issue.message for issue in issues))
            self.task_file._atomic_write(candidate)
            if self.path.read_text(encoding="utf-8") != candidate or validate_structure(self.path):
                self.task_file._atomic_write(original)
                raise TaskFileError("refusal-card verification failed; original tasks.md restored")
            return task_id


class Runtime:
    def __init__(self, root: str | Path, *, skill_loader: SkillLoader | None = None) -> None:
        self.root = Path(root)
        self.board = BoardStore(self.root)
        self.skill_loader = skill_loader or SkillLoader(self.root / "cmo_skills")
        self.artifact_dir = self.root / "artifacts"

    def plan(self, date: str | None = None) -> PlanResult:
        cards = self.board.cards()
        reviews = [card for card in cards if card.section == "CMO Review"]
        backlog = [card for card in cards if card.section == "Backlog" and card.field("Change status") != "commissioning"]
        if reviews:
            top = [
                {"task_id": card.task_id, "reason": "Ready for independent CMO review before new work is created."}
                for card in reviews[:3]
            ]
            reason = f"clear the CMO Review queue ({len(reviews)} cards) before planning new work; no cards were created."
        else:
            top = [
                {"task_id": card.task_id, "reason": "Highest existing Backlog priority; no duplicate work was created."}
                for card in backlog[:3]
            ]
            reason = "Use the existing Backlog in its current priority order; no cards were created."
        return PlanResult(
            date=date or datetime.now(UTC).date().isoformat(),
            created=[],
            reason=reason,
            top_three=top,
            review_count=len(reviews),
            backlog_count=len(backlog),
        )

    def execute(self) -> ExecuteResult:
        cards = self.board.cards()
        active = next((card for card in cards if card.section == "In Progress"), None)
        backlog = [card for card in cards if card.section == "Backlog"]
        if active is not None:
            attempted = backlog[0].task_id if backlog else "no queued task"
            raise ActiveTaskError(f"{active.task_id} is already in In Progress; {attempted} cannot enter In Progress")
        if not backlog:
            raise TaskFileError("no Backlog task is available")
        card = backlog[0]
        self.board.mutate(card.task_id, target_section="In Progress", updates={"Change status": "executing"})
        loaded_skill = "none"
        try:
            loaded = self.skill_loader.load(card.field("Skill") or card.field("Owner"))
            loaded_skill = loaded.name
        except DisabledSkillError as error:
            self.board.mutate(
                card.task_id,
                target_section="Backlog",
                updates={"Change status": "blocked", "Latest summary": str(error)},
            )
            return ExecuteResult(card.task_id, "blocked", loaded_skill, None, str(error))

        card = self.board.get(card.task_id)
        required_tool = card.field("Required tool", "none")
        if required_tool.lower() != "none":
            reason = f"blocked — {required_tool} not connected; no output was fabricated"
            self.board.mutate(
                card.task_id,
                target_section="Backlog",
                updates={"Change status": "blocked", "Latest summary": reason},
            )
            return ExecuteResult(card.task_id, "blocked", loaded_skill, None, reason)
        if card.field("KPI gate", "pending").lower() not in {"approved", "not-required"}:
            reason = "pending human decision — KPI set is not approved; no KPI was guessed"
            self.board.mutate(
                card.task_id,
                target_section="Backlog",
                updates={"Change status": "pending human decision", "Latest summary": reason},
            )
            return ExecuteResult(card.task_id, "pending human decision", loaded_skill, None, reason)
        if card.field("Work type") != "internal-board-summary":
            reason = "blocked — no connected executor exists for this work type; no output was fabricated"
            self.board.mutate(
                card.task_id,
                target_section="Backlog",
                updates={"Change status": "blocked", "Latest summary": reason},
            )
            return ExecuteResult(card.task_id, "blocked", loaded_skill, None, reason)

        counts = {section: 0 for section in BOARD_SECTIONS}
        for item in self.board.cards():
            counts[item.section] += 1
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = self.artifact_dir / f"{card.task_id}-{loaded_skill}.md"
        artifact = (
            f"# {card.field('Title')}\n\n"
            "Source: tasks.md only.\n\n"
            "## Lifecycle lane counts\n\n"
            + "\n".join(f"- {section}: {counts[section]}" for section in BOARD_SECTIONS)
            + "\n\nDecision bullets:\n"
            "- The board summary uses tasks.md as its only evidence source.\n"
            "- All five lifecycle lanes are counted so queue pressure is visible.\n"
            "- No marketing content, external tool result, publication, or spend is produced.\n"
        )
        artifact_path.write_text(artifact, encoding="utf-8")
        self.board.mutate(
            card.task_id,
            target_section="CMO Review",
            updates={
                "Attachment": str(artifact_path),
                "Tag": "action to be taken by: cmo",
                "Change status": "pending CMO review",
                "Latest summary": "Internal board-state summary produced from tasks.md alone; pending cold-context CMO review.",
            },
        )
        return ExecuteResult(card.task_id, "pending CMO review", loaded_skill, str(artifact_path), "artifact produced")

    def review(self, task_id: str) -> ReviewResult:
        card = self.board.get(task_id)
        if card.section != "CMO Review" and not (
            card.section == "In Progress" and "requires a DECISION SUMMARY" in card.field("Latest summary")
        ):
            raise TaskFileError(f"{task_id} is not eligible for CMO review")
        artifact_path = card.field("Attachment")
        artifact = ""
        if artifact_path and artifact_path.lower() != "none":
            try:
                artifact = Path(artifact_path).read_text(encoding="utf-8")
            except OSError:
                artifact = ""
        payload = {"card": {"task_id": card.task_id, "fields": card.fields}, "artifact": artifact}
        completed = subprocess.run(
            [sys.executable, "-m", "cmo_runtime.review_worker"],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise TaskFileError(f"cold review worker failed: {completed.stderr.strip() or completed.stdout.strip()}")
        decision = json.loads(completed.stdout)
        outcome = decision["outcome"]
        reason = decision["reason"]
        approval: str | None = None
        if outcome == "send-back":
            self.board.mutate(
                task_id,
                target_section="Backlog",
                updates={
                    "Change status": "revision requested",
                    "Review comment": reason,
                    "Latest summary": f"CMO review send-back: {reason}",
                },
            )
        elif outcome == "flag":
            self.board.mutate(
                task_id,
                updates={"Change status": "pending human decision", "Review comment": reason},
            )
        elif outcome == "escalate":
            approval = render_approval_card(card, artifact_path, artifact)
            self.board.mutate(
                task_id,
                target_section="Human Approval",
                updates={"Change status": "pending human approval", "Latest summary": "CMO review complete; pending human approval."},
            )
        else:
            raise TaskFileError(f"cold review worker returned invalid outcome: {outcome}")
        return ReviewResult(task_id, outcome, reason, approval, decision["evidence"])

    def approval_card(self, task_id: str) -> str:
        card = self.board.get(task_id)
        artifact_path = card.field("Attachment")
        try:
            artifact = Path(artifact_path).read_text(encoding="utf-8")
        except OSError as error:
            raise TaskFileError(f"{task_id}: attachment cannot be opened: {error}") from error
        return render_approval_card(card, artifact_path, artifact)

    def comment(self, task_id: str, comment: str) -> None:
        if not comment or "\n" in comment or "\r" in comment:
            raise TaskFileError("human comment must be a non-empty single line")
        self.board.mutate(
            task_id,
            target_section="Backlog",
            updates={
                "Change status": "revision requested",
                "Human decision": "rejected",
                "Human decision comment": comment,
                "Latest summary": f"Human comment treated as rejection: {comment}",
            },
        )

    @staticmethod
    def mark_approved(task_id: str) -> None:
        raise AuthorityError(f"Only a human may mark {task_id} approved")

    @staticmethod
    def mark_completed(task_id: str) -> None:
        raise AuthorityError(f"CMO runtime cannot mark tasks completed; {task_id} requires human authority and completion evidence")


T = TypeVar("T")


class RunAccountant:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    def run(self, run_type: str, skill_loaded: str, operation: Callable[[], T]) -> T:
        status = "completed"
        result: T | None = None
        error: BaseException | None = None
        try:
            result = operation()
        except BaseException as caught:
            status = "failed"
            error = caught
        outcome_text = repr(result) if error is None else str(error)
        self.append(run_type, skill_loaded, max(1, len(outcome_text) // 4), 0.0, status)
        if error is not None:
            raise error
        return result  # type: ignore[return-value]

    def append(
        self,
        run_type: str,
        skill_loaded: str,
        approximate_tokens: int,
        approximate_cost_inr: float | None,
        status: str,
        *,
        note: str | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        entry: dict[str, object] = {
            "record_type": "run",
            "date": datetime.now(UTC).isoformat(),
            "run_type": run_type,
            "skill_loaded": skill_loaded,
            "approximate_tokens": approximate_tokens,
            "approximate_cost_inr": approximate_cost_inr,
            "status": status,
        }
        if note:
            entry["note"] = note
        if extra:
            overlap = set(entry).intersection(extra)
            if overlap:
                raise RuntimeError(
                    "extra spend fields cannot replace core fields: "
                    + ", ".join(sorted(overlap))
                )
            entry.update(extra)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
