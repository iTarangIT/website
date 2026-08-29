from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import stat
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator, TextIO

SKILLS = {"seo", "content", "social", "ads", "ops"}
STATUSES = {
    "queued",
    "in-progress",
    "pending CMO review",
    "pending human approval",
    "approved",
    "rejected",
    "blocked",
    "pending human decision",
}
OPEN_STATUSES = STATUSES - {"approved", "rejected"}
TASK_HEADING = re.compile(r"^### TASK-(\d+)$")
BOARD_TASK_HEADING = re.compile(r"^### (TASK-\d+)(?:\s+—\s+.*)?$")
TASK_ID_FLOOR = re.compile(r"^TASK-(\d+)$")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
BOARD_SECTIONS = ("Backlog", "In Progress", "CMO Review", "Human Approval", "Completed")


class TaskFileError(ValueError):
    pass


class ActiveTaskError(TaskFileError):
    pass


@dataclass(frozen=True)
class Task:
    title: str
    skill: str
    description: str
    attachment: str
    metric: str
    status: str
    tag: str


@dataclass(frozen=True)
class TaskRecord(Task):
    task_id: str
    updated: str


@dataclass(frozen=True)
class ReadResult:
    tasks: list[TaskRecord]
    lines_read: int
    reached_eof: bool


@dataclass(frozen=True)
class ValidationIssue:
    line: int
    code: str
    message: str


def card_count_floor(path: str | Path) -> int:
    """The fewest cards this board may hold, or 0 when no floor is recorded.

    Companion to `tasks.id-floor`, and for the same reason: some facts about the
    board cannot be derived from the board. Structural validation asks "is this
    well-formed", and a board with cards deleted off the end is perfectly
    well-formed — which is how four of them vanished without a single check
    objecting. The floor is what makes a shrinking board a detectable event.

    Archiving completed work legitimately lowers it, so it is a file a human edits,
    not a number the code raises behind their back.
    """
    floor_path = Path(path).with_name("tasks.card-floor")
    try:
        value = floor_path.read_text(encoding="ascii").strip()
    except OSError:
        return 0
    if not value.isdigit():
        raise TaskFileError(f"invalid card floor in {floor_path}: expected a whole number")
    return int(value)


def validate_structure(path: str | Path) -> list[ValidationIssue]:
    """Return every section, status, mirrored-field and card-count inconsistency."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    issues: list[ValidationIssue] = []
    seen_sections: dict[str, int] = {}
    current_section: str | None = None
    current_section_index = -1
    cards: list[dict[str, object]] = []
    current_card: dict[str, object] | None = None

    def finish_card() -> None:
        nonlocal current_card
        if current_card is not None:
            cards.append(current_card)
            current_card = None

    for line_number, line in enumerate(lines, start=1):
        section_match = re.fullmatch(r"## (.+)", line)
        if section_match:
            finish_card()
            name = section_match.group(1)
            if name not in BOARD_SECTIONS:
                current_section = None
                continue
            if name in seen_sections:
                issues.append(
                    ValidationIssue(
                        line_number,
                        "duplicate-section",
                        f"duplicate ## {name}; first declared at line {seen_sections[name]}",
                    )
                )
            else:
                seen_sections[name] = line_number
            section_index = BOARD_SECTIONS.index(name)
            if section_index < current_section_index:
                issues.append(
                    ValidationIssue(line_number, "section-order", f"## {name} is out of lifecycle order")
                )
            current_section_index = max(current_section_index, section_index)
            current_section = name
            continue

        task_match = BOARD_TASK_HEADING.fullmatch(line)
        if task_match:
            finish_card()
            current_card = {
                "task_id": task_match.group(1),
                "line": line_number,
                "section": current_section,
                "fields": {},
                "all_fields": {},
            }
            if current_section is None:
                issues.append(
                    ValidationIssue(
                        line_number,
                        "task-outside-section",
                        f"{task_match.group(1)} is outside a lifecycle section",
                    )
                )
            continue

        if current_card is not None:
            any_field_match = re.fullmatch(r"- ([^:]+):\s*(.*)", line)
            if any_field_match:
                all_fields = current_card["all_fields"]
                assert isinstance(all_fields, dict)
                field_name = any_field_match.group(1)
                if field_name in all_fields:
                    issues.append(
                        ValidationIssue(
                            line_number,
                            "duplicate-field",
                            f"{current_card['task_id']}: duplicate {field_name}; first declared at line {all_fields[field_name]}",
                        )
                    )
                else:
                    all_fields[field_name] = line_number
            field_match = re.fullmatch(
                r"- (Status|Owner|Skill|Last updated|Updated):\s*(.*)", line
            )
            if field_match:
                fields = current_card["fields"]
                assert isinstance(fields, dict)
                fields[field_match.group(1)] = (field_match.group(2), line_number)

    finish_card()

    task_lines: dict[str, int] = {}
    in_progress_count = 0
    for card in cards:
        task_id = str(card["task_id"])
        line_number = int(card["line"])
        section = card["section"]
        fields = card["fields"]
        assert isinstance(fields, dict)
        if section == "In Progress":
            in_progress_count += 1
            if in_progress_count > 1:
                issues.append(
                    ValidationIssue(
                        line_number,
                        "multiple-in-progress",
                        f"{task_id}: only one card may be in ## In Progress",
                    )
                )
        if task_id in task_lines:
            issues.append(
                ValidationIssue(
                    line_number,
                    "duplicate-task",
                    f"duplicate {task_id}; first declared at line {task_lines[task_id]}",
                )
            )
        else:
            task_lines[task_id] = line_number

        status = fields.get("Status")
        if status is None:
            issues.append(
                ValidationIssue(line_number, "missing-status", f"{task_id} has no Status field")
            )
        elif section is not None and status[0] != section:
            issues.append(
                ValidationIssue(
                    int(status[1]),
                    "section-status",
                    f"{task_id}: section is {section!r} but Status is {status[0]!r}",
                )
            )

        for left, right, code in (
            ("Owner", "Skill", "owner-skill"),
            ("Last updated", "Updated", "updated-mirror"),
        ):
            left_value = fields.get(left)
            right_value = fields.get(right)
            if left_value is not None and right_value is not None and left_value[0] != right_value[0]:
                issues.append(
                    ValidationIssue(
                        int(right_value[1]),
                        code,
                        f"{task_id}: {left} is {left_value[0]!r} but {right} is {right_value[0]!r}",
                    )
                )

    floor = card_count_floor(path)
    if floor and len(cards) < floor:
        issues.append(
            ValidationIssue(
                len(lines) or 1,
                "card-count",
                f"the board holds {len(cards)} cards; tasks.card-floor requires at least {floor}. "
                "Cards have been lost, or the floor needs lowering after an archive.",
            )
        )

    return sorted(issues, key=lambda issue: (issue.line, issue.code))


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_single_line(name: str, value: str) -> None:
    if not value or "\n" in value or "\r" in value:
        raise TaskFileError(f"{name} must be a non-empty single line")


def _validate_task(task: Task) -> None:
    for name in ("title", "description", "attachment", "metric", "tag"):
        _validate_single_line(name, getattr(task, name))
    if task.skill not in SKILLS:
        raise TaskFileError(f"invalid skill: {task.skill}")
    if task.status not in STATUSES:
        raise TaskFileError(f"invalid status: {task.status}")


def _validate_timestamp(value: str) -> None:
    if not TIMESTAMP.fullmatch(value):
        raise TaskFileError("timestamp must use YYYY-MM-DDTHH:MM:SSZ")


def _field(line: str, prefix: str) -> str:
    if not line.startswith(prefix):
        raise TaskFileError(f"expected {prefix.rstrip()}")
    return line[len(prefix) :].rstrip()


def _read_record(first_line: str, stream: TextIO, line_counter: list[int]) -> TaskRecord:
    match = TASK_HEADING.fullmatch(first_line.rstrip("\n"))
    if not match:
        raise TaskFileError(f"invalid task heading: {first_line.rstrip()}")

    lines: list[str] = []
    for _ in range(8):
        line = stream.readline()
        if not line:
            raise TaskFileError(f"truncated TASK-{int(match.group(1)):03d}")
        line_counter[0] += 1
        lines.append(line.rstrip("\n"))

    record = TaskRecord(
        task_id=f"TASK-{int(match.group(1)):03d}",
        title=_field(lines[0], "TITLE:        "),
        skill=_field(lines[1], "SKILL:        "),
        description=_field(lines[2], "DESCRIPTION:  "),
        attachment=_field(lines[3], "ATTACHMENT:   "),
        metric=_field(lines[4], "METRIC:       "),
        status=_field(lines[5], "STATUS:       "),
        tag=_field(lines[6], "TAG:          "),
        updated=_field(lines[7], "UPDATED:      "),
    )
    _validate_task(
        Task(
            title=record.title,
            skill=record.skill,
            description=record.description,
            attachment=record.attachment,
            metric=record.metric,
            status=record.status,
            tag=record.tag,
        )
    )
    _validate_timestamp(record.updated)
    return record


class TaskFile:
    def __init__(
        self,
        path: str | Path,
        id_floor_path: str | Path | None = None,
        lock_path: str | Path | None = None,
    ) -> None:
        self.path = Path(path)
        self.id_floor_path = (
            Path(id_floor_path)
            if id_floor_path is not None
            else self.path.with_name("tasks.id-floor")
        )
        self.lock_path = (
            Path(lock_path)
            if lock_path is not None
            else self.path.parent / "state" / "tasks.lock"
        )
        self.id_floor = self._read_id_floor()

    def _records(self) -> Iterator[TaskRecord]:
        with self.path.open("r", encoding="utf-8") as stream:
            line_counter = [0]
            while True:
                line = stream.readline()
                if not line:
                    return
                line_counter[0] += 1
                if not line.strip():
                    continue
                yield _read_record(line, stream, line_counter)

    def next_id(self) -> str:
        highest = max(self.id_floor, self._highest_id(self.path))
        return f"TASK-{highest + 1:03d}"

    def _read_id_floor(self) -> int:
        if not self.id_floor_path.exists():
            return 0
        value = self.id_floor_path.read_text(encoding="ascii").strip()
        match = TASK_ID_FLOOR.fullmatch(value)
        if not match:
            raise TaskFileError(
                f"invalid task ID floor in {self.id_floor_path}: expected TASK-<nnn>"
            )
        return int(match.group(1))

    @staticmethod
    def _highest_id(path: Path) -> int:
        highest = 0
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                match = TASK_HEADING.fullmatch(line.rstrip("\r\n"))
                if match:
                    highest = max(highest, int(match.group(1)))
        return highest

    def add(self, task: Task, *, updated: str | None = None) -> str:
        _validate_task(task)
        timestamp = updated or utc_timestamp()
        _validate_timestamp(timestamp)
        if task.status == "in-progress":
            active = self._active_task_id()
            if active:
                raise ActiveTaskError(
                    f"{active} is already in-progress; a new task cannot enter in-progress"
                )
        task_id = self.next_id()
        record = self._render(task_id, task, timestamp)
        needs_separator = self.path.stat().st_size > 0
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            if needs_separator:
                stream.write("\n")
            stream.write(record)
        return task_id

    def top_open(self, limit: int) -> ReadResult:
        if limit < 0:
            raise TaskFileError("limit cannot be negative")
        if limit == 0:
            return ReadResult(tasks=[], lines_read=0, reached_eof=False)

        tasks: list[TaskRecord] = []
        lines_read = [0]
        with self.path.open("r", encoding="utf-8") as stream:
            while len(tasks) < limit:
                line = stream.readline()
                if not line:
                    return ReadResult(tasks=tasks, lines_read=lines_read[0], reached_eof=True)
                lines_read[0] += 1
                if not line.strip():
                    continue
                record = _read_record(line, stream, lines_read)
                if record.status in OPEN_STATUSES:
                    tasks.append(record)
        return ReadResult(tasks=tasks, lines_read=lines_read[0], reached_eof=False)

    def get(self, task_id: str) -> TaskRecord:
        for record in self._records():
            if record.task_id == task_id:
                return record
        raise TaskFileError(f"task not found: {task_id}")

    def set_status(self, task_id: str, status: str, *, updated: str | None = None) -> None:
        if status not in STATUSES:
            raise TaskFileError(f"invalid status: {status}")
        timestamp = updated or utc_timestamp()
        _validate_timestamp(timestamp)
        if status == "in-progress":
            active = self._active_task_id()
            if active and active != task_id:
                raise ActiveTaskError(
                    f"{active} is already in-progress; {task_id} cannot enter in-progress"
                )

        lines = self.path.read_text(encoding="utf-8").splitlines(keepends=True)
        wanted = f"### {task_id}"
        in_task = False
        status_index: int | None = None
        updated_index: int | None = None
        for index, line in enumerate(lines):
            stripped = line.rstrip("\r\n")
            if stripped.startswith("### TASK-"):
                if in_task:
                    break
                in_task = stripped == wanted
            elif in_task and stripped.startswith("STATUS:       "):
                status_index = index
            elif in_task and stripped.startswith("UPDATED:      "):
                updated_index = index
                break

        if status_index is None or updated_index is None:
            raise TaskFileError(f"task not found or malformed: {task_id}")

        lines[status_index] = self._replace_line_value(lines[status_index], "STATUS:       ", status)
        lines[updated_index] = self._replace_line_value(
            lines[updated_index],
            "UPDATED:      ",
            timestamp,
        )
        self._atomic_write("".join(lines))

    def set_change_status(
        self,
        task_id: str,
        value: str,
        *,
        updated: str | None = None,
    ) -> None:
        _validate_single_line("change status", value)
        timestamp = updated or utc_timestamp()
        _validate_timestamp(timestamp)

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", original)
            if heading is None:
                raise TaskFileError(f"task not found: {task_id}")
            next_boundary = re.search(r"(?m)^### |^## ", original[heading.end() :])
            end = heading.end() + (
                next_boundary.start()
                if next_boundary is not None
                else len(original) - heading.end()
            )
            card = original[heading.start() : end].strip()
            card = self._set_board_field(card, "Change status", value)
            card = self._set_board_field(card, "Last updated", timestamp)
            card = self._set_board_field(card, "Updated", timestamp)
            candidate = original[: heading.start()] + card + "\n\n" + original[end:]
            self._refuse_lost_cards(original, candidate, "change status update")
            issues = self._validate_candidate(candidate)
            if issues:
                detail = "; ".join(issue.message for issue in issues)
                raise TaskFileError(f"change would make tasks.md invalid: {detail}")
            self._atomic_write(candidate)
            persisted = self.path.read_text(encoding="utf-8")
            persisted_issues = validate_structure(self.path)
            if persisted != candidate or persisted_issues:
                self._atomic_write(original)
                raise TaskFileError("change verification failed; original tasks.md restored")

    def set_board_fields(
        self,
        task_id: str,
        fields: dict[str, str],
        *,
        updated: str | None = None,
    ) -> None:
        """Set non-lifecycle fields through the locked, validated commit path."""
        if not fields:
            raise TaskFileError("at least one board field is required")
        forbidden = {"Status", "Owner", "Skill", "Last updated", "Updated"}
        blocked = forbidden.intersection(fields)
        if blocked:
            raise TaskFileError(f"mirrored fields require a lifecycle writer: {', '.join(sorted(blocked))}")
        for name, value in fields.items():
            _validate_single_line("field name", name)
            _validate_single_line(name, value)
        timestamp = updated or utc_timestamp()
        _validate_timestamp(timestamp)

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", original)
            if heading is None:
                raise TaskFileError(f"task not found: {task_id}")
            boundary = re.search(r"(?m)^### |^## ", original[heading.end() :])
            end = heading.end() + (boundary.start() if boundary is not None else len(original) - heading.end())
            card = original[heading.start() : end].strip()
            for name, value in fields.items():
                card = self._set_board_field(card, name, value)
            card = self._set_board_field(card, "Last updated", timestamp)
            card = self._set_board_field(card, "Updated", timestamp)
            candidate = original[: heading.start()] + card + "\n\n" + original[end:]
            self._commit(original, candidate, "board field update")

    def set_card_title(self, task_id: str, title: str) -> None:
        """Rename a card — the heading and the mirrored field, in one commit.

        A board card carries its title twice: in the `### TASK-000 — ...` heading and
        in a `- Title:` field. `dashboard_server.parse_tasks` reads the heading first
        and then lets the field overwrite it, so the field is what the console shows
        and the heading is what every other reader greps. Writing one without the
        other leaves a card that answers the same question two ways.

        `set_board_fields` can already write the field; nothing could write the
        heading, which is why this exists rather than a second call at the caller.
        Both go through one lock and one `_commit`, so they cannot land apart.
        """
        # Collapsed before it is validated, not after: `_validate_single_line` asks
        # whether the value is empty, and "   " is not — so a whitespace-only title
        # would pass it and write `### TASK-000 —` with nothing after the dash.
        title = " ".join(str(title or "").split())
        _validate_single_line("title", title)
        timestamp = utc_timestamp()

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", original)
            if heading is None:
                raise TaskFileError(f"task not found: {task_id}")
            boundary = re.search(r"(?m)^### |^## ", original[heading.end() :])
            end = heading.end() + (
                boundary.start() if boundary is not None else len(original) - heading.end()
            )
            card = original[heading.start() : end].strip()
            # An em dash, not a hyphen: the board parser's card pattern requires one,
            # and a hyphen yields a board with zero tasks rather than an error.
            # A function replacement, not a template: a title is free text a human
            # typed, and a backslash in it would otherwise be read as a group
            # reference and either corrupt the heading or raise.
            card = re.sub(
                rf"\A### {re.escape(task_id)}(?:\s+—\s+.*)?$",
                lambda _match: f"### {task_id} — {title}",
                card,
                count=1,
                flags=re.M,
            )
            card = self._set_board_field(card, "Title", title)
            card = self._set_board_field(card, "Last updated", timestamp)
            card = self._set_board_field(card, "Updated", timestamp)
            candidate = original[: heading.start()] + card + "\n\n" + original[end:]
            self._commit(original, candidate, "card title update")

    def add_board_cards(self, cards: list[str], section: str = "Backlog") -> None:
        """Add fully rendered cards through the locked, validated commit path."""
        if section not in BOARD_SECTIONS:
            raise TaskFileError(f"invalid target section: {section}")
        if not cards:
            raise TaskFileError("at least one board card is required")
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            marker = f"## {section}\n"
            insert_at = original.find(marker)
            if insert_at < 0:
                raise TaskFileError(f"target section not found: {section}")
            insert_at += len(marker)
            rendered = "\n\n".join(card.strip() for card in cards) + "\n\n"
            candidate = original[:insert_at] + "\n" + rendered + original[insert_at:]
            self._commit(original, candidate, "board card add")

    def _commit(self, original: str, candidate: str, operation: str) -> None:
        self._refuse_lost_cards(original, candidate, operation)
        issues = self._validate_candidate(candidate)
        if issues:
            detail = "; ".join(issue.message for issue in issues)
            raise TaskFileError(f"{operation} would make tasks.md invalid: {detail}")
        self._atomic_write(candidate)
        if self.path.read_text(encoding="utf-8") != candidate or validate_structure(self.path):
            self._atomic_write(original)
            raise TaskFileError(f"{operation} verification failed; original tasks.md restored")

    def move(
        self,
        task_id: str,
        target_section: str,
        *,
        updated: str | None = None,
        change_status: str | None = None,
        tag: str | None = None,
    ) -> None:
        if target_section not in BOARD_SECTIONS:
            raise TaskFileError(f"invalid target section: {target_section}")
        if change_status is not None:
            _validate_single_line("Change status", change_status)
        if tag is not None:
            _validate_single_line("Tag", tag)
        timestamp = updated or utc_timestamp()
        _validate_timestamp(timestamp)

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.touch(exist_ok=True)
        with self.lock_path.open("r+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_EX)
            original = self.path.read_text(encoding="utf-8")
            candidate = self._moved_board(
                original,
                task_id,
                target_section,
                timestamp,
                change_status=change_status,
                tag=tag,
            )
            self._refuse_lost_cards(original, candidate, "move")
            issues = self._validate_candidate(candidate)
            if issues:
                detail = "; ".join(issue.message for issue in issues)
                raise TaskFileError(f"move would make tasks.md invalid: {detail}")

            self._atomic_write(candidate)
            persisted = self.path.read_text(encoding="utf-8")
            persisted_issues = validate_structure(self.path)
            if persisted != candidate or persisted_issues:
                self._atomic_write(original)
                raise TaskFileError("move verification failed; original tasks.md restored")

    def _moved_board(
        self,
        text: str,
        task_id: str,
        target_section: str,
        timestamp: str,
        *,
        change_status: str | None = None,
        tag: str | None = None,
    ) -> str:
        heading = re.search(rf"(?m)^### {re.escape(task_id)}(?:\s+—\s+.*?)?$", text)
        if heading is None:
            raise TaskFileError(f"task not found: {task_id}")
        next_boundary = re.search(r"(?m)^### |^## ", text[heading.end() :])
        end = heading.end() + (
            next_boundary.start() if next_boundary is not None else len(text) - heading.end()
        )
        card = text[heading.start() : end].strip()

        if target_section == "In Progress":
            active = self._board_task_ids_in_section(text, "In Progress")
            other_active = next((active_id for active_id in active if active_id != task_id), None)
            if other_active is not None:
                raise ActiveTaskError(
                    f"{other_active} is already in In Progress; {task_id} cannot enter In Progress"
                )

        card = self._set_board_field(card, "Status", target_section)
        if change_status is not None:
            card = self._set_board_field(card, "Change status", change_status)
        if tag is not None:
            card = self._set_board_field(card, "Tag", tag)
        card = self._set_board_field(card, "Last updated", timestamp)
        card = self._set_board_field(card, "Updated", timestamp)
        without_card = text[: heading.start()] + text[end:]
        marker = f"## {target_section}\n"
        insert_at = without_card.find(marker)
        if insert_at < 0:
            raise TaskFileError(f"target section not found: {target_section}")
        insert_at += len(marker)
        return without_card[:insert_at] + "\n" + card + "\n\n" + without_card[insert_at:]

    @staticmethod
    def _set_board_field(card: str, name: str, value: str) -> str:
        pattern = rf"(?m)^- {re.escape(name)}:\s*.*?$"
        matches = re.findall(pattern, card)
        if len(matches) > 1:
            raise TaskFileError(f"duplicate {name} field")
        line = f"- {name}: {value}"
        if matches:
            # `value` reaches here from a human-typed title, so the replacement is a
            # function: `re.sub` would read a backslash in a template as a group
            # reference.
            return re.sub(pattern, lambda _match: line, card, count=1)
        return card.rstrip() + "\n" + line

    @staticmethod
    def _board_task_ids_in_section(text: str, section: str) -> list[str]:
        marker = f"## {section}\n"
        start = text.find(marker)
        if start < 0:
            raise TaskFileError(f"section not found: {section}")
        start += len(marker)
        next_section = re.search(r"(?m)^## ", text[start:])
        end = start + next_section.start() if next_section is not None else len(text)
        return re.findall(r"(?m)^### (TASK-\d+)(?:\s+—\s+.*?)?$", text[start:end])

    def _validate_candidate(self, content: str) -> list[ValidationIssue]:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=self.path.parent,
                prefix=f".{self.path.name}.validate.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            return validate_structure(temporary_path)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def card_ids(text: str) -> list[str]:
        """Every task ID with a card on the board, in board order."""
        return [
            match.group(1)
            for line in text.splitlines()
            if (match := BOARD_TASK_HEADING.fullmatch(line.rstrip("\r")))
        ]

    def _refuse_lost_cards(self, original: str, candidate: str, operation: str) -> None:
        """No board write may make a card disappear.

        `validate_structure` answers "is this a well-formed board", and a board with
        four cards deleted off the end is perfectly well-formed. That is not a
        hypothetical: a substitution run with `re.S` consumed everything from one
        field to the end of the file, four Completed cards went with it, and every
        check in the write path passed.

        So the write path now compares what it is about to commit against what is
        there. Sections may change, fields may change, cards may be added — a card
        may not silently stop existing. Removing one is a deliberate act that needs
        its own writer, not a side effect of editing a field.
        """
        before = set(self.card_ids(original))
        lost = before.difference(self.card_ids(candidate))
        if lost:
            raise TaskFileError(
                f"{operation} would remove {len(lost)} card(s) from the board: "
                + ", ".join(sorted(lost))
            )

    def _active_task_id(self) -> str | None:
        for record in self._records():
            if record.status == "in-progress":
                return record.task_id
        return None

    @staticmethod
    def _replace_line_value(line: str, prefix: str, value: str) -> str:
        if line.endswith("\r\n"):
            ending = "\r\n"
        elif line.endswith("\n"):
            ending = "\n"
        else:
            ending = ""
        return f"{prefix}{value}{ending}"

    def _atomic_write(self, content: str) -> None:
        mode = stat.S_IMODE(self.path.stat().st_mode)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as stream:
                temporary_path = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary_path, mode)
            os.replace(temporary_path, self.path)
            temporary_path = None
            directory_fd = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _render(task_id: str, task: Task, updated: str) -> str:
        return "\n".join(
            [
                f"### {task_id}",
                f"TITLE:        {task.title}",
                f"SKILL:        {task.skill}",
                f"DESCRIPTION:  {task.description}",
                f"ATTACHMENT:   {task.attachment}",
                f"METRIC:       {task.metric}",
                f"STATUS:       {task.status}",
                f"TAG:          {task.tag}",
                f"UPDATED:      {updated}",
                "",
            ]
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the SOUL.md section 4 task file")
    parser.add_argument("--file", default="tasks.md", help="task file path")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("next-id")

    add = commands.add_parser("add")
    add.add_argument("--title", required=True)
    add.add_argument("--skill", required=True, choices=sorted(SKILLS))
    add.add_argument("--description", required=True)
    add.add_argument("--attachment", required=True)
    add.add_argument("--metric", required=True)
    add.add_argument("--status", default="queued", choices=sorted(STATUSES))
    add.add_argument("--tag", default="action to be taken by: cmo")

    top = commands.add_parser("top")
    top.add_argument("--limit", type=int, required=True)

    update = commands.add_parser("set-status")
    update.add_argument("task_id")
    update.add_argument("status", choices=sorted(STATUSES))
    move = commands.add_parser("move")
    move.add_argument("task_id")
    move.add_argument("target_section", choices=BOARD_SECTIONS)
    change_status = commands.add_parser("set-change-status")
    change_status.add_argument("task_id")
    change_status.add_argument("value")
    commands.add_parser("validate")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    task_file = TaskFile(args.file)
    try:
        if args.command == "next-id":
            print(task_file.next_id())
        elif args.command == "add":
            task_id = task_file.add(
                Task(
                    title=args.title,
                    skill=args.skill,
                    description=args.description,
                    attachment=args.attachment,
                    metric=args.metric,
                    status=args.status,
                    tag=args.tag,
                )
            )
            print(task_id)
        elif args.command == "top":
            result = task_file.top_open(args.limit)
            print(
                json.dumps(
                    {
                        "tasks": [asdict(task) for task in result.tasks],
                        "lines_read": result.lines_read,
                        "reached_eof": result.reached_eof,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        elif args.command == "set-status":
            task_file.set_status(args.task_id, args.status)
            print(f"{args.task_id}: {args.status}")
        elif args.command == "move":
            task_file.move(args.task_id, args.target_section)
            print(f"{args.task_id}: {args.target_section}")
        elif args.command == "set-change-status":
            task_file.set_change_status(args.task_id, args.value)
            print(f"{args.task_id}: Change status: {args.value}")
        elif args.command == "validate":
            issues = validate_structure(args.file)
            # The count is printed whether or not anything is wrong. A number a
            # human sees every run is a number they notice halving.
            cards = TaskFile.card_ids(Path(args.file).read_text(encoding="utf-8"))
            print(
                json.dumps(
                    {
                        "cards": len(cards),
                        "card_floor": card_count_floor(args.file),
                        "issues": [asdict(issue) for issue in issues],
                    },
                    indent=2,
                )
            )
            return 2 if issues else 0
    except TaskFileError as error:
        print(f"ERROR: {error}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
