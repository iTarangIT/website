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

SCHEMA_VERSION = 6
DATABASE_NAME = "console.db"

#: `archived` is not a soft rejection. A rejection is remembered by norm_key and
#: suppresses the idea forever; archiving only clears the screen. An archived
#: proposal can be restored by hand, and `add_candidates` below resurfaces one on
#: its own if the same idea comes back through research. Nothing about archiving
#: touches `rejected_topics`.
PROPOSAL_STATUSES = ("proposed", "revising", "approved", "carded", "rejected", "archived")

#: The statuses a norm_key can hold while still blocking a fresh candidate. A
#: rejected key is suppressed outright; an archived one is resurfaced instead, so
#: neither counts as live.
_LIVE_PROPOSAL_STATUSES = tuple(
    status for status in PROPOSAL_STATUSES if status not in {"rejected", "archived"}
)
SOURCE_KINDS = ("search_console", "firecrawl", "cache", "legacy_board")

#: The six stages of writing a blog, in the order Apoorv asked for them, mapped to
#: the position they occupy on the Process tab. One definition, imported by the
#: recorder that writes rows and the read model that renders them, so the two
#: cannot drift into disagreeing about what a stage is called or where it sits.
STAGE_ORDER: dict[str, int] = {
    "topic": 1,
    "keywords": 2,
    "summary": 3,
    "outline": 4,
    "research": 5,
    "writing": 6,
}

#: What a reader sees instead of the slug.
STAGE_LABELS: dict[str, str] = {
    "topic": "Topic selection",
    "keywords": "Keyword selection",
    "summary": "Summary",
    "outline": "Outline",
    "research": "Research",
    "writing": "Writing",
}

STAGE_STATUSES = ("running", "completed", "failed")
FETCH_KINDS = ("search", "scrape", "gsc", "leader")
FETCH_OUTCOMES = ("fetched", "failed", "skipped", "cached")
LEADER_KINDS = ("organisation", "person")
#: The platforms a published article is cross-posted to, in console order.
#: Facebook is absent because the organisation has no Facebook channel connected
#: in Buffer, and a platform with no channel is a row that can only say so.
#: Buffer calls X `twitter`; the mapping lives in `buffer_client`.
CROSSPOST_PLATFORMS = ("linkedin", "x", "instagram")

#: A draft's life. `draft` is written the moment copy exists; `queued` means
#: Buffer accepted it and holds a post id; `failed` keeps the reason on the row
#: so the console can show it beside a Retry rather than losing it to a log.
CROSSPOST_STATUSES = ("draft", "queued", "failed")

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
    created_at  TEXT NOT NULL,
    -- Which beat of the news radar produced this subject, empty for one typed in
    -- by hand. Added in schema 4; `_add_column` backfills existing databases,
    -- where every row predates the radar and correctly reads as hand-entered.
    beat        TEXT NOT NULL DEFAULT ''
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
    -- The measured demand behind this pass, as JSON: impressions, clicks, the
    -- derived CTR and the impression-weighted position. Empty string means no
    -- rows matched, which is a different fact from zero demand and is rendered
    -- as such. Added in schema 5; `_add_column` backfills existing databases.
    demand_json      TEXT NOT NULL DEFAULT '',
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

-- The people and organisations whose published work feeds research. Declared
-- before `stage_fetches` because that table points at it, and foreign keys are on.
CREATE TABLE IF NOT EXISTS leaders (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    org         TEXT NOT NULL DEFAULT '',
    kind        TEXT NOT NULL,          -- organisation|person
    source_url  TEXT NOT NULL,
    active      INTEGER NOT NULL DEFAULT 1,
    note        TEXT NOT NULL DEFAULT '',
    added_by    TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS leaders_source ON leaders(source_url);

-- One row per pipeline stage that actually ran. A stage is opened in one
-- transaction and closed in another, so a process killed mid-run leaves every
-- finished stage committed and the interrupted one readable as 'running'. The
-- console draws these rows and nothing else: a stage with no row is not drawn.
CREATE TABLE IF NOT EXISTS pipeline_stages (
    id           INTEGER PRIMARY KEY,
    task_id      TEXT NOT NULL DEFAULT '',
    proposal_id  INTEGER REFERENCES proposals(id),
    stage        TEXT NOT NULL,
    ordinal      INTEGER NOT NULL,
    attempt      INTEGER NOT NULL DEFAULT 1,
    status       TEXT NOT NULL,         -- running|completed|failed
    started_at   TEXT NOT NULL,
    ended_at     TEXT,
    duration_ms  INTEGER,
    summary      TEXT NOT NULL DEFAULT '',
    detail_json  TEXT NOT NULL DEFAULT '{}'
);
-- Two partial indexes, not one: the topic-side stages are recorded against a
-- proposal before any card exists, and only acquire a task_id when the proposal
-- is carded.
CREATE UNIQUE INDEX IF NOT EXISTS pipeline_stages_task
    ON pipeline_stages(task_id, stage, attempt) WHERE task_id <> '';
CREATE INDEX IF NOT EXISTS pipeline_stages_proposal
    ON pipeline_stages(proposal_id) WHERE proposal_id IS NOT NULL;

-- The fetch ledger. Every attempt to read something, including the ones that
-- failed. This is the only table the research stage's source list may be built
-- from — a URL that reaches the console without a row here was never fetched.
CREATE TABLE IF NOT EXISTS stage_fetches (
    id             INTEGER PRIMARY KEY,
    stage_id       INTEGER NOT NULL REFERENCES pipeline_stages(id),
    kind           TEXT NOT NULL,        -- search|scrape|gsc|leader
    query          TEXT NOT NULL DEFAULT '',
    url            TEXT NOT NULL DEFAULT '',
    title          TEXT NOT NULL DEFAULT '',
    published_date TEXT NOT NULL DEFAULT '',
    accessed_at    TEXT NOT NULL,
    outcome        TEXT NOT NULL,        -- fetched|failed|skipped|cached
    message        TEXT NOT NULL DEFAULT '',
    leader_id      INTEGER REFERENCES leaders(id),
    credits        INTEGER
);
CREATE INDEX IF NOT EXISTS stage_fetches_stage ON stage_fetches(stage_id);

CREATE TABLE IF NOT EXISTS crosspost_drafts (
    id                  INTEGER PRIMARY KEY,
    task_id             TEXT NOT NULL,
    platform            TEXT NOT NULL,
    body                TEXT NOT NULL,
    link                TEXT NOT NULL,
    article_fingerprint TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    thread_json         TEXT NOT NULL DEFAULT '[]',
    image_alt           TEXT NOT NULL DEFAULT '',
    producer            TEXT NOT NULL DEFAULT 'composed',  -- writer|composed
    status              TEXT NOT NULL DEFAULT 'draft',     -- draft|queued|failed
    channel_id          TEXT NOT NULL DEFAULT '',
    buffer_post_id      TEXT NOT NULL DEFAULT '',
    scheduled_at        TEXT NOT NULL DEFAULT '',
    sent_by             TEXT NOT NULL DEFAULT '',
    sent_at             TEXT NOT NULL DEFAULT '',
    error               TEXT NOT NULL DEFAULT '',
    updated_at          TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS crosspost_drafts_key
    ON crosspost_drafts(task_id, platform);

CREATE TABLE IF NOT EXISTS radar_runs (
    id              INTEGER PRIMARY KEY,
    started_at      TEXT NOT NULL,
    mode            TEXT NOT NULL,          -- due|forced|manual|dry-run
    beats_json      TEXT NOT NULL DEFAULT '[]',
    -- The beats searched that returned nothing new. Added in schema 4; rows from
    -- before it read as an empty list, which is honestly "not recorded" rather
    -- than a claim that every beat delivered.
    empty_beats_json TEXT NOT NULL DEFAULT '[]',
    headlines_seen  INTEGER NOT NULL DEFAULT 0,
    subjects_json   TEXT NOT NULL DEFAULT '[]',
    proposals_added INTEGER NOT NULL DEFAULT 0,
    credits_used    INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL,          -- completed|refused|failed
    message         TEXT NOT NULL DEFAULT ''
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
        # `CREATE TABLE IF NOT EXISTS` is a no-op on a database that already has the
        # table, so a column added to the schema above never reaches one. Every such
        # column needs a line here as well, and both must agree.
        self._add_column("subjects", "beat", "TEXT NOT NULL DEFAULT ''")
        self._add_column("radar_runs", "empty_beats_json", "TEXT NOT NULL DEFAULT '[]'")
        self._add_column("research_runs", "demand_json", "TEXT NOT NULL DEFAULT ''")
        for column, declaration in (
            ("thread_json", "TEXT NOT NULL DEFAULT '[]'"),
            ("image_alt", "TEXT NOT NULL DEFAULT ''"),
            ("producer", "TEXT NOT NULL DEFAULT 'composed'"),
            ("status", "TEXT NOT NULL DEFAULT 'draft'"),
            ("channel_id", "TEXT NOT NULL DEFAULT ''"),
            ("buffer_post_id", "TEXT NOT NULL DEFAULT ''"),
            ("scheduled_at", "TEXT NOT NULL DEFAULT ''"),
            ("sent_by", "TEXT NOT NULL DEFAULT ''"),
            ("sent_at", "TEXT NOT NULL DEFAULT ''"),
            ("error", "TEXT NOT NULL DEFAULT ''"),
            ("updated_at", "TEXT NOT NULL DEFAULT ''"),
        ):
            self._add_column("crosspost_drafts", column, declaration)
        self._connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def _add_column(self, table: str, column: str, declaration: str) -> None:
        """Add a column to an existing table, once. Safe to run on every open."""
        present = {
            row["name"] for row in self._connection.execute(f"PRAGMA table_info({table})")
        }
        if column in present:
            return
        self._connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")

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

    def subject_for(self, raw_text: str, actor: str, beat: str = "") -> dict[str, Any]:
        """Get or create the subject row. The norm_key is what makes the cache work.

        `beat` names the radar beat that produced the subject, and is empty for one
        a human typed in. A subject that already exists keeps everything about
        itself except an empty beat: the radar finding a subject somebody had
        already entered by hand is the one case where we learn something new about
        a row that is otherwise unchanged.
        """
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
            beat = _single_line(beat, limit=60)
            existing = connection.execute(
                "SELECT * FROM subjects WHERE norm_key = ?", (key,)
            ).fetchone()
            if existing is not None:
                if beat and not str(existing["beat"] or "").strip():
                    connection.execute(
                        "UPDATE subjects SET beat = ? WHERE id = ?", (beat, existing["id"])
                    )
                    existing = connection.execute(
                        "SELECT * FROM subjects WHERE id = ?", (existing["id"],)
                    ).fetchone()
                return dict(existing)
            cursor = connection.execute(
                "INSERT INTO subjects (raw_text, norm_key, actor, created_at, beat)"
                " VALUES (?, ?, ?, ?, ?)",
                (text, key, actor, utc_timestamp(), beat),
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
        demand: Mapping[str, Any] | None = None,
        cache_hit_of: int | None = None,
        message: str = "",
    ) -> int:
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO research_runs (subject_id, kind, pages_requested, pages_fetched,"
                " credits_before, credits_after, credits_used, credits_remaining, gsc_rows_used,"
                " demand_json, cache_hit_of, status, message, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
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
                    json.dumps(dict(demand), sort_keys=True) if demand else "",
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

    # ------------------------------------------------------------ news radar

    def record_radar_run(
        self,
        *,
        started_at: str,
        mode: str,
        beats: Sequence[str],
        headlines_seen: int,
        empty_beats: Sequence[str] = (),
        subjects: Sequence[str],
        proposals_added: int,
        credits_used: int,
        status: str,
        message: str = "",
    ) -> int:
        """One row per sweep, refusals included.

        A refused sweep that left no trace reads as a sweep that never ran, and the
        console cannot tell an operator why nothing new appeared this morning.
        """
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO radar_runs (started_at, mode, beats_json, empty_beats_json,"
                " headlines_seen, subjects_json, proposals_added, credits_used, status, message)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    started_at,
                    _single_line(mode, limit=40),
                    json.dumps([str(beat) for beat in beats], ensure_ascii=False),
                    json.dumps([str(beat) for beat in empty_beats], ensure_ascii=False),
                    int(headlines_seen),
                    json.dumps([str(subject) for subject in subjects], ensure_ascii=False),
                    int(proposals_added),
                    int(credits_used),
                    _single_line(status, limit=40),
                    _single_line(message, limit=1000),
                ),
            )
            return int(cursor.lastrowid or 0)

    def latest_radar_run(self) -> dict[str, Any] | None:
        row = self._one("SELECT * FROM radar_runs ORDER BY id DESC LIMIT 1")
        if row is None:
            return None
        record = dict(row)
        record["beats"] = json.loads(record.pop("beats_json"))
        record["empty_beats"] = json.loads(record.pop("empty_beats_json", None) or "[]")
        record["subjects"] = json.loads(record.pop("subjects_json"))
        return record

    def radar_seen_urls(self, *, limit: int = 400) -> set[str]:
        """URLs the pipeline has already fetched, so a sweep does not re-read them."""
        rows = self._query(
            "SELECT url FROM stage_fetches WHERE url != '' ORDER BY id DESC LIMIT ?", (int(limit),)
        )
        return {str(row["url"]) for row in rows}

    # ------------------------------------------------------- pipeline stages

    def start_stage(
        self,
        stage: str,
        *,
        task_id: str = "",
        proposal_id: int | None = None,
        attempt: int = 1,
        started_at: str | None = None,
    ) -> int:
        """Open a stage. Its own transaction, so it is durable before work begins.

        The row is written *before* the work runs and closed afterwards. That is
        the whole crash story: a process killed halfway leaves this row saying
        `running` with a start time, which is both the honest record and exactly
        what the console needs to show elapsed time against.
        """
        if stage not in STAGE_ORDER:
            raise ConsoleDBError(f"unknown pipeline stage: {stage!r}")
        if not task_id and proposal_id is None:
            raise ConsoleDBError(f"stage {stage!r} names neither a task nor a proposal")
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO pipeline_stages (task_id, proposal_id, stage, ordinal, attempt,"
                " status, started_at) VALUES (?,?,?,?,?,'running',?)",
                (
                    task_id,
                    proposal_id,
                    stage,
                    STAGE_ORDER[stage],
                    attempt,
                    started_at or utc_timestamp(),
                ),
            )
            return int(cursor.lastrowid or 0)

    def finish_stage(
        self,
        stage_id: int,
        *,
        status: str = "completed",
        summary: str = "",
        detail: Mapping[str, Any] | None = None,
        duration_ms: int | None = None,
    ) -> None:
        """Close a stage. A separate transaction from `start_stage` on purpose."""
        if status not in STAGE_STATUSES or status == "running":
            raise ConsoleDBError(f"cannot finish a stage as {status!r}")
        with self.write() as connection:
            connection.execute(
                "UPDATE pipeline_stages SET status = ?, ended_at = ?, duration_ms = ?,"
                " summary = ?, detail_json = ? WHERE id = ?",
                (
                    status,
                    utc_timestamp(),
                    duration_ms,
                    _single_line(summary, limit=600),
                    json.dumps(detail or {}, ensure_ascii=False),
                    stage_id,
                ),
            )

    def record_fetch(
        self,
        stage_id: int,
        *,
        kind: str,
        outcome: str,
        url: str = "",
        query: str = "",
        title: str = "",
        published_date: str = "",
        accessed_at: str = "",
        message: str = "",
        leader_id: int | None = None,
        credits: int | None = None,
    ) -> int:
        """Log one attempt to read something. Failures are rows too, not silence."""
        if kind not in FETCH_KINDS:
            raise ConsoleDBError(f"unknown fetch kind: {kind!r}")
        if outcome not in FETCH_OUTCOMES:
            raise ConsoleDBError(f"unknown fetch outcome: {outcome!r}")
        if not url.strip() and not query.strip():
            raise ConsoleDBError("a fetch record names neither a URL nor a query")
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO stage_fetches (stage_id, kind, query, url, title, published_date,"
                " accessed_at, outcome, message, leader_id, credits) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    stage_id,
                    kind,
                    _single_line(query, limit=300),
                    _single_line(url, limit=2000),
                    _single_line(title, limit=300),
                    _single_line(published_date, limit=100),
                    accessed_at or utc_timestamp(),
                    outcome,
                    _single_line(message, limit=600),
                    leader_id,
                    credits,
                ),
            )
            return int(cursor.lastrowid or 0)

    def next_attempt(self, stage: str, *, task_id: str = "", proposal_id: int | None = None) -> int:
        """The attempt number a fresh run of this stage should carry.

        Nine failed generations are nine rows. A retry that overwrote its
        predecessor would make the board say the writer succeeded first time.
        """
        if task_id:
            row = self._one(
                "SELECT MAX(attempt) AS highest FROM pipeline_stages WHERE task_id = ? AND stage = ?",
                (task_id, stage),
            )
        else:
            row = self._one(
                "SELECT MAX(attempt) AS highest FROM pipeline_stages"
                " WHERE proposal_id = ? AND stage = ?",
                (proposal_id, stage),
            )
        highest = row["highest"] if row else None
        return int(highest or 0) + 1

    def bind_stages_to_task(self, proposal_id: int, task_id: str) -> int:
        """Give the topic-side stages the card they turned out to belong to.

        Stages 1-3 run before a card exists — that is the point of the topic flow.
        They are recorded against the proposal and claimed here, at the moment
        approval mints the card.
        """
        with self.write() as connection:
            cursor = connection.execute(
                "UPDATE pipeline_stages SET task_id = ? WHERE proposal_id = ? AND task_id = ''",
                (task_id, proposal_id),
            )
            return cursor.rowcount

    def stages_for_task(self, task_id: str) -> list[dict[str, Any]]:
        """Every recorded stage for one card, in reading order, with its fetches.

        Only rows. Nothing here infers a stage that has no row, which is what
        keeps the Process tab honest about what actually ran.
        """
        if not task_id:
            return []
        rows = self._query(
            "SELECT * FROM pipeline_stages WHERE task_id = ? ORDER BY ordinal, attempt, id",
            (task_id,),
        )
        if not rows:
            return []
        fetches: dict[int, list[dict[str, Any]]] = {}
        placeholders = ",".join("?" for _ in rows)
        for fetch in self._query(
            f"SELECT * FROM stage_fetches WHERE stage_id IN ({placeholders}) ORDER BY id",
            [row["id"] for row in rows],
        ):
            fetches.setdefault(int(fetch["stage_id"]), []).append(dict(fetch))
        return [self._stage_payload(row, fetches.get(int(row["id"]), [])) for row in rows]

    @staticmethod
    def _stage_payload(row: sqlite3.Row, fetches: list[dict[str, Any]]) -> dict[str, Any]:
        try:
            detail = json.loads(row["detail_json"])
        except (TypeError, ValueError):
            detail = {}
        return {
            **dict(row),
            "label": STAGE_LABELS.get(row["stage"], row["stage"]),
            "detail": detail if isinstance(detail, dict) else {},
            "fetches": fetches,
        }

    # --------------------------------------------------------------- leaders

    def add_leader(
        self,
        *,
        name: str,
        kind: str,
        source_url: str,
        org: str = "",
        note: str = "",
        added_by: str,
        active: bool = True,
    ) -> int:
        """Insert one tracked source, or return the existing row for that URL."""
        if kind not in LEADER_KINDS:
            raise ConsoleDBError(f"unknown leader kind: {kind!r}")
        if not name.strip():
            raise ConsoleDBError("a leader with no name is not a leader")
        if not source_url.strip():
            raise ConsoleDBError(f"{name!r} names no source URL")
        existing = self._one("SELECT id FROM leaders WHERE source_url = ?", (source_url,))
        if existing is not None:
            return int(existing["id"])
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO leaders (name, org, kind, source_url, active, note, added_by,"
                " created_at) VALUES (?,?,?,?,?,?,?,?)",
                (
                    _single_line(name, limit=200),
                    _single_line(org, limit=200),
                    kind,
                    _single_line(source_url, limit=2000),
                    1 if active else 0,
                    _single_line(note, limit=400),
                    added_by,
                    utc_timestamp(),
                ),
            )
            return int(cursor.lastrowid or 0)

    def leaders(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        sql = "SELECT * FROM leaders"
        if active_only:
            sql += " WHERE active = 1"
        return [dict(row) for row in self._query(sql + " ORDER BY kind, org, name")]

    # ------------------------------------------------------ crosspost drafts

    def save_crosspost_draft(
        self,
        *,
        task_id: str,
        platform: str,
        body: str,
        link: str,
        article_fingerprint: str,
        thread: Sequence[str] = (),
        image_alt: str = "",
        producer: str = "composed",
    ) -> int:
        """Write or replace one platform's draft, without disturbing a sent post.

        Regenerating copy for an article whose LinkedIn post has already been
        queued must not quietly reset that row to `draft` — the post exists on
        LinkedIn either way, and a console that forgot would offer to send it
        again. So the send columns are left exactly as they are and only the copy
        is replaced.
        """
        if platform not in CROSSPOST_PLATFORMS:
            raise ConsoleDBError(f"unknown cross-post platform: {platform!r}")
        if producer not in ("writer", "composed"):
            raise ConsoleDBError(f"unknown cross-post producer: {producer!r}")
        now = utc_timestamp()
        with self.write() as connection:
            cursor = connection.execute(
                "INSERT INTO crosspost_drafts (task_id, platform, body, link,"
                " article_fingerprint, created_at, thread_json, image_alt, producer,"
                " status, updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,'draft',?)"
                " ON CONFLICT(task_id, platform) DO UPDATE SET body = excluded.body,"
                " link = excluded.link, article_fingerprint = excluded.article_fingerprint,"
                " thread_json = excluded.thread_json, image_alt = excluded.image_alt,"
                " producer = excluded.producer, updated_at = excluded.updated_at",
                (
                    task_id,
                    platform,
                    body,
                    link,
                    article_fingerprint,
                    now,
                    json.dumps(list(thread)),
                    image_alt,
                    producer,
                    now,
                ),
            )
            return int(cursor.lastrowid or 0)

    def mark_crosspost_queued(
        self,
        *,
        task_id: str,
        platform: str,
        channel_id: str,
        buffer_post_id: str,
        scheduled_at: str,
        actor: str,
    ) -> None:
        """Record that Buffer took the post, and who pressed the button."""
        with self.write() as connection:
            connection.execute(
                "UPDATE crosspost_drafts SET status = 'queued', channel_id = ?,"
                " buffer_post_id = ?, scheduled_at = ?, sent_by = ?, sent_at = ?,"
                " error = '', updated_at = ? WHERE task_id = ? AND platform = ?",
                (
                    channel_id,
                    buffer_post_id,
                    scheduled_at,
                    actor,
                    utc_timestamp(),
                    utc_timestamp(),
                    task_id,
                    platform,
                ),
            )

    def mark_crosspost_failed(self, *, task_id: str, platform: str, error: str) -> None:
        """Keep the refusal on the row. A reason in a log file is a reason nobody reads."""
        now = utc_timestamp()
        with self.write() as connection:
            connection.execute(
                "UPDATE crosspost_drafts SET status = 'failed', error = ?, updated_at = ?"
                " WHERE task_id = ? AND platform = ?",
                (_single_line(error, limit=600), now, task_id, platform),
            )

    def crosspost_drafts(self, task_id: str) -> list[dict[str, Any]]:
        """Every draft for one article, in console platform order with the thread parsed."""
        if not task_id:
            return []
        order = {platform: index for index, platform in enumerate(CROSSPOST_PLATFORMS)}
        rows = []
        for row in self._query("SELECT * FROM crosspost_drafts WHERE task_id = ?", (task_id,)):
            item = dict(row)
            try:
                thread = json.loads(item.get("thread_json") or "[]")
            except json.JSONDecodeError:
                thread = []
            item["thread"] = [str(part) for part in thread] if isinstance(thread, list) else []
            item.pop("thread_json", None)
            rows.append(item)
        rows.sort(key=lambda item: order.get(str(item.get("platform")), 99))
        return rows

    def crosspost_summary(self) -> dict[str, int]:
        """How many drafts sit in each status, for the tab badge."""
        counts = {status: 0 for status in CROSSPOST_STATUSES}
        for row in self._query(
            "SELECT status, COUNT(*) AS n FROM crosspost_drafts GROUP BY status", ()
        ):
            counts[str(row["status"])] = int(row["n"])
        return counts

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
        actor: str = "research",
    ) -> dict[str, list[dict[str, Any]]]:
        """Insert candidates, suppressing anything Sanchit already rejected.

        Suppression is reported, never silent — an operator who cannot see why an
        obvious topic never appears will assume the agent is broken. The same rule
        covers the archive: an archived candidate that research finds again is
        resurfaced and reported, because archiving was never a veto.
        """
        added: list[dict[str, Any]] = []
        suppressed: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        resurfaced: list[dict[str, Any]] = []
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
                if key in seen:
                    duplicates.append({"title": candidate.title, "reason": "already a live proposal"})
                    continue
                placeholders = ",".join("?" for _ in _LIVE_PROPOSAL_STATUSES)
                live = connection.execute(
                    f"SELECT id, status FROM proposals WHERE norm_key = ?"
                    f" AND status IN ({placeholders})",
                    (key, *_LIVE_PROPOSAL_STATUSES),
                ).fetchone()
                if live is not None:
                    duplicates.append({"title": candidate.title, "reason": "already a live proposal"})
                    continue
                # An archived row is not a veto, so research finding the idea again
                # brings it back rather than silently dropping it as a duplicate.
                shelved = connection.execute(
                    "SELECT id FROM proposals WHERE norm_key = ? AND status = 'archived'",
                    (key,),
                ).fetchone()
                if shelved is not None:
                    proposal_id = int(shelved["id"])
                    connection.execute(
                        "UPDATE proposals SET status = 'proposed', updated_at = ? WHERE id = ?",
                        (stamp, proposal_id),
                    )
                    self._record_event(
                        connection,
                        proposal_id=proposal_id,
                        action="resurface",
                        actor=actor,
                        comment="research surfaced this archived topic again",
                        stamp=stamp,
                    )
                    seen.add(key)
                    resurfaced.append({"id": proposal_id, "title": candidate.title})
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
        return {
            "added": added,
            "suppressed": suppressed,
            "duplicates": duplicates,
            "resurfaced": resurfaced,
        }

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
        # The demand figures belong to the research pass the current version came
        # out of, so they are read through that join rather than copied onto every
        # candidate the pass produced. A version from before schema 5, or one whose
        # pass matched no Search Console rows, carries `{}` -- which the console
        # renders as "no data", never as zero.
        record["demand"] = self._demand_for(record["version"])
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

    def _demand_for(self, version: dict[str, Any] | None) -> dict[str, Any]:
        if not version or not version.get("research_run_id"):
            return {}
        run = self._one(
            "SELECT demand_json FROM research_runs WHERE id = ?", (version["research_run_id"],)
        )
        if run is None:
            return {}
        try:
            decoded = json.loads(run["demand_json"] or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}
        return decoded if isinstance(decoded, dict) else {}

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
            # The topic-side stages ran before this card existed, which is the
            # point of the topic flow. They are claimed here, inside the same
            # transaction that mints the card, so no caller can card a proposal
            # and forget to bring its recorded work along.
            connection.execute(
                "UPDATE pipeline_stages SET task_id = ? WHERE proposal_id = ? AND task_id = ''",
                (task_id, proposal_id),
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

    def archive_siblings(self, proposal_id: int, actor: str) -> list[dict[str, Any]]:
        """Clear the candidates left over from the same subject, reversibly.

        One subject fans out to up to six candidates and only one of them becomes a
        card. The rest are not wrong — they are simply not the decision that was
        made — so they are set aside, not vetoed. Nothing here writes to
        `rejected_topics`; `restore_proposal` below is the way back.
        """
        stamp = utc_timestamp()
        archived: list[dict[str, Any]] = []
        with self.write() as connection:
            row = connection.execute(
                "SELECT subject_id FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            siblings = connection.execute(
                "SELECT p.id AS id, v.title AS title FROM proposals p"
                " LEFT JOIN proposal_versions v ON v.id = p.current_version_id"
                " WHERE p.subject_id = ? AND p.id != ? AND p.status IN ('proposed','revising')"
                " ORDER BY p.id",
                (int(row["subject_id"]), proposal_id),
            ).fetchall()
            for sibling in siblings:
                sibling_id = int(sibling["id"])
                connection.execute(
                    "UPDATE proposals SET status = 'archived', updated_at = ? WHERE id = ?",
                    (stamp, sibling_id),
                )
                self._record_event(
                    connection,
                    proposal_id=sibling_id,
                    action="archive",
                    actor=actor,
                    comment=f"set aside when proposal {proposal_id} was approved",
                    stamp=stamp,
                )
                archived.append({"id": sibling_id, "title": sibling["title"] or ""})
        return archived

    def archive_proposal(self, proposal_id: int, actor: str) -> dict[str, Any]:
        """Set one candidate aside by hand. Same reversibility as the sweep above."""
        stamp = utc_timestamp()
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            if row["status"] not in {"proposed", "revising"}:
                raise ConsoleDBError(
                    f"proposal {proposal_id} is {row['status']}, so there is nothing to archive"
                )
            connection.execute(
                "UPDATE proposals SET status = 'archived', updated_at = ? WHERE id = ?",
                (stamp, proposal_id),
            )
            self._record_event(
                connection,
                proposal_id=proposal_id,
                action="archive",
                actor=actor,
                comment="set aside from Topics",
                stamp=stamp,
            )
            return dict(
                connection.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
            )

    def restore_proposal(self, proposal_id: int, actor: str) -> dict[str, Any]:
        """Bring an archived candidate back to the pool it came from."""
        stamp = utc_timestamp()
        with self.write() as connection:
            row = connection.execute(
                "SELECT * FROM proposals WHERE id = ?", (proposal_id,)
            ).fetchone()
            if row is None:
                raise ConsoleDBError(f"no proposal {proposal_id}")
            if row["status"] != "archived":
                raise ConsoleDBError(
                    f"proposal {proposal_id} is {row['status']}, not archived; there is nothing to restore"
                )
            connection.execute(
                "UPDATE proposals SET status = 'proposed', updated_at = ? WHERE id = ?",
                (stamp, proposal_id),
            )
            self._record_event(
                connection,
                proposal_id=proposal_id,
                action="restore",
                actor=actor,
                comment="restored from Archived",
                stamp=stamp,
            )
            return dict(
                connection.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
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
