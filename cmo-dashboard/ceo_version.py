"""One cheap token that changes when the console's data changes.

The console has to notice work done by something else — the writer finishing an
article, cold review escalating a card, the hourly cycle rewriting the board —
without Sanchit pressing refresh. The cheapest honest way to do that is to let
the client ask "has anything changed?" far more often than it asks "what is
everything?", so this module answers only the first question.

What it reads, and why each one:

- ``tasks.md`` — mtime and size. Every board write lands here.
- ``state/console.db`` — SQLite's own file change counter (four big-endian bytes
  at offset 24 of the header), plus the ``-wal`` sidecar's mtime and size. The
  header counter only advances at checkpoint under WAL, and the WAL only exists
  between checkpoints, so the two together cover both halves of the cycle.
- ``artifacts/`` — the newest entry and how many there are. A new draft file is a
  change the board may not have caught up with yet.
- ``state/*.json`` — the small console-owned files: the research queue, the
  watchlist. Changed from the Analytics tab or by the agent, and visible on screen.

What it deliberately does not do: no Firecrawl, no Search Console, no GA4, no
network of any kind, and no board parse. Computing the token must not cost more
than serving the page it is protecting — this is a handful of ``stat`` calls, two
shallow directory scans and a 28-byte read.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

#: SQLite's header layout: bytes 24..28 hold the file change counter.
_CHANGE_COUNTER_OFFSET = 24
_HEADER_BYTES = 28

__all__ = ["version_parts", "version_token", "version_payload"]


def _stat_key(path: Path) -> str:
    """mtime and size for one file, or a marker when it is not there yet."""
    try:
        info = path.stat()
    except OSError:
        return "-"
    return f"{info.st_mtime_ns}.{info.st_size}"


def _change_counter(database: Path) -> int:
    """SQLite's own commit counter, read straight out of the file header."""
    try:
        with database.open("rb") as handle:
            header = handle.read(_HEADER_BYTES)
    except OSError:
        return 0
    if len(header) < _HEADER_BYTES:
        return 0
    return int.from_bytes(header[_CHANGE_COUNTER_OFFSET:_HEADER_BYTES], "big")


def _newest(directory: Path, suffix: str = "") -> str:
    """The newest entry in one directory, and how many entries it holds.

    One ``scandir``, no recursion, no file reads. ``st_mtime_ns`` comes off the
    directory entry cache on Linux, so this stays a single syscall per name.
    """
    newest = 0
    count = 0
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if suffix and not entry.name.endswith(suffix):
                    continue
                try:
                    modified = entry.stat(follow_symlinks=False).st_mtime_ns
                except OSError:
                    continue
                count += 1
                if modified > newest:
                    newest = modified
    except OSError:
        return "-"
    return f"{newest}.{count}"


def version_parts(profile_dir: Path) -> dict[str, str]:
    """The individual facts the token is built from — useful when it misbehaves."""
    profile = Path(profile_dir)
    database = profile / "state" / "console.db"
    return {
        "tasks": _stat_key(profile / "tasks.md"),
        "db": f"{_change_counter(database)}.{_stat_key(database)}",
        "wal": _stat_key(profile / "state" / "console.db-wal"),
        "artifacts": _newest(profile / "artifacts"),
        "state": _newest(profile / "state", ".json"),
    }


def version_token(profile_dir: Path) -> str:
    """A short token that differs whenever any watched fact differs."""
    parts = version_parts(profile_dir)
    joined = "|".join(f"{name}={parts[name]}" for name in sorted(parts))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def version_payload(profile_dir: Path) -> dict[str, object]:
    """What ``GET /ceo/api/version`` returns."""
    parts = version_parts(profile_dir)
    joined = "|".join(f"{name}={parts[name]}" for name in sorted(parts))
    return {
        "version": hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16],
        "parts": parts,
    }
