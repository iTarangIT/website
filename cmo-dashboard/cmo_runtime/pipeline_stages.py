"""Record what each stage of writing a blog actually did, while it does it.

The pipeline already performed most of these steps; it just performed them
invisibly. A topic went in, an article came out, and the fifteen minutes in
between were a spinner. This module is the seam that turns each step into a row
someone can read.

Two rules shape everything here.

**A stage is opened before the work and closed after it.** Not written once at
the end. `ConsoleDB.write()` is one `BEGIN IMMEDIATE` per call, so opening and
closing are separate transactions and a process killed halfway through leaves
every finished stage committed and the interrupted one readable as `running`
with a start time. That is both the honest record of a crash and exactly what
the console needs in order to show "in progress, 41s elapsed". Writing the row
only on success would have made a crash look like a stage that never ran.

**A failure is a row, not a gap.** An exception inside the block closes the
stage as `failed`, carrying the reason, and then re-raises. `ContentRunRefused`
— Firecrawl out of credits, an outline too broad — is a thing the pipeline did,
and the reader is owed it. The same applies to fetches: a source that returned
502 gets a row saying so, because "we tried eight and got six" is information
and "here are six" is not.

Retries do not overwrite. `attempt` increments, so nine failed generations are
nine rows rather than one row that eventually says `completed`.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from cmo_runtime.console_db import ConsoleDB

__all__ = ["OpenStage", "StageRecorder", "NullStage", "NullRecorder"]


class OpenStage:
    """A stage that is currently running. Handed to the caller inside the block."""

    def __init__(
        self,
        database: ConsoleDB,
        stage_id: int,
        stage: str,
        *,
        duration_ms: int | None = None,
    ) -> None:
        self.database = database
        self.id = stage_id
        self.stage = stage
        self._started = time.monotonic()
        self._duration_override = duration_ms
        self._detail: dict[str, Any] = {}
        self._summary = ""
        self._closed = False

    # -- what the stage produced -------------------------------------------

    def note(self, **detail: Any) -> None:
        """Add to the stage's output. Merged, so a caller can build it up."""
        self._detail.update(detail)

    def set_summary(self, summary: str) -> None:
        self._summary = summary

    # -- what the stage read -----------------------------------------------

    def record_fetch(self, **fields: Any) -> int:
        """One attempt to read something. See `ConsoleDB.record_fetch`."""
        return self.database.record_fetch(self.id, **fields)

    def record_sources(
        self,
        sources: Sequence[Mapping[str, Any]],
        *,
        kind: str = "scrape",
        outcome: str = "fetched",
    ) -> int:
        """Log a run of sources given as plain mappings.

        Deliberately takes mappings rather than the researcher's dataclasses:
        this module is imported *by* the research code, so it must not import it
        back.
        """
        recorded = 0
        for source in sources:
            self.record_fetch(
                kind=kind,
                outcome=str(source.get("outcome", outcome)),
                url=str(source.get("url", "")),
                query=str(source.get("query", "")),
                title=str(source.get("title", "")),
                published_date=str(source.get("published_date", "")),
                accessed_at=str(source.get("accessed_date", source.get("accessed_at", ""))),
                message=str(source.get("message", "")),
                leader_id=source.get("leader_id"),
                credits=source.get("credits"),
            )
            recorded += 1
        return recorded

    # -- closing ------------------------------------------------------------

    @property
    def duration_ms(self) -> int:
        if self._duration_override is not None:
            return self._duration_override
        return int((time.monotonic() - self._started) * 1000)

    def finish(self, *, summary: str = "", status: str = "completed", **detail: Any) -> None:
        """Close the stage. Called for you on a clean exit from the block."""
        if self._closed:
            return
        self._detail.update(detail)
        self.database.finish_stage(
            self.id,
            status=status,
            summary=summary or self._summary,
            detail=self._detail,
            duration_ms=self.duration_ms,
        )
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed


class StageRecorder:
    """Opens and closes stage rows for one article's run.

    Owns no connection of its own — the caller passes the `ConsoleDB` it is
    already using, so a stage write joins the same file and the same WAL that
    `ceo_version` is already watching. The console therefore updates without any
    new mechanism.
    """

    def __init__(
        self,
        database: ConsoleDB,
        *,
        task_id: str = "",
        proposal_id: int | None = None,
    ) -> None:
        self.database = database
        self.task_id = task_id
        self.proposal_id = proposal_id

    @classmethod
    def for_profile(
        cls,
        profile_dir: str | Path,
        *,
        task_id: str = "",
        proposal_id: int | None = None,
    ) -> StageRecorder:
        return cls(ConsoleDB(profile_dir), task_id=task_id, proposal_id=proposal_id)

    @contextmanager
    def stage(
        self,
        name: str,
        *,
        task_id: str | None = None,
        proposal_id: int | None = None,
        attempt: int | None = None,
    ) -> Iterator[OpenStage]:
        """Run a block as a recorded stage.

        On a clean exit the stage closes `completed`. On an exception it closes
        `failed` carrying the reason, and the exception continues on its way —
        this records, it never swallows.
        """
        target_task = self.task_id if task_id is None else task_id
        target_proposal = self.proposal_id if proposal_id is None else proposal_id
        if attempt is None:
            attempt = self.database.next_attempt(
                name, task_id=target_task, proposal_id=target_proposal
            )
        stage_id = self.database.start_stage(
            name, task_id=target_task, proposal_id=target_proposal, attempt=attempt
        )
        open_stage = OpenStage(self.database, stage_id, name)
        try:
            yield open_stage
        except BaseException as error:
            if not open_stage.closed:
                open_stage.finish(
                    status="failed",
                    summary=f"{type(error).__name__}: {error}",
                )
            raise
        open_stage.finish()

    @contextmanager
    def replay(
        self,
        name: str,
        *,
        started_at: str,
        duration_ms: int,
        task_id: str | None = None,
        proposal_id: int | None = None,
        attempt: int | None = None,
    ) -> Iterator[OpenStage]:
        """Record a stage whose work has already run, with its measured timings.

        The topic side needs this and the writer side does not. One research pass
        and one proposer call produce up to six candidate topics, and a candidate
        does not exist as a proposal until after both have finished — so the
        stages cannot be opened around work that has not yet chosen which
        proposal it belongs to. The timings passed in are the real measured ones
        for that shared pass; the stage detail says it was shared, so nobody
        reads six separate research passes into what was one.

        Everything after the topic flow uses `stage()` and is recorded live.
        """
        target_task = self.task_id if task_id is None else task_id
        target_proposal = self.proposal_id if proposal_id is None else proposal_id
        if attempt is None:
            attempt = self.database.next_attempt(
                name, task_id=target_task, proposal_id=target_proposal
            )
        stage_id = self.database.start_stage(
            name,
            task_id=target_task,
            proposal_id=target_proposal,
            attempt=attempt,
            started_at=started_at,
        )
        open_stage = OpenStage(self.database, stage_id, name, duration_ms=duration_ms)
        try:
            yield open_stage
        except BaseException as error:
            if not open_stage.closed:
                open_stage.finish(status="failed", summary=f"{type(error).__name__}: {error}")
            raise
        open_stage.finish()

    def bind_to_task(self, task_id: str) -> int:
        """Claim this recorder's proposal-side stages for a freshly minted card."""
        if self.proposal_id is None:
            return 0
        return self.database.bind_stages_to_task(self.proposal_id, task_id)


class NullStage(OpenStage):
    """A stage that records nothing, for callers built without a store."""

    def __init__(self) -> None:  # noqa: D107 - deliberately skips the parent
        self.id = 0
        self.stage = ""
        self._started = time.monotonic()
        self._duration_override = None
        self._detail = {}
        self._summary = ""
        self._closed = False

    def record_fetch(self, **fields: Any) -> int:
        del fields
        return 0

    def finish(self, *, summary: str = "", status: str = "completed", **detail: Any) -> None:
        del summary, status, detail
        self._closed = True


class NullRecorder(StageRecorder):
    """Explicit opt-out, for tests and for callers with no profile.

    Not a fallback: a store that fails to open is an error worth seeing, not a
    reason to write an article whose work went unrecorded.
    """

    def __init__(self) -> None:  # noqa: D107 - deliberately skips the parent
        self.database = None  # type: ignore[assignment]
        self.task_id = ""
        self.proposal_id = None

    @contextmanager
    def stage(
        self,
        name: str,
        *,
        task_id: str | None = None,
        proposal_id: int | None = None,
        attempt: int | None = None,
    ) -> Iterator[OpenStage]:
        del name, task_id, proposal_id, attempt
        yield NullStage()

    @contextmanager
    def replay(
        self,
        name: str,
        *,
        started_at: str,
        duration_ms: int,
        task_id: str | None = None,
        proposal_id: int | None = None,
        attempt: int | None = None,
    ) -> Iterator[OpenStage]:
        del name, started_at, duration_ms, task_id, proposal_id, attempt
        yield NullStage()

    def bind_to_task(self, task_id: str) -> int:
        del task_id
        return 0
