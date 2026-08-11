"""Invariant 5 — the change token is cheap, and it is honest.

Two failure modes, opposite to each other. A token that misses a change leaves
the console stale and Sanchit back on the refresh key, which is the bug this whole
thing exists to remove. A token that costs as much as the page it protects turns
one page load every few minutes into twenty, which is worse than the bug.

So: every watched surface has a test that the token moves when it changes, and
the cost is pinned by proving what the token *does not* read — not by timing it,
which would only ever be flaky.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import ceo_version


class ChangeToken(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "state").mkdir()
        (self.root / "artifacts").mkdir()
        (self.root / "tasks.md").write_text("# board\n\n## Backlog\n", encoding="utf-8")

    def token(self) -> str:
        return ceo_version.version_token(self.root)

    def touch_db(self) -> None:
        """One real commit through the same driver the console writes with."""
        connection = sqlite3.connect(self.root / "state" / "console.db", isolation_level=None)
        try:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("CREATE TABLE IF NOT EXISTS note(text TEXT)")
            connection.execute("INSERT INTO note(text) VALUES ('a card moved')")
        finally:
            connection.close()

    # ---- it moves when something the console shows moves -------------------

    def test_the_token_is_stable_while_nothing_changes(self) -> None:
        self.assertEqual(self.token(), self.token())

    def test_the_token_moves_when_the_board_is_written(self) -> None:
        before = self.token()
        (self.root / "tasks.md").write_text("# board\n\n## Backlog\n\n## Completed\n", encoding="utf-8")

        self.assertNotEqual(before, self.token())

    def test_the_token_moves_when_the_store_commits(self) -> None:
        self.touch_db()
        before = self.token()
        self.touch_db()

        self.assertNotEqual(before, self.token(), "a committed row did not move the token")

    def test_the_token_moves_when_an_artifact_lands(self) -> None:
        before = self.token()
        (self.root / "artifacts" / "TASK-9-content.md").write_text("# a draft\n", encoding="utf-8")

        self.assertNotEqual(before, self.token())

    def test_the_token_moves_when_the_research_queue_is_written(self) -> None:
        before = self.token()
        (self.root / "state" / "ceo-research-queue.json").write_text("[]", encoding="utf-8")

        self.assertNotEqual(before, self.token())

    def test_a_missing_profile_still_answers(self) -> None:
        # The console must not go down because a directory has not been made yet.
        self.assertRegex(ceo_version.version_token(self.root / "not-here"), r"^[0-9a-f]{16}$")

    # ---- and it stays cheap ------------------------------------------------

    def test_the_board_is_never_read_only_stated(self) -> None:
        # Same length, same mtime, different bytes. A token built from a board
        # parse would move; one built from stat cannot, and must not.
        board = self.root / "tasks.md"
        original = board.stat()
        before = self.token()
        board.write_text("# BOARD\n\n## backlog\n", encoding="utf-8")
        self.assertEqual(board.stat().st_size, original.st_size, "rewrite changed the size")
        import os

        os.utime(board, ns=(original.st_atime_ns, original.st_mtime_ns))

        self.assertEqual(self.token(), before, "the token read the board rather than stating it")

    def test_computing_the_token_parses_no_board_and_calls_nothing_outside(self) -> None:
        import analytics_readers
        import console_board
        import urllib.request

        self.touch_db()
        (self.root / "artifacts" / "TASK-9-content.md").write_text("# a draft\n", encoding="utf-8")
        refuse = mock.Mock(side_effect=AssertionError("the version token did this"))

        with mock.patch.object(console_board, "read_board", refuse), \
             mock.patch.object(analytics_readers, "trending_rows", refuse), \
             mock.patch.object(analytics_readers, "ga4_summary", refuse), \
             mock.patch.object(urllib.request, "urlopen", refuse), \
             mock.patch("socket.socket", refuse):
            token = self.token()

        self.assertRegex(token, r"^[0-9a-f]{16}$")
        refuse.assert_not_called()

    def test_the_token_opens_only_the_database_header(self) -> None:
        self.touch_db()
        opened: list[str] = []
        real_open = Path.open

        def watched(self, *args, **kwargs):  # noqa: ANN001
            opened.append(self.name)
            return real_open(self, *args, **kwargs)

        with mock.patch.object(Path, "open", watched):
            self.token()

        self.assertEqual(opened, ["console.db"], f"the token opened files it does not need: {opened}")

    def test_the_parts_name_every_surface_it_watches(self) -> None:
        parts = ceo_version.version_parts(self.root)

        self.assertEqual(sorted(parts), ["artifacts", "db", "state", "tasks", "wal"])


if __name__ == "__main__":
    unittest.main()
