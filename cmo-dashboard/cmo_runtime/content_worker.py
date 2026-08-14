"""The loop that turns an approval into a run.

Approving a topic mints a card. Until this existed, that was the whole of it: the
card sat in Backlog and somebody had to open a shell and type
`cmo_agent … content-execute` for anything to happen. There is no cron here and
`cron_mode: deny` blocks scheduled runs, so the mechanism is a long-lived process
that watches the board and starts the work it finds.

What it does not do:

- **It does not decide.** It never approves, never rejects, never reorders the
  board to suit itself, and never touches a card a human put on hold.
- **It does not reimplement the concurrency rule.** One card is In Progress at a
  time because `TaskFile` enforces that; this loop simply declines to provoke the
  error, so a second approval queues instead of failing.
- **It does not run the writer in-process.** Each job is `cmo_agent`'s existing
  accounted subcommand in a subprocess, so spend logging and the skill-file audit
  stay byte-for-byte what they were, and a writer that dies cannot take the loop
  with it.

The one thing it owns is `state/content-worker.json`: pid, which card, which kind
of run, when it started, when it was last seen. The console reads that file to say
*Researching…* or *Writing…* with an elapsed time, and this loop reads it back on
the next tick to notice a card stranded In Progress by a crash.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from cmo_runtime.agent_runtime import BoardCard, BoardStore
from cmo_runtime.content_flow import (
    BLOCKING_CHANGE_STATUSES,
    NON_ARTICLE_WORK_TYPES,
    WRITE_FAILED,
)
from cmo_runtime.task_file import TaskFile, TaskFileError

#: How often the board is read. Cheap: one file read, no network.
DEFAULT_POLL_SECONDS = 5.0

#: How long a card may sit In Progress with no live worker before it is returned.
#: The writer's own subprocess timeout is 600s and research can precede it, so this
#: is deliberately well past any healthy run.
DEFAULT_STALE_SECONDS = 1800.0

HEARTBEAT_NAME = "content-worker.json"

REVISION_REQUESTED = "revision requested"

#: The interpreter the deployed console runs under; the writer needs the same one.
DEFAULT_PYTHON = "/opt/hermes/.venv/bin/python"

#: After a card's run fails, how long before this loop offers it again — doubling
#: each time, capped. A run that fails in milliseconds must not be retried in
#: milliseconds; the cost of getting this wrong is a board write per second and a
#: writer call per second. Held in memory, so restarting the worker is itself the
#: way to say "try again now".
FAILURE_BACKOFF_SECONDS = 30.0
FAILURE_BACKOFF_CAP_SECONDS = 900.0


def utc_now() -> datetime:
    return datetime.now(UTC)


def _stamp(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _field(card: BoardCard, name: str) -> str:
    return str(card.fields.get(name, "")).strip()


def _is_content(card: BoardCard) -> bool:
    return (_field(card, "Skill") or _field(card, "Owner")).casefold() == "content"


def _has_artifact(card: BoardCard) -> bool:
    attachment = _field(card, "Attachment").casefold()
    return bool(attachment) and attachment not in {"none", "not attached", "n/a"}


def eligible_cards(cards: list[BoardCard]) -> list[BoardCard]:
    """Cards an approved topic has queued and nobody has held.

    Board order, except that a card marked `Priority: high` comes first — that is
    the marker the board already carries, and it is the only reordering allowed.
    """
    candidates: list[BoardCard] = []
    for card in cards:
        if card.section != "Backlog" or not _is_content(card):
            continue
        if _field(card, "Topic stage").casefold() != "approved":
            continue
        if _has_artifact(card):
            continue
        if _field(card, "Change status").casefold() in BLOCKING_CHANGE_STATUSES:
            continue
        if _field(card, "Work type").casefold() in NON_ARTICLE_WORK_TYPES:
            continue
        candidates.append(card)
    # `sorted` is stable, so cards of equal priority keep board order.
    return sorted(candidates, key=lambda card: 0 if _field(card, "Priority").casefold() == "high" else 1)


def revision_cards(cards: list[BoardCard]) -> list[BoardCard]:
    """Cards whose human asked for a rewrite and has not had one yet.

    The round has to be there: it is what names the comment being answered, so
    `revision requested` without one is the word for a request rather than a
    request. Such a card must never be picked up, because a refused revision
    restores `revision requested` — an unguarded loop would rewrite the board
    once per tick, forever. That is not hypothetical; it is what this worker did
    on its first live run.
    """
    return [
        card
        for card in cards
        if _is_content(card)
        and card.section != "In Progress"
        and _field(card, "Change status").casefold() == REVISION_REQUESTED
        and re.fullmatch(r"[1-9][0-9]*", _field(card, "Revision round"))
    ]


def active_cards(cards: list[BoardCard]) -> list[BoardCard]:
    return [card for card in cards if card.section == "In Progress"]


@dataclass(frozen=True)
class Job:
    kind: str  # "write" | "revise"
    task_id: str


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ContentWorker:
    def __init__(
        self,
        root: str | Path,
        *,
        poll_seconds: float | None = None,
        stale_seconds: float | None = None,
        python: str | None = None,
        runner: object | None = None,
        now: object | None = None,
    ) -> None:
        self.root = Path(root)
        self.board = BoardStore(self.root)
        self.task_file = TaskFile(self.root / "tasks.md", lock_path=self.root / "state" / "tasks.lock")
        self.poll_seconds = float(
            poll_seconds if poll_seconds is not None else os.getenv("CMO_WORKER_POLL_SECONDS", DEFAULT_POLL_SECONDS)
        )
        self.stale_seconds = float(
            stale_seconds if stale_seconds is not None else os.getenv("CMO_WORKER_STALE_SECONDS", DEFAULT_STALE_SECONDS)
        )
        self.python = python or os.getenv("CMO_WORKER_PYTHON", DEFAULT_PYTHON)
        self.runner = runner or self._run_subprocess
        self.now = now or utc_now
        self._started_at = ""
        #: task_id -> (consecutive failures, monotonic time it may be tried again)
        self._cooling: dict[str, tuple[int, float]] = {}

    # ------------------------------------------------------------------ backoff
    def _cooling_off(self, task_id: str, clock: float) -> bool:
        entry = self._cooling.get(task_id)
        return entry is not None and clock < entry[1]

    def _note_failure(self, task_id: str, clock: float) -> float:
        failures = self._cooling.get(task_id, (0, 0.0))[0] + 1
        delay = min(FAILURE_BACKOFF_SECONDS * (2 ** (failures - 1)), FAILURE_BACKOFF_CAP_SECONDS)
        self._cooling[task_id] = (failures, clock + delay)
        return delay

    def _note_success(self, task_id: str) -> None:
        self._cooling.pop(task_id, None)

    # ---------------------------------------------------------------- heartbeat
    @property
    def heartbeat_path(self) -> Path:
        return self.root / "state" / HEARTBEAT_NAME

    def read_heartbeat(self) -> dict[str, object]:
        try:
            value = json.loads(self.heartbeat_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return value if isinstance(value, dict) else {}

    def write_heartbeat(self, job: Job | None) -> None:
        """One small JSON file, replaced atomically.

        `ceo_version` already folds `state/*.json` into its token, so writing this
        is what makes the console notice a run starting without any new plumbing.
        """
        moment = _stamp(self.now())
        payload: dict[str, object] = {
            "pid": os.getpid(),
            "updated_at": moment,
            "task_id": job.task_id if job else "",
            "kind": job.kind if job else "",
            "started_at": self._started_at if job else "",
        }
        path = self.heartbeat_path
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, sort_keys=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise

    # ----------------------------------------------------------------- recovery
    def _age_seconds(self, value: str) -> float | None:
        try:
            moment = datetime.strptime(value.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        except ValueError:
            return None
        return (self.now() - moment).total_seconds()

    def recover_stranded(self, cards: list[BoardCard]) -> list[str]:
        """Return a card the writer abandoned, with the reason on the card.

        Two conditions, and both must hold. No worker is behind the card — the
        heartbeat names something else, or names a pid that is gone, or has gone
        quiet past the stale window. **And** the card itself has sat In Progress
        longer than that window. The second condition is what keeps this from
        yanking a card out from under somebody running `content-execute` by hand:
        their run has no heartbeat here, and a card that only just moved is not
        evidence of a crash.

        Without this a crash parks a card In Progress forever, and the
        single-In-Progress rule then stops the whole board behind it.
        """
        beat = self.read_heartbeat()
        raw_pid = str(beat.get("pid", ""))
        pid = int(raw_pid) if raw_pid.lstrip("-").isdigit() else 0
        held = str(beat.get("task_id", ""))
        beat_age = self._age_seconds(str(beat.get("updated_at", "")))
        worker_live = (
            _process_alive(pid) and beat_age is not None and beat_age <= self.stale_seconds
        )

        returned: list[str] = []
        for card in active_cards(cards):
            if not _is_content(card):
                continue
            if held == card.task_id and worker_live:
                continue
            card_age = self._age_seconds(_field(card, "Updated") or _field(card, "Last updated"))
            if card_age is None or card_age <= self.stale_seconds:
                continue
            minutes = int(card_age // 60)
            reason = (
                "Returned to Backlog: the writer stopped without finishing "
                f"(In Progress for {minutes} minutes with no live worker). "
                "Retry it when you are ready."
            )
            try:
                self.task_file.move(
                    card.task_id,
                    "Backlog",
                    change_status=WRITE_FAILED,
                    tag="action to be taken by: cmo",
                )
                self.task_file.set_board_fields(card.task_id, {"Latest summary": reason})
            except TaskFileError:
                continue
            returned.append(card.task_id)
        return returned

    # ------------------------------------------------------------------ picking
    def next_job(self, cards: list[BoardCard], clock: float | None = None) -> Job | None:
        """A rewrite outranks a fresh write: it is a reply to a human who is waiting."""
        if active_cards(cards):
            return None
        moment = time.monotonic() if clock is None else clock
        for kind, candidates in (("revise", revision_cards(cards)), ("write", eligible_cards(cards))):
            for card in candidates:
                if not self._cooling_off(card.task_id, moment):
                    return Job(kind, card.task_id)
        return None

    # ------------------------------------------------------------------ running
    def _command(self, job: Job) -> list[str]:
        base = [self.python, "-m", "cmo_runtime.cmo_agent", "--profile", str(self.root)]
        if job.kind == "revise":
            return [*base, "content-revise", job.task_id]
        return [*base, "content-execute"]

    def _run_subprocess(self, command: list[str]) -> int:
        environment = dict(os.environ)
        source = Path(__file__).resolve().parents[1]
        existing = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = f"{source}{os.pathsep}{existing}" if existing else str(source)
        completed = subprocess.run(
            command,
            cwd=str(self.root),
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        if completed.returncode != 0:
            # cmo_agent has already written the reason onto the card and into the
            # spend log; this line is for whoever reads the worker's own log.
            sys.stderr.write((completed.stdout or "")[-2000:])
            sys.stderr.write((completed.stderr or "")[-2000:])
            sys.stderr.flush()
        return completed.returncode

    def tick(self) -> Job | None:
        """One pass: recover what crashed, then start at most one run."""
        cards = self.board.cards()
        self.recover_stranded(cards)
        job = self.next_job(self.board.cards())
        if job is None:
            self._started_at = ""
            self.write_heartbeat(None)
            return None
        self._started_at = _stamp(self.now())
        self.write_heartbeat(job)
        code = 1
        try:
            code = self.runner(self._command(job)) or 0  # type: ignore[operator]
        finally:
            self._started_at = ""
            self.write_heartbeat(None)
            if code == 0:
                self._note_success(job.task_id)
            else:
                delay = self._note_failure(job.task_id, time.monotonic())
                sys.stderr.write(
                    f"content-worker: {job.task_id} {job.kind} exited {code}; "
                    f"not offering it again for {int(delay)}s\n"
                )
                sys.stderr.flush()
        return job

    def run_forever(self) -> int:
        while True:
            try:
                self.tick()
            except Exception as error:  # noqa: BLE001 - a bad tick must not end the loop
                sys.stderr.write(f"content-worker tick failed: {error}\n")
                sys.stderr.flush()
            # Always, whether or not a job ran. A job that fails in milliseconds
            # would otherwise be retried in milliseconds, and the first live run of
            # this worker wrote the board 147 times in fifteen seconds doing
            # exactly that.
            time.sleep(self.poll_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start approved content runs as they appear on the board")
    parser.add_argument(
        "--profile",
        default=os.getenv("CMO_DASHBOARD_PROFILE_DIR", "/opt/data/profiles/itarang_cmo"),
    )
    parser.add_argument("--once", action="store_true", help="run a single tick and exit")
    args = parser.parse_args(argv)
    worker = ContentWorker(args.profile)
    if args.once:
        job = worker.tick()
        print(json.dumps({"started": job.task_id if job else "", "kind": job.kind if job else ""}))
        return 0
    return worker.run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
