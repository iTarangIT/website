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
import http.server
import json
import os
import re
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
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

### TASK-778 — What a battery repair actually costs
- ID: TASK-778
- Title: What a battery repair actually costs
- Owner: content
- Skill: content
- Priority: medium
- Status: Backlog
- Attachment: none
- Metric: Organic sessions to the article
- Tag: action to be taken by: cmo
- Topic stage: approved
- Change status: write failed
- Latest summary: writer article has 1742 words; WRITER_CONTRACT requires 900-1,400
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

### TASK-782 — A failed write the retry test consumes
- ID: TASK-782
- Title: A failed write the retry test consumes
- Owner: content
- Skill: content
- Priority: medium
- Status: Backlog
- Attachment: none
- Metric: Organic sessions to the article
- Tag: action to be taken by: cmo
- Topic stage: approved
- Change status: write failed
- Latest summary: Hermes writer exited 1
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

### TASK-781 — A topic a human parked
- ID: TASK-781
- Title: A topic a human parked
- Owner: content
- Skill: content
- Priority: medium
- Status: Backlog
- Attachment: none
- Metric: Organic sessions to the article
- Tag: action to be taken by: cmo
- Topic stage: approved
- Change status: blocked
- Latest summary: Held behind the card above by CEO instruction
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

### TASK-780 — An approved topic nobody has started
- ID: TASK-780
- Title: An approved topic nobody has started
- Owner: content
- Skill: content
- Priority: medium
- Status: Backlog
- Attachment: none
- Metric: Organic sessions to the article
- Tag: action to be taken by: cmo
- Topic stage: approved
- Change status: queued
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

## In Progress

## CMO Review

## Human Approval

### TASK-779 — Charging habits that shorten a pack's life
- ID: TASK-779
- Title: Charging habits that shorten a pack's life
- Owner: content
- Skill: content
- Priority: medium
- Status: Human Approval
- Attachment: artifacts/TASK-779-content.md
- Metric: Organic sessions to the article
- Tag: action to be taken by: human
- Change status: published to cmo-changes
- Preview URL: https://itarangwebsite.vercel.app/blog/charging-habits
- Revision round: 0
- Last updated: 2026-08-11T00:00:00Z
- Updated: 2026-08-11T00:00:00Z

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


def seed_recorded_stages(root: Path) -> None:
    """Record three of the six stages for TASK-777, the way a real run would.

    The store is used rather than hand-written SQL: a fixture that builds rows by
    hand drifts from the writer that builds them for real, and then the tab passes
    against a shape nothing produces. This is not the render path — the suite still
    imports none of that, and reads everything back over a socket.

    TASK-779 is left with no stages on purpose, so "nothing was recorded" stays a
    distinguishable outcome on the wire.
    """
    sys.path.insert(0, str(HERE))
    from cmo_runtime.console_db import ConsoleDB
    from cmo_runtime.pipeline_stages import StageRecorder

    database = ConsoleDB(root)
    try:
        recorder = StageRecorder(database, task_id="TASK-777")
        with recorder.stage("topic") as stage:
            stage.finish(
                summary="Chose the replacement-cost angle",
                why="Search Console shows unanswered demand for replacement pricing.",
            )
        with recorder.stage("research") as stage:
            stage.record_sources(
                [
                    {
                        "url": "https://really-fetched.test/pricing",
                        "title": "Replacement pricing survey",
                        "published_date": "2026-07-01",
                        "accessed_date": "2026-08-11",
                    },
                    {
                        "url": "https://really-fetched.test/down",
                        "outcome": "failed",
                        "message": "HTTP 502",
                    },
                ]
            )
            stage.finish(summary="1/2 source page(s) fetched")
        with recorder.stage("writing") as stage:
            stage.finish(summary="1,180 words in 5 section(s)", words=1180)
    finally:
        database.close()


def seed_proposals(root: Path) -> dict[str, tuple[int, list[int]]]:
    """Subjects that fanned out to three candidates each, through the real store.

    The archive sweep is a property of approving, so a fixture has to be a real
    fan-out: one subject, several live candidates, none of them carded. Each
    mutating test gets its own subject — the same reason the blog tests each get
    their own card — so nothing here depends on the order the suite runs in.
    """
    sys.path.insert(0, str(HERE))
    from cmo_runtime.console_db import ConsoleDB, ProposalCandidate

    database = ConsoleDB(root)
    fixtures: dict[str, tuple[int, list[int]]] = {}
    try:
        for name in ("sweep", "restore", "refuse"):
            subject = database.subject_for(f"served {name} fixture subject", CEO_EMAIL)
            run_id = database.record_research_run(
                subject_id=int(subject["id"]),
                kind="initial",
                pages_requested=1,
                pages_fetched=1,
                status="completed",
            )
            result = database.add_candidates(
                subject_id=int(subject["id"]),
                research_run_id=run_id,
                candidates=[
                    ProposalCandidate(
                        title=f"Served {name} fixture candidate {index}",
                        keywords=(f"served {name} fixture",),
                        outline=f"Outline for served {name} fixture candidate {index}.",
                        source_kind="firecrawl",
                        source_refs=(f"https://fixture.test/{name}/{index}",),
                    )
                    for index in (1, 2, 3)
                ],
            )
            ids = [int(item["id"]) for item in result["added"]]
            fixtures[name] = (ids[0], ids[1:])
        return fixtures
    finally:
        database.close()


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


#: The one account this suite's bearer token resolves to.
CEO_EMAIL = "served-page-ceo@itarang.test"
BEARER = "served-page-bearer-token"


class FakeSupabase(http.server.BaseHTTPRequestHandler):
    """Just enough Supabase to let the real auth path run.

    `console_auth` verifies a bearer token by asking Supabase who it belongs to.
    Without a stand-in, nothing behind that check could ever be fetched over a
    socket — which is how every authenticated route on this console came to have
    no served-bytes coverage at all. This answers one endpoint and nothing else,
    so the code under test is the console's, not a mock of it.
    """

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's spelling
        if self.path != "/auth/v1/user":
            self.send_error(404)
            return
        if self.headers.get("Authorization", "") != f"Bearer {BEARER}":
            self.send_error(401)
            return
        body = json.dumps({"email": CEO_EMAIL}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


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
        (root / "artifacts" / "TASK-779-content.md").write_text(ARTICLE, encoding="utf-8")
        seed_recorded_stages(root)
        cls.proposal_fixtures = seed_proposals(root)
        cls.root = root
        cls.port = free_port()
        cls.supabase = socketserver.TCPServer(("127.0.0.1", 0), FakeSupabase)
        cls.supabase_thread = threading.Thread(target=cls.supabase.serve_forever, daemon=True)
        cls.supabase_thread.start()
        supabase_url = f"http://127.0.0.1:{cls.supabase.server_address[1]}"
        environment = {
            **os.environ,
            "CMO_DASHBOARD_PROFILE_DIR": str(root),
            "SUPABASE_URL": supabase_url,
            "SUPABASE_ANON_KEY": "served-page-anon-key",
            "CMO_CEO_EMAIL": CEO_EMAIL,
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
        cls.supabase.shutdown()
        cls.supabase.server_close()
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
    def fetch(
        cls,
        path: str,
        *,
        auth: bool = False,
        payload: dict | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            f"http://127.0.0.1:{cls.port}{path}",
            data=body,
            method="POST" if body is not None else "GET",
        )
        if body is not None:
            request.add_header("Content-Type", "application/json")
        if auth:
            # The console's own routes take a Supabase bearer token; `/api/*` on the
            # legacy dashboard still takes Basic. Send whichever the path expects.
            if path.startswith("/ceo/"):
                request.add_header("Authorization", f"Bearer {BEARER}")
            else:
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

    def test_the_stamp_covers_the_runtime_the_console_imports(self) -> None:
        """A cmo_runtime-only deploy has to move the stamp, or the deploy check lies.

        `deploy-dashboard` refuses to report success unless the served stamp moves.
        While the stamp read only `dashboard/*.py`, a change landing entirely in
        `cmo_runtime` — the board, the writer, the publisher — could not move it,
        so a deploy that had genuinely worked reported failure.
        """
        import ceo_build

        # A temporary tree shaped like a deployed profile, so this touches nothing
        # real and does not depend on whichever file in the checkout is newest.
        with tempfile.TemporaryDirectory() as folder:
            profile = Path(folder)
            dashboard = profile / "dashboard"
            runtime = profile / "cmo_runtime"
            dashboard.mkdir()
            runtime.mkdir()
            (dashboard / "ceo_console.py").write_text("", encoding="utf-8")
            module = runtime / "content_flow.py"
            module.write_text("", encoding="utf-8")
            os.utime(dashboard / "ceo_console.py", (1_700_000_000, 1_700_000_000))
            os.utime(module, (1_700_000_000, 1_700_000_000))
            before = ceo_build.source_stamp(dashboard)

            os.utime(module, (1_700_000_500, 1_700_000_500))
            after = ceo_build.source_stamp(dashboard)

        self.assertNotEqual(after["epoch"], before["epoch"], "a runtime change did not move the stamp")
        self.assertEqual(after["file"], "cmo_runtime/content_flow.py")
        self.assertEqual(before["file"], "ceo_console.py")

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

    def test_the_served_page_orders_the_tabs_topics_blogs_analytics_archived(self) -> None:
        page = self.text("/ceo")
        nav = page.split('<nav class="primary"', 1)[1].split("</nav>", 1)[0]

        self.assertEqual(
            re.findall(r'data-view="([a-z-]+)"', nav),
            ["topics", "blogs", "analytics", "archived"],
        )
        self.assertRegex(nav, r'class="active" data-view="topics"')
        self.assertEqual(
            re.findall(r"<kbd>(\d)</kbd>\s*([A-Za-z&; ]+?)<", nav),
            [
                ("1", "Topics &amp; Research"),
                ("2", "Blogs"),
                ("3", "Analytics"),
                ("4", "Archived"),
            ],
        )

    def test_the_served_page_shows_topics_first_and_hides_the_others(self) -> None:
        page = self.text("/ceo")

        self.assertIn('<section id="panel-topics" class="screen paper">', page)
        self.assertIn('<section id="panel-blogs" class="screen paper" hidden>', page)
        self.assertIn('<section id="panel-analytics" class="screen paper" hidden>', page)
        self.assertIn('<section id="panel-archived" class="screen paper" hidden>', page)

    def test_the_served_page_carries_the_needs_you_band_above_the_tabs(self) -> None:
        """The band has to arrive with the shell, not with the first render.

        It is the answer to "what needs me", so a page that paints the tabs first
        and the band a second later has answered a different question first.
        """
        page = self.text("/ceo")

        self.assertIn('<section id="needs-you" class="needs-band"', page)
        self.assertLess(
            page.index('id="needs-you"'),
            page.index('<nav class="primary"'),
            "the band must be served above the tabs, not below them",
        )
        # And it must be reachable: the jump control the band emits is handled.
        self.assertIn("if(data.jump){", page)

    def test_the_served_page_offers_the_news_radar(self) -> None:
        page = self.text("/ceo")

        self.assertIn('id="scan-news"', page)
        self.assertIn("/ceo/api/radar/scan", page)
        # The button must be wired, not merely present.
        self.assertIn("$('#scan-news').addEventListener('click',scanNews)", page)

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

    # ---- the process tab, on the wire ------------------------------------

    def test_the_served_page_orders_the_blog_card_tabs_with_process_after_read(self) -> None:
        """The detail tab order was never asserted over the wire until now.

        A tab that renders nothing and a tab that is missing look identical in a
        module; over the socket they do not.
        """
        page = self.text("/ceo")
        nav = page.split('<nav class="nested"', 1)[1].split("</nav>", 1)[0]

        self.assertEqual(
            re.findall(r'data-detail="([a-z-]+)"', nav),
            ["read", "process", "impact", "discussion", "files"],
        )
        self.assertRegex(nav, r'class="active" data-detail="read"')
        self.assertIn(">Process<", nav)

    def test_the_state_endpoint_serves_only_the_stages_that_were_recorded(self) -> None:
        """Invariant 2, over the socket."""
        served = self.blogs()["TASK-777"]

        self.assertEqual(
            [(stage["ordinal"], stage["stage"]) for stage in served["process"]],
            [(1, "topic"), (5, "research"), (6, "writing")],
        )
        self.assertEqual(
            served["process"][0]["detail"]["why"],
            "Search Console shows unanswered demand for replacement pricing.",
            "the recorded reason for choosing the topic did not reach the page",
        )

    def test_a_card_with_no_recorded_stages_serves_an_empty_process_list(self) -> None:
        self.assertEqual(
            self.blogs()["TASK-779"]["process"],
            [],
            "a card whose stages were never recorded had some invented for it",
        )

    def test_the_served_research_stage_itemises_what_failed_as_well_as_what_worked(self) -> None:
        research = [
            stage for stage in self.blogs()["TASK-777"]["process"] if stage["stage"] == "research"
        ][0]

        self.assertEqual((research["fetched"], research["failed"]), (1, 1))
        self.assertEqual(
            [(item["url"], item["outcome"]) for item in research["fetches"]],
            [
                ("https://really-fetched.test/pricing", "fetched"),
                ("https://really-fetched.test/down", "failed"),
            ],
            "a source that failed to fetch was dropped instead of reported",
        )

    # ---- invariant 8, on the wire ----------------------------------------

    def test_the_served_page_requests_nothing_from_another_host(self) -> None:
        page = self.text("/ceo")

        for marker in ("http://", "https://", "//cdn", "<link", "@import", "<iframe"):
            self.assertNotIn(marker, page, f"the served page references {marker}")

    def test_the_config_endpoint_serves_the_public_browser_config(self) -> None:
        status, _headers, body = self.fetch("/ceo/api/config")

        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["anon_key"], "served-page-anon-key")

    # ---- the blog chain, on the wire -------------------------------------

    def blogs(self) -> dict[str, dict]:
        payload = json.loads(self.text("/ceo/api/state", auth=True))
        return {task["id"]: task for task in payload["blogs"]}

    def test_a_content_card_with_no_article_is_still_served_on_the_blogs_tab(self) -> None:
        """Invariant 5. Three cards, only two of which have been written."""
        served = self.blogs()

        self.assertEqual(
            sorted(served),
            ["TASK-777", "TASK-778", "TASK-779", "TASK-780", "TASK-781", "TASK-782"],
        )
        self.assertIsNone(served["TASK-780"]["article"])
        self.assertEqual(served["TASK-780"]["blog"]["label"], "Queued to be written")
        # Every one of them says something. None of them is silently absent.
        self.assertTrue(all(task["blog"]["label"] for task in served.values()))

    def test_a_failed_write_is_served_with_its_reason_and_a_retry(self) -> None:
        """Invariant 4, in the bytes: the reason is the writer's own sentence."""
        card = self.blogs()["TASK-778"]["blog"]

        self.assertEqual(card["state"], "failed")
        self.assertEqual(card["label"], "Could not be written")
        self.assertIn("1742 words", card["reason"])
        self.assertTrue(card["retryable"])

    # ---- marker: approving one topic sweeps its siblings -----------------

    def topics(self) -> dict:
        return json.loads(self.text("/ceo/api/state", auth=True))["topics"]

    def test_approving_a_topic_archives_its_siblings_over_the_wire(self) -> None:
        """The whole point of the sweep, measured on what the console is served.

        Approving is one decision about one subject. The candidates that lost are
        not rejected — nothing may be written to the rejection memory — but they
        must leave the screen, and they must be findable afterwards.
        """
        approve_id, siblings = self.proposal_fixtures["sweep"]
        live = {item["id"] for item in self.topics()["proposals"]}
        self.assertIn(approve_id, live)
        for sibling in siblings:
            self.assertIn(sibling, live)

        status, _headers, body = self.fetch(
            "/ceo/api/proposal/approve", auth=True, payload={"proposal_id": approve_id}
        )
        self.assertEqual(status, 200, body)
        outcome = json.loads(body)
        self.assertRegex(outcome["task_id"], r"^TASK-[0-9]+$")
        self.assertEqual(sorted(item["id"] for item in outcome["archived"]), sorted(siblings))

        after = self.topics()
        remaining = {item["id"] for item in after["proposals"]}
        archived = {item["id"] for item in after["archived"]}
        for sibling in siblings:
            self.assertNotIn(sibling, remaining, "an archived sibling is still on Topics")
            self.assertIn(sibling, archived, "an archived sibling is nowhere to be found")
        # Archiving is not rejecting: the rejection memory must be untouched, or the
        # idea could never be proposed again.
        self.assertEqual(
            [item for item in after["rejected"] if item["proposal_id"] in siblings], []
        )
        # And the archived rows carry what the Archived screen groups them by.
        shelved = next(item for item in after["archived"] if item["id"] == siblings[0])
        self.assertTrue(shelved["subject_id"])
        self.assertEqual(shelved["status"], "archived")

    def test_restoring_an_archived_topic_returns_it_to_the_pool(self) -> None:
        approve_id, siblings = self.proposal_fixtures["restore"]
        self.fetch("/ceo/api/proposal/approve", auth=True, payload={"proposal_id": approve_id})
        target = siblings[-1]
        status, _headers, body = self.fetch(
            "/ceo/api/proposal/restore", auth=True, payload={"proposal_id": target}
        )
        self.assertEqual(status, 200, body)

        after = self.topics()
        self.assertIn(target, {item["id"] for item in after["proposals"]})
        self.assertNotIn(target, {item["id"] for item in after["archived"]})

    def test_restoring_something_that_was_never_archived_is_refused(self) -> None:
        approve_id, _siblings = self.proposal_fixtures["refuse"]
        status, _headers, body = self.fetch(
            "/ceo/api/proposal/restore", auth=True, payload={"proposal_id": approve_id}
        )
        self.assertEqual(status, 400, body)
        self.assertIn("not archived", body.decode("utf-8"))

    def test_a_published_card_is_served_with_its_preview_url(self) -> None:
        card = self.blogs()["TASK-779"]["blog"]

        self.assertEqual(card["label"], "Live on the site")
        self.assertEqual(card["url"], "https://itarangwebsite.vercel.app/blog/charging-habits")

    def test_the_served_page_can_draw_every_state_and_the_retry_control(self) -> None:
        """The states exist server-side; the page has to be able to say them."""
        page = self.text("/ceo")

        for state in ("queued", "researching", "writing", "failed", "held",
                      "checking", "awaiting_you", "rewriting", "published"):
            self.assertIn(f"{state}:{{glyph:", page, f"the served page has no vocabulary for {state}")
        for chip in ("Awaiting you", "Being written", "Could not be written", "Published"):
            self.assertIn(chip, page, f"the served page cannot filter by {chip!r}")
        self.assertIn("data-retry=", page, "the served page carries no retry control")
        self.assertIn("data-elapsed=", page, "a running write has no elapsed clock")

    def test_a_held_card_is_served_as_held_and_offers_no_retry(self) -> None:
        card = self.blogs()["TASK-781"]["blog"]

        self.assertEqual(card["state"], "held")
        self.assertEqual(card["label"], "On hold")
        self.assertFalse(card["retryable"])

    def test_a_retry_is_refused_on_a_card_a_human_put_on_hold(self) -> None:
        """Clearing somebody's hold is not a retry, and the console will not do it."""
        status, _headers, body = self.fetch(
            "/ceo/api/blog-retry", auth=True, payload={"task_id": "TASK-781"}
        )

        self.assertEqual(status, 400)
        self.assertIn("cannot be retried", json.loads(body)["error"])
        self.assertEqual(self.blogs()["TASK-781"]["blog"]["state"], "held")

    def test_a_retry_requeues_a_failed_card_over_the_wire(self) -> None:
        """Invariant 4's other half: the console can actually start it again.

        Uses its own card, because this one mutates the board and a suite whose
        assertions depend on which test ran first is a suite that will lie later.
        """
        self.assertEqual(self.blogs()["TASK-782"]["blog"]["state"], "failed")

        status, _headers, body = self.fetch(
            "/ceo/api/blog-retry", auth=True, payload={"task_id": "TASK-782"}
        )
        self.assertEqual(status, 200, body)

        after = self.blogs()["TASK-782"]
        self.assertEqual(after["blog"]["state"], "queued")
        self.assertEqual(after["blog"]["label"], "Queued to be written")
        self.assertFalse(after["blog"]["retryable"])
        # And the board says who asked for it, not just that something happened.
        self.assertIn(CEO_EMAIL, after["latest_summary"])


class UnconfiguredConsoleTests(unittest.TestCase):
    """The console with no Supabase configured at all.

    The main suite now stands a Supabase up so the authenticated routes can be
    fetched over a socket, which means it can no longer answer the question this
    one exists for: does the console still boot, and still serve its shell, when
    nobody has configured auth? That is a real starting state on a fresh box, and
    an exception there looks identical to a broken deploy.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        for name in ("state", "artifacts", "logs"):
            (root / name).mkdir()
        (root / "tasks.md").write_text(BOARD, encoding="utf-8")
        cls.port = free_port()
        environment = {
            **os.environ,
            "CMO_DASHBOARD_PROFILE_DIR": str(root),
            "CMO_DASHBOARD_PORT": str(cls.port),
            "CMO_DASHBOARD_HOST": "127.0.0.1",
            "CMO_DASHBOARD_USERNAME": USERNAME,
            "CMO_DASHBOARD_PASSWORD": PASSWORD,
            "PYTHONPATH": os.pathsep.join(
                path for path in (str(HERE), os.environ.get("PYTHONPATH", "")) if path
            ),
        }
        for name in ("SUPABASE_URL", "SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_URL",
                     "NEXT_PUBLIC_SUPABASE_ANON_KEY", "CMO_CEO_EMAIL",
                     "GSC_CREDENTIALS_PATH", "GSC_PROPERTY", "GA4_PROPERTY_ID"):
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
        if cls.server.poll() is None:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait(timeout=10)
        cls.temp.cleanup()

    def test_the_console_boots_without_credentials_rather_than_erroring(self) -> None:
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/ceo/api/config")
        with urllib.request.urlopen(request, timeout=20) as response:
            self.assertEqual(json.loads(response.read()), {"url": "", "anon_key": ""})

    def test_the_shell_still_renders_without_auth_configured(self) -> None:
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/ceo")
        with urllib.request.urlopen(request, timeout=20) as response:
            self.assertIn("iTarang CEO Console", response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
