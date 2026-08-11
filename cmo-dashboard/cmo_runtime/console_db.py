"""The CEO console's own store.

Everything the console displays is written here and read back from here, so the
agent can answer "what did we propose, reject and publish" without re-scraping.

SQLite because it is stdlib, it runs on Hermes, and the topic flow needs real
transactions: approving a proposal marks the row and mints exactly one board card,
and a crash between those two must not be able to produce a second card.

This module owns rows. It never touches tasks.md — `topic_proposals` does that
through TaskFile's public writers.
"""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

SCHEMA_VERSION = 1
DATABASE_NAME = "console.db"

PROPOSAL_STATUSES = ("proposed", "revising", "approved", "carded", "rejected")
SOURCE_KINDS = ("search_console", "firecrawl", "cache", "legacy_board")

_STOPWORDS = frozenset(
    """
    a an and are as at be been being by can could do does for from had has have how
    in into is it its of on or should that the their there these this to under upon
    was were what when where which who why will with would you your we our us
    """.split()
)


class ConsoleDBError(RuntimeError):
    """A store-level refusal that is safe to show to an operator."""


def utc_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_key(text: str) -> str:
    """A fingerprint that survives rewording.

    Lowercase, drop stopwords, crudely singularise, sort the remaining tokens.
    "Three wheeler battery data" and "Data on three wheeler batteries" collapse to
    the same key, which is what makes a rejection stick against a paraphrase.
    """
    tokens: list[str] = []
    for token in re.findall(r"[a-z0-9]+", text.casefold()):
        if token in _STOPWORDS:
            continue
        if token.endswith("ies") and len(token) > 4:
            token = token[:-3] + "y"
        elif token.endswith("sses"):
            token = token[:-2]
        elif token.endswith("s") and not token.endswith("ss") and len(token) > 3:
            token = token[:-1]
        tokens.append(token)
    return " ".join(sorted(set(tokens)))


def _single_line(value: object, *, limit: int = 400) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()[:limit]


@dataclass(frozen=True)
class ProposalCandidate:
    """One candidate topic as the researcher produced it.

    `source_refs` is non-empty by construction — a candidate that cannot say where
    it came from is not a candidate.
    """

    title: str
    keywords: tuple[str, ...]
    outline: str
    source_kind: str
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ConsoleDBError("candidate title is empty")
        if not self.outline.strip():
            raise ConsoleDBError("candidate outline is empty")
        if self.source_kind not in SOURCE_KINDS:
            raise ConsoleDBError(f"unknown candidate source kind: {self.source_kind}")
        if not [ref for ref in self.source_refs if ref.strip()]:
            raise ConsoleDBError(f"candidate names no source: {self.title!r}")


_SCHEMA = """
CREATE TABLE IF NOT EXISTS subjects (
    id          INTEGER PRIMARY KEY,
    raw_text    TEXT NOT NULL,
    norm_key    TEXT NOT NULL UNIQUE,
    actor       TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS research_runs (
    id               INTEGER PRIMARY KEY,
    subject_id       INTEGER NOT NULL REFERENCES subjects(id),
    kind             TEXT NOT NULL,
    pages_requested  INTEGER NOT NULL,
    pages_fetched    INTEGER NOT NULL,
    credits_before   INTEGER,
    credits_after    INTEGER,
    credits_used     INTEGER NOT NULL DEFAULT 0,
    credits_remaining INTEGER,
    gsc_rows_used    INTEGER NOT NULL DEFAULT 0,
    cache_hit_of     INTEGER REFERENCES research_runs(id),
    status           TEXT NOT NULL,
    message          TEXT NOT NULL DEFAULT '',
    created_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proposals (
    id                 INTEGER PRIMARY KEY,
    subject_id         INTEGER NOT NULL REFERENCES subjects(id),
    current_version_id INTEGER,
    status             TEXT NOT NULL,
    norm_key           TEXT NOT NULL,
    task_id            TEXT,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS proposals_status ON proposals(status);
CREATE UNIQUE INDEX IF NOT EXISTS proposals_task ON proposals(task_id)
    WHERE task_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS proposal_versions (
    id               INTEGER PRIMARY KEY,
    proposal_id      INTEGER NOT NULL REFERENCES proposals(id),
    round            INTEGER NOT NULL,
    title            TEXT NOT NULL,
    keywords_json    TEXT NOT NULL,
    outline          TEXT NOT NULL,
    source_kind      TEXT NOT NULL,
    source_refs_json TEXT NOT NULL,
    research_run_id  INTEGER REFERENCES research_runs(id),
    created_at       TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS proposal_versions_round
    ON proposal_versions(proposal_id, round);

CREATE TABLE IF NOT EXISTS proposal_events (
    id          INTEGER PRIMARY KEY,
    proposal_id INTEGER NOT NULL REFERENCES proposals(id),
    round       INTEGER NOT NULL,
    action      TEXT NOT NULL,
    actor       TEXT NOT NULL,
    comment     TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rejected_topics (
    id            INTEGER PRIMARY KEY,
    norm_key      TEXT NOT NULL UNIQUE,
    title         TEXT NOT NULL,
    keywords_json TEXT NOT NULL DEFAULT '[]',
    reason        TEXT NOT NULL DEFAULT '',
    actor         TEXT NOT NULL,
    proposal_id   INTEGER REFERENCES proposals(id),
    created_at    TEXT NOT NULL,
    revoked_at    TEXT
);
"""


class ConsoleDB:
    """One connection per caller. Writers are transactional; readers are plain."""

    def __init__(self, profile_dir: str | Path, *, filename: str = DATABASE_NAME) -> None:
        self.profile_dir = Path(profile_dir)
        state = self.profile_dir / "state"
        state.mkdir(parents=True, exist_ok=True)
        self.path = state / filename
        self._connection = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA busy_timeout=15000")
        self._initialise()

    def _initialise(self) -> None:
        # `executescript` commits any pending transaction of its own, so it must not run
        # inside `write()` — the COMMIT there would find nothing active.
        self._connection.executescript(_SCHEMA)
        self._connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> ConsoleDB:
        return self

    def __exit__(self, *_exception: object) -> None:
        self.close()

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        """One IMMEDIATE transaction. Everything inside commits or none of it does."""
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            yield self._connection
        except BaseException:
            self._connection.execute("ROLLBACK")
            raise
        self._connection.execute("COMMIT")

    def _query(self, sql: str, parameters: Sequence[Any] = ()) -> list[sqlite3.Row]:
        return list(self._connection.execute(sql, parameters))

    def _one(self, sql: str, parameters: Sequence[Any] = ()) -> sqlite3.Row | None:
        rows = self._query(sql, parameters)
        return rows[0] if rows else None

    # ---------------------------------------------------------------- subjects

    def subject_for(self, raw_text: str, actor: str) -> dict[str, Any]:
        """Get or create the subject row. The norm_key is what makes the cache work."""
        text = _single_line(raw_text, limit=180)
        if not 3 <= len(text) <= 180:
            raise ConsoleDBError("a subject must be one line between 3 and 180 characters")
        actor = _single_line(actor, limit=180)
        if not actor:
            raise ConsoleDBError("a subject needs a submitting actor")
        key = norm_key(text)
        if not key:
            raise ConsoleDBError("a subject must contain at least one meaningful word")
        with self.write() as connection:
            existing = connection.execute(
                "SELECT * FROM subjects WHERE norm_key = ?", (key,)
            ).fetchone()
            if existing is not None:
                return dict(existing)
            cursor = connection.execute(
                "INSERT INTO subjects (raw_text, norm_key, actor, created_at)"
                " VALUES (?, ?, ?, ?)",
                (text, key, actor, utc_timestamp()),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM subjects WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
            )

    def subject(self, subject_id: int) -> dict[str, Any]:
        row = self._one("SELECT * FROM subjects WHERE id = ?", (subject_id,))
        if row is None:
            raise ConsoleDBError(f"no subject {subject_id}")
        return dict(row)

    # ---------------------------------------------------------- research runs

    def record_research_run(
        self,
        *,
        subject_id: int,
        kind: str,
        pages_requested: int,
        pages_fetched: int,
        status: str,
        credits_before: int | None = None,
        credits_after: int | None = None,
        credits_used: int = 0,
        credits_remaining: int | None = None,
        gsc_rows_used: int = 0,
        cache_hit_of: int | None = None,
        message: str = "",
    ) -> int:
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO research_runs (subject_id, kind, pages_requested, pages_fetched,"
                " credits_before, credits_after, credits_used, credits_remaining, gsc_rows_used,"
                " cache_hit_of, status, message, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    subject_id,
                    kind,
                    pages_requested,
                    pages_fetched,
                    credits_before,
                    credits_after,
                    credits_used,
                    credits_remaining,
                    gsc_rows_used,
                    cache_hit_of,
                    status,
                    _single_line(message, limit=600),
                    utc_timestamp(),
                ),
            )
            return int(cursor.lastrowid or 0)

    def research_run(self, run_id: int) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM research_runs WHERE id = ?", (run_id,))
        return dict(row) if row else None

    def cached_research_run(self, subject_id: int, *, kind: str = "initial") -> dict[str, Any] | None:
        """The most recent successful run for this subject, whatever its age.

        Age is the caller's policy, not the store's — it holds the TTL constant.
        """
        row = self._one(
            "SELECT * FROM research_runs WHERE subject_id = ? AND kind = ? AND status = 'completed'"
            " ORDER BY id DESC LIMIT 1",
            (subject_id, kind),
        )
        return dict(row) if row else None

    def credits_used_since(self, iso_timestamp: str) -> int:
        row = self._one(
            "SELECT COALESCE(SUM(credits_used), 0) AS total FROM research_runs WHERE created_at >= ?",
            (iso_timestamp,),
        )
        return int(row["total"]) if row else 0

    # --------------------------------------------------------------- rejection

    def is_rejected(self, key: str) -> bool:
        row = self._one(
            "SELECT 1 FROM rejected_topics WHERE norm_key = ? AND revoked_at IS NULL", (key,)
        )
        return row is not None

    def rejected_topics(self, *, include_revoked: bool = False) -> list[dict[str, Any]]:
        sql = "SELECT * FROM rejected_topics"
        if not include_revoked:
            sql += " WHERE revoked_at IS NULL"
        sql += " ORDER BY id DESC"
        return [
            {**dict(row), "keywords": json.loads(row["keywords_json"])}
            for row in self._query(sql)
        ]

    def undo_rejection(self, key: str, actor: str) -> bool:
        """Revoke a permanent veto. Rejection is forever, but forever is reversible."""
        del actor
        with self.write() as connection:
            cursor = connection.execute(
                "UPDATE rejected_topics SET revoked_at = ? WHERE norm_key = ? AND revoked_at IS NULL",
                (utc_timestamp(), key),
            )
            return cursor.rowcount > 0

    # --------------------------------------------------------------- proposals

    def add_candidates(
        self,
        *,
        subject_id: int,
        research_run_id: int | None,
        candidates: Sequence[ProposalCandidate],
    ) -> dict[str, list[dict[str, Any]]]:
        """Insert candidates, suppressing anything Sanchit already rejected.

        Suppression is reported, never silent — an operator who cannot see why an
        obvious topic never appears will assume the agent is broken.
        """
        added: list[dict[str, Any]] = []
        suppressed: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        stamp = utc_timestamp()
        seen: set[str] = set()
        with self.write() as connection:
            for candidate in candidates:
                key = norm_key(candidate.title)
                if not key:
                    continue
                rejected = connection.execute(
                    "SELECT title FROM rejected_topics WHERE norm_key = ? AND revoked_at IS NULL",
                    (key,),
                ).fetchone()
                if rejected is not None:
                    suppressed.append(
                        {"title": candidate.title, "reason": f"previously rejected as {rejected['title']!r}"}
                    )
                    continue
                live = connection.execute(
                    "SELECT id, status FROM proposals WHERE norm_key = ? AND status != 'rejected'",
                    (key,),
                ).fetchone()
                if key in seen or live is not None:
                    duplicates.append({"title": candidate.title, "reason": "already a live proposal"})
                    continue
                seen.add(key)
                cursor = connection.execute(
                    "INSERT INTO proposals (subject_id, status, norm_key, created_at, updated_at)"
                    " VALUES (?, 'proposed', ?, ?, ?)",
                    (subject_id, key, stamp, stamp),
                )
                proposal_id = int(cursor.lastrowid or 0)
                version_id = self._insert_version(
                    connection,
                    proposal_id=proposal_id,
                    round_number=1,
                    candidate=candidate,
                    research_run_id=research_run_id,
                    stamp=stamp,
                )
                connection.execute(
                    "UPDATE proposals SET current_version_id = ? WHERE id = ?",
                    (version_id, proposal_id),
                )
                added.append({"id": proposal_id, "title": candidate.title})
        return {"added": added, "suppressed": suppressed, "duplicates": duplicates}

    @staticmethod
    def _insert_version(
        connection: sqlite3.Connection,
        *,
        proposal_id: int,
        round_number: int,
        candidate: ProposalCandidate,
        research_run_id: int | None,
        stamp: str,
    ) -> int:
        cursor = connection.execute(
            "INSERT INTO proposal_versions (proposal_id, round, title, keywords_json, outline,"
            " source_kind, source_refs_json, research_run_id, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (
                proposal_id,
                round_number,
                _single_line(candidate.title, limit=180),
                json.dumps(list(candidate.keywords), ensure_ascii=False),
                candidate.outline.strip()[:2000],
                candidate.source_kind,
                json.dumps(list(candidate.source_refs), ensure_ascii=False),
                research_run_id,
                stamp,
            ),
        )
        return int(cursor.lastrowid or 0)

    def proposal(self, proposal_id: int) -> dict[str, Any]:
        row = self._one("SELECT * FROM proposals WHERE id = ?", (proposal_id,))
        if row is None:
            raise ConsoleDBError(f"no proposal {proposal_id}")
        return self._expand(row)

    def proposals(self, *, statuses: Sequence[str] | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM proposals"
        parameters: list[Any] = []
        if statuses:
            sql += " WHERE status IN (%s)" % ",".join("?" for _ in statuses)
            parameters.extend(statuses)
        sql += " ORDER BY id DESC"
        return [self._expand(row) for row in self._query(sql, parameters)]

    def _expand(self, row: sqlite3.Row) -> dict[str, Any]:
        record = dict(row)
        version = self._one(
            "SELECT * FROM proposal_versions WHERE id = ?", (record["current_version_id"],)
        )
        record["version"] = self._version_payload(version) if version else None
        record["history"] = [
            self._version_payload(item)
            for item in self._query(
                "SELECT * FROM proposal_versions WHERE proposal_id = ? ORDER BY round",
                (record["id"],),
            )
        ]
        record["events"] = [
            dict(item)
            for item in self._query(
                "SELECT * FROM proposal_events WHERE proposal_id = ? ORDER BY id", (record["id"],)
            )
        ]
        subject = self._one("SELECT * FROM subjects WHERE id = ?", (record["subject_id"],))
        record["subject"] = dict(subject) if subject else None
        return record

    @staticmethod
    def _version_payload(row: sqlite3.Row) -> dict[str, Any]:
        payload = dict(row)
        payload["keywords"] = json.loads(payload.pop("keywords_json"))
        payload["source_refs"] = json.loads(payload.pop("source_refs_json"))
        return payload

    def _current_round(self, connection: sqlite3.Connection, proposal_id: int) -> int:
        row = connection.execute(
            "SELECT COALESCE(MAX(round), 0) AS round FROM proposal_versions WHERE proposal_id = ?",
            (proposal_id,),
        ).fetchone()
        return int(row["round"])

    def _record_event(
        self,
        connection: sqlite3.Connection,
        *,
        proposal_id: int,
        action: str,
        actor: str,
        comment: str,
        stamp: str,
    ) -> None:
        connection.execute(
            "INSERT INTO proposal_events (proposal_id, round, action, actor, comment, created_at)"
            " VALUES (?,?,?,?,?,?)",
            (
                proposal_id,
                self._current_round(connection, proposal_id),
                action,
                _single_line(actor, limit=180),
                _single_line(comment, limit=1000),
                stamp,
            ),
        )

    def mark_approved(self, proposal_id: int, actor: str) -> dict[str, Any]:
        """Approve without minting. The caller mints the card, then calls attach_task.

        Split in two so that a crash between them leaves an approved proposal with no
        task_id — a state the caller reconciles by looking for the card — rather than a
        card nobody can trace.
        """
        stamp = utc_timestamp()
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            if row["status"] == "rejected":
                raise ConsoleDBError("a rejected proposal cannot be approved; undo the rejection first")
            if row["status"] in {"approved", "carded"}:
                return dict(row)
            self._record_event(
                connection,
                proposal_id=proposal_id,
                action="approve",
                actor=actor,
                comment="",
                stamp=stamp,
            )
            connection.execute(
                "UPDATE proposals SET status = 'approved', updated_at = ? WHERE id = ?",
                (stamp, proposal_id),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
                ).fetchone()
            )

    def attach_task(self, proposal_id: int, task_id: str) -> dict[str, Any]:
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            if row["task_id"] and row["task_id"] != task_id:
                raise ConsoleDBError(
                    f"proposal {proposal_id} is already carded as {row['task_id']}"
                )
            connection.execute(
                "UPDATE proposals SET task_id = ?, status = 'carded', updated_at = ? WHERE id = ?",
                (task_id, utc_timestamp(), proposal_id),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
                ).fetchone()
            )

    def mark_revising(self, proposal_id: int, comment: str, actor: str) -> dict[str, Any]:
        comment = _single_line(comment, limit=1000)
        if not comment:
            raise ConsoleDBError("suggesting changes needs a comment saying what to change")
        stamp = utc_timestamp()
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            if row["status"] not in {"proposed", "revising"}:
                raise ConsoleDBError(
                    f"a {row['status']} proposal cannot be revised"
                )
            self._record_event(
                connection,
                proposal_id=proposal_id,
                action="suggest",
                actor=actor,
                comment=comment,
                stamp=stamp,
            )
            connection.execute(
                "UPDATE proposals SET status = 'revising', updated_at = ? WHERE id = ?",
                (stamp, proposal_id),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
                ).fetchone()
            )

    def add_revision(
        self,
        proposal_id: int,
        candidate: ProposalCandidate,
        *,
        research_run_id: int | None,
    ) -> dict[str, Any]:
        """Land a revised candidate as a new round. The prior round stays readable."""
        stamp = utc_timestamp()
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            round_number = self._current_round(connection, proposal_id) + 1
            version_id = self._insert_version(
                connection,
                proposal_id=proposal_id,
                round_number=round_number,
                candidate=candidate,
                research_run_id=research_run_id,
                stamp=stamp,
            )
            connection.execute(
                "UPDATE proposals SET current_version_id = ?, status = 'proposed',"
                " norm_key = ?, updated_at = ? WHERE id = ?",
                (version_id, norm_key(candidate.title), stamp, proposal_id),
            )
            return self.proposal(proposal_id)

    def revision_failed(self, proposal_id: int, message: str) -> None:
        """Return to `proposed` at the unchanged round.

        A failed revision must not read as a considered one, so the round does not
        advance and the reason is recorded against the proposal.
        """
        stamp = utc_timestamp()
        with self.write() as connection:
            self._record_event(
                connection,
                proposal_id=proposal_id,
                action="revision-failed",
                actor="system",
                comment=_single_line(message, limit=1000),
                stamp=stamp,
            )
            connection.execute(
                "UPDATE proposals SET status = 'proposed', updated_at = ? WHERE id = ?",
                (stamp, proposal_id),
            )

    def mark_rejected(self, proposal_id: int, reason: str, actor: str) -> dict[str, Any]:
        """Reject and remember. The memory is what stops a re-proposal next Tuesday."""
        stamp = utc_timestamp()
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            if row["status"] in {"approved", "carded"}:
                raise ConsoleDBError(
                    "this proposal is already a board card; reject it on the board, not here"
                )
            version = connection.execute(
                "SELECT * FROM proposal_versions WHERE id = ?", (row["current_version_id"],)
            ).fetchone()
            title = version["title"] if version else ""
            keywords = version["keywords_json"] if version else "[]"
            self._record_event(
                connection,
                proposal_id=proposal_id,
                action="reject",
                actor=actor,
                comment=reason,
                stamp=stamp,
            )
            connection.execute(
                "UPDATE proposals SET status = 'rejected', updated_at = ? WHERE id = ?",
                (stamp, proposal_id),
            )
            connection.execute(
                "INSERT INTO rejected_topics (norm_key, title, keywords_json, reason, actor,"
                " proposal_id, created_at) VALUES (?,?,?,?,?,?,?)"
                " ON CONFLICT(norm_key) DO UPDATE SET revoked_at = NULL, reason = excluded.reason,"
                " actor = excluded.actor, created_at = excluded.created_at",
                (
                    row["norm_key"],
                    title,
                    keywords,
                    _single_line(reason, limit=600),
                    _single_line(actor, limit=180),
                    proposal_id,
                    stamp,
                ),
            )
            return dict(
                connection.execute(
                    "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
                ).fetchone()
            )

    def proposal_for_task(self, task_id: str) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM proposals WHERE task_id = ?", (task_id,))
        return self._expand(row) if row else None

    def import_legacy_card(
        self,
        *,
        task_id: str,
        title: str,
        outline: str,
        submitted_by: str,
        keywords: Sequence[str] = (),
    ) -> dict[str, Any]:
        """Carry a board card that predates this flow back into the proposal queue.

        The card is not deleted; the proposal names it as its source, so the
        "every proposal names a source" rule holds for carried-over rows too.
        """
        subject = self.subject_for(title, submitted_by)
        candidate = ProposalCandidate(
            title=title,
            keywords=tuple(keywords),
            outline=outline,
            source_kind="legacy_board",
            source_refs=(f"board:{task_id}",),
        )
        result = self.add_candidates(
            subject_id=int(subject["id"]), research_run_id=None, candidates=[candidate]
        )
        if not result["added"]:
            return {"imported": False, "task_id": task_id, **result}
        return {"imported": True, "task_id": task_id, "proposal_id": result["added"][0]["id"]}


def summary_counts(database: ConsoleDB) -> Mapping[str, int]:
    counts = {status: 0 for status in PROPOSAL_STATUSES}
    for row in database._query("SELECT status, COUNT(*) AS n FROM proposals GROUP BY status"):
        counts[str(row["status"])] = int(row["n"])
    return counts
