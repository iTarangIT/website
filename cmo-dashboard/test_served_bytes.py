"""What the server actually put on the wire.

Every failure on this console has had the same shape: a test asserting a thing is
*present* — a function name in a module, a string in a constant — rather than that
it *works*. A renderer that produced garbage satisfied all of them, because nothing
executed it, and a build that was never deployed satisfied them too, because nothing
fetched it.

So this suite owns no imports of the render path. It starts `dashboard_server.py`
as a subprocess against a temporary profile, opens a socket, and asserts on the
bytes that come back. If the deploy did not run, or the reader broke, or the tab
order moved, these fail — and they fail for the same reason a human would notice.
"""

from __future__ import annotations

import base64
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = os.getenv("CMO_TEST_PYTHON", sys.executable)
USERNAME = "served-page-test"
PASSWORD = "served-page-test-not-a-secret"

ARTICLE = """---
title: Battery replacement, city by city
slug: battery-replacement
category: financing
---

# Battery replacement, city by city

A rider asking about **replacement cost** wants one number, not a *survey*.

| City | Price band | Wait |
|---|---:|:---:|
| Delhi | **12,000-18,000** | 2 days |
| Jaipur | **11,500-17,000** | 3 days |

> Prices are indicative and need local confirmation.

## Decision bullets:

- **Measure first.** Check Search Console before commissioning more pages.
"""

#: The board parser requires an em dash in the card heading; a hyphen
#: silently yields zero tasks.
BOARD = """# iTarang CMO Task Board

## Backlog

## In Progress

## CMO Review

## Human Approval

### TASK-777 — Battery replacement, city by city
- ID: TASK-777
- Title: Battery replacement, city by city
- Owner: content
- Skill: content
- Priority: high
- Status: Human Approval
- Attachment: artifacts/TASK-777-content.md
- Metric: Organic sessions to the article
- Tag: action to be taken by: human
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

## Completed
"""


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class ServedPageTests(unittest.TestCase):
    """Nothing here touches the render path in-process. Everything is fetched."""

    server: subprocess.Popen | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        (root / "state").mkdir()
        (root / "artifacts").mkdir()
        (root / "logs").mkdir()
        (root / "tasks.md").write_text(BOARD, encoding="utf-8")
        (root / "artifacts" / "TASK-777-content.md").write_text(ARTICLE, encoding="utf-8")
        cls.root = root
        cls.port = free_port()
        environment = {
            **os.environ,
            "CMO_DASHBOARD_PROFILE_DIR": str(root),
            "CMO_DASHBOARD_PORT": str(cls.port),
            "CMO_DASHBOARD_HOST": "127.0.0.1",
            "CMO_DASHBOARD_USERNAME": USERNAME,
            "CMO_DASHBOARD_PASSWORD": PASSWORD,
            # On the deployed tree cmo_runtime sits at the profile root, not beside
            # the dashboard, so an inherited PYTHONPATH has to survive rather than
            # be replaced — otherwise this suite can only ever run from a checkout.
            "PYTHONPATH": os.pathsep.join(
                path for path in (str(HERE), os.environ.get("PYTHONPATH", "")) if path
            ),
        }
        for name in ("GSC_CREDENTIALS_PATH", "GSC_PROPERTY", "GA4_PROPERTY_ID"):
            environment.pop(name, None)
        cls.log = root / "server.log"
        with cls.log.open("wb") as handle:
            cls.server = subprocess.Popen(
                [PYTHON, str(HERE / "dashboard_server.py")],
                cwd=str(HERE), env=environment, stdout=handle, stderr=subprocess.STDOUT,
            )
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            if cls.server.poll() is not None:
                raise AssertionError(
                    "the dashboard exited before serving:\n"
                    + cls.log.read_text(encoding="utf-8", errors="replace")
                )
            try:
                with socket.create_connection(("127.0.0.1", cls.port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.2)
        else:
            raise AssertionError("the dashboard never opened its port")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.server is not None and cls.server.poll() is None:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait(timeout=10)
        cls.temp.cleanup()

    # ---- the wire --------------------------------------------------------

    @classmethod
    def fetch(cls, path: str, *, auth: bool = False) -> tuple[int, dict[str, str], bytes]:
        request = urllib.request.Request(f"http://127.0.0.1:{cls.port}{path}")
        if auth:
            token = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
            request.add_header("Authorization", f"Basic {token}")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def text(self, path: str, *, auth: bool = False) -> str:
        status, _headers, body = self.fetch(path, auth=auth)
        self.assertEqual(status, 200, f"{path} returned {status}")
        return body.decode("utf-8")

    # ---- marker: the build stamp -----------------------------------------

    def test_the_served_page_carries_a_build_stamp_in_its_body(self) -> None:
        page = self.text("/ceo")
        match = re.search(r'<p class="build" id="build-stamp">(.*?)</p>', page, re.S)

        self.assertIsNotNone(match, "the served page has no build stamp")
        stamp = re.sub(r"<[^>]+>", " ", match.group(1))
        self.assertRegex(stamp, r"\d{2} \w{3} \d{4} \d{2}:\d{2}", "no source mtime in the stamp")
        self.assertRegex(stamp, r"\.py\b", "the stamp does not name the newest source file")
        self.assertRegex(stamp, r"page [0-9a-f]{12}", "no page digest in the stamp")
        self.assertNotIn("@@CMO_BUILD_STAMP@@", page, "the placeholder was never substituted")

    def test_the_build_header_matches_the_stamp_on_the_page(self) -> None:
        status, headers, body = self.fetch("/ceo")
        page = body.decode("utf-8")

        self.assertEqual(status, 200)
        self.assertIn("X-CMO-Build", headers)
        digest = re.search(r"page=([0-9a-f]{12})", headers["X-CMO-Build"]).group(1)
        self.assertIn(f"page {digest}", re.sub(r"<[^>]+>", " ", page))

    def test_the_page_digest_is_reproducible_from_the_served_bytes(self) -> None:
        # Swap the rendered stamp back for the placeholder and the same digest
        # must come out — so the number on screen can be checked, not just read.
        import hashlib

        page = self.text("/ceo")
        stamp = re.search(r'<p class="build" id="build-stamp">(.*?)</p>', page, re.S).group(1)
        digest = re.search(r"page ([0-9a-f]{12})", re.sub(r"<[^>]+>", " ", stamp)).group(1)
        restored = page.replace(stamp, "@@CMO_BUILD_STAMP@@")

        self.assertEqual(hashlib.sha256(restored.encode()).hexdigest()[:12], digest)

    def test_the_stamp_moves_when_a_source_file_changes(self) -> None:
        first = self.fetch("/ceo")[1]["X-CMO-Build"]
        target = HERE / "ceo_build.py"
        original = target.stat()
        # The stamp reports the NEWEST *.py, so the bump has to clear every other
        # file in the directory — not just this one's own mtime. Bumping by a fixed
        # two hours passed only while ceo_build.py happened to be among the newest;
        # adding any newer file silently turned this into a test of nothing.
        newest = max(path.stat().st_mtime for path in HERE.glob("*.py"))
        try:
            os.utime(target, (original.st_atime, newest + 7200))
            second = self.fetch("/ceo")[1]["X-CMO-Build"]
        finally:
            os.utime(target, (original.st_atime, original.st_mtime))
        restored = self.fetch("/ceo")[1]["X-CMO-Build"]

        self.assertNotEqual(first, second, "a newer source file did not move the stamp")
        self.assertEqual(first, restored)

    # ---- marker: tab order ------------------------------------------------

    def test_the_served_page_orders_the_tabs_topics_blogs_analytics(self) -> None:
        page = self.text("/ceo")
        nav = page.split('<nav class="primary"', 1)[1].split("</nav>", 1)[0]

        self.assertEqual(re.findall(r'data-view="([a-z-]+)"', nav), ["topics", "blogs", "analytics"])
        self.assertRegex(nav, r'class="active" data-view="topics"')
        self.assertEqual(
            re.findall(r"<kbd>(\d)</kbd>\s*([A-Za-z&; ]+?)<", nav),
            [("1", "Topics &amp; Research"), ("2", "Blogs"), ("3", "Analytics")],
        )

    def test_the_served_page_shows_topics_first_and_hides_the_others(self) -> None:
        page = self.text("/ceo")

        self.assertIn('<section id="panel-topics" class="screen paper">', page)
        self.assertIn('<section id="panel-blogs" class="screen paper" hidden>', page)
        self.assertIn('<section id="panel-analytics" class="screen paper" hidden>', page)

    # ---- marker: the editor ----------------------------------------------

    def test_the_served_page_carries_the_editor_control(self) -> None:
        page = self.text("/ceo")

        self.assertIn('data-reader="edit"', page)
        self.assertIn('id="editor-input"', page)
        self.assertIn('id="editor-preview"', page)
        self.assertIn('data-editor="save"', page)
        self.assertIn('data-editor="cancel"', page)
        self.assertIn("/ceo/api/article/edit", page)
        self.assertIn("/ceo/api/article/preview", page)

    # ---- marker: a rendered article --------------------------------------

    def test_a_served_article_contains_a_real_table_element(self) -> None:
        article = self.text("/api/attachment?task=TASK-777", auth=True)

        self.assertIn("<table", article)
        self.assertIn('<th scope="col">City</th>', article)
        self.assertIn('<th scope="col" class="align-right">Price band</th>', article)
        self.assertIn("<td>Delhi</td>", article)
        self.assertEqual(article.count("<tr>"), 3)

    def test_a_served_article_contains_no_raw_markdown(self) -> None:
        article = self.text("/api/attachment?task=TASK-777", auth=True)
        body = article.split("<body>", 1)[1]

        self.assertNotIn("**", body, "bold reached the page as asterisks")
        self.assertNotIn("| City |", body, "a table row reached the page as text")
        self.assertNotIn("slug:", body, "front matter reached the page")
        self.assertNotIn("category: financing", body)
        self.assertIn("<strong>replacement cost</strong>", body)
        self.assertIn("<em>survey</em>", body)
        self.assertIn("<blockquote>", body)

    def test_the_article_route_refuses_an_unauthenticated_fetch(self) -> None:
        status, _headers, _body = self.fetch("/api/attachment?task=TASK-777")

        self.assertEqual(status, 401)

    # ---- marker: the console updates itself ------------------------------

    def test_the_served_page_polls_one_version_endpoint(self) -> None:
        page = self.text("/ceo")

        self.assertIn("/ceo/api/version", page, "the served page has no change check")
        self.assertIn("POLL_LADDER=[3000,6000,12000,30000]", page,
                      "the served page does not carry the 3s check or its backoff")
        self.assertIn("document.hidden", page, "the served page polls a tab nobody is looking at")

    def test_the_old_sixty_second_reload_is_gone_from_the_served_bytes(self) -> None:
        # Two refreshers fighting each other is worse than either alone, and the
        # one that survives is the one that knows whether anything changed.
        page = self.text("/ceo")

        self.assertNotIn("60000", page, "the blind 60-second refresh is still being served")
        self.assertNotIn("refresh(true),6", page)
        for legacy in ("EventSource", "/api/events"):
            self.assertNotIn(legacy, page, f"a second update mechanism ({legacy}) is being served")

    def test_the_served_page_carries_the_busy_state_for_a_slow_action(self) -> None:
        page = self.text("/ceo")

        self.assertIn('id="topics-pending"', page, "no place for the skeleton to sit")
        self.assertIn("Researching…", page)
        self.assertIn('aria-busy', page, "the busy button announces nothing")
        self.assertIn('class="failure"', page, "a failed action has nowhere to say why")

    def test_the_served_page_carries_keyed_rows_and_arrival_counts(self) -> None:
        page = self.text("/ceo")

        self.assertIn("data-key=", page, "rows are not keyed, so an update cannot patch them")
        self.assertIn('data-badge="blogs"', page, "no count can appear on the Blogs tab")
        self.assertIn('id="topics-new"', page)
        self.assertIn("This article changed elsewhere. Save yours, or reload to see theirs.", page,
                      "the editor has no conflict line")

    def test_the_version_endpoint_is_served_and_refuses_an_unauthenticated_read(self) -> None:
        status, _headers, body = self.fetch("/ceo/api/version")

        self.assertEqual(status, 401, "the change token is readable without a session")
        self.assertIn(b"bearer", body.lower())

    # ---- invariant 8, on the wire ----------------------------------------

    def test_the_served_page_requests_nothing_from_another_host(self) -> None:
        page = self.text("/ceo")

        for marker in ("http://", "https://", "//cdn", "<link", "@import", "<iframe"):
            self.assertNotIn(marker, page, f"the served page references {marker}")

    def test_the_console_boots_without_credentials_rather_than_erroring(self) -> None:
        status, _headers, body = self.fetch("/ceo/api/config")

        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"url": "", "anon_key": ""})


if __name__ == "__main__":
    unittest.main()
