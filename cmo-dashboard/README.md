# iTarang CMO monitoring dashboard

Read-only single-page dashboard for `/opt/data/profiles/itarang_cmo/tasks.md`.

## Run

Credentials live in `/opt/data/profiles/itarang_cmo/dashboard/.env`, which must remain mode `600`:

```dotenv
CMO_DASHBOARD_USERNAME=your-user
CMO_DASHBOARD_PASSWORD=your-password
```

Start the persistent service through tmux:

```bash
/opt/data/profiles/itarang_cmo/bin/run-dashboard
```

This creates session `cmo-dashboard`; the session runs `/opt/data/profiles/itarang_cmo/dashboard/run-dashboard`, which loads `/opt/data/profiles/itarang_cmo/dashboard/.env` and starts `/opt/data/profiles/itarang_cmo/dashboard/dashboard_server.py` as `hermes`. `start-cmo-agents` and `ensure-cmo-agents` also manage this session. It listens on `0.0.0.0:8080` by default. Override with `CMO_DASHBOARD_HOST` or `CMO_DASHBOARD_PORT` in the environment file if needed.

`/opt/data/profiles/itarang_cmo/bin/dashboard-session-healthy` requires all of the following: the expected tmux session has a live pane, its process tree contains the expected server script owned by `hermes`, and that same process owns the expected listening port. A session name or live pane by itself is not considered healthy.

## Deploy

**This directory is not what is being served.** `dashboard_server.py` runs from
`/opt/data/profiles/itarang_cmo/dashboard/`, a copy of this directory; `cmo_runtime/`
is copied to the profile root the same way. A commit here changes nothing anyone can
see until the copy happens.

```bash
./deploy-dashboard --dry-run   # list what differs, change nothing
./deploy-dashboard             # copy, restart through run-dashboard, verify
```

The script copies changed `*.py` (never `.env`), kills the tmux session so
`run-dashboard` cannot short-circuit on its own health check, restarts, then
verifies four things: the port answers, the tmux session owns the listener, exactly
one `dashboard_server.py` is running, and the **served** `X-CMO-Build` header
changed. Files copied without the served stamp moving is a failed deploy.

Never name a shell variable `TMUX` in scripts here — inside a tmux pane it is
already exported, so assigning to it redirects tmux's socket path for every child
process, and the next server will create its socket over whatever lives there.

## Which build am I looking at?

Every console page renders a build stamp in its footer and returns the same value as
the `X-CMO-Build` header: the mtime of the newest `dashboard/*.py` on the serving
box, plus a 12-character digest of the assembled page.

```bash
curl -fsS -o /dev/null -D - http://127.0.0.1:8080/ceo | grep -i x-cmo-build
# X-CMO-Build: src=1786445643 file=ceo_script.py page=df5a106f2a00
```

The mtime catches a deploy that never ran; the digest catches one that ran and
landed different bytes. The digest is reproducible: replace the rendered stamp in
the served HTML with `@@CMO_BUILD_STAMP@@` and take `sha256(...)[:12]`.

## Tests

```bash
./run-tests
```

Runs the console suites, every `tests/*.py` module and the board validator under
`/opt/hermes/.venv/bin/python` — the interpreter the deployed server actually uses.
**Do not run the suites under `/usr/bin/python3`**: it has no PyYAML and cannot get it
(the distro disables pip and the agent is not root), so `tests/test_approval_cards.py`
fails to import and its 13 tests silently disappear from the run. Override with
`CMO_TEST_PYTHON` only if you know the target has PyYAML.

Three suites check behaviour rather than presence, because presence-only tests are
how a reader that printed raw Markdown stayed green for weeks:

- `test_served_bytes.py` starts the server against a temporary profile and asserts on
  bytes fetched over a socket — a rendered `<table>`, the tab order, the editor
  control, the build stamp. It imports nothing from the render path.
- `test_ceo_console_render.py` executes the browser script under node via
  `console_harness.js` and asserts on what each panel rendered.
- `test_ceo_reader.py` renders every `.md` in the live profile and fails on any raw
  Markdown that reaches the page.

## The topic flow

A rough subject typed into the CEO Console is **not** a writing instruction. It is
researched into candidate topics, each carrying a title, its keywords, an outline and
the source that produced it; the CEO then approves, suggests changes to, or rejects
each candidate. Only an approved candidate mints a board card.

Proposals live in SQLite at `state/console.db` (`cmo_runtime/console_db.py`), never on
the board — so an unapproved candidate is not filtered out of `tasks.md`, it was never
on it, and neither `Runtime.execute()` nor `ContentRuntime._select()` can reach it.
Rejections are remembered by a fingerprint that survives rewording, and suppress future
re-proposals until explicitly undone.

Firecrawl is **discovery then retrieval**, never search-with-scrape: `/v2/search`
without `scrapeOptions` returns URLs, then `/v2/scrape` reads at most
`PROPOSAL_PAGE_CAP` of them at roughly one credit each. Search Console answers demand
questions first because it is free. A repeat subject replays cached research for
nothing. Runs refuse above `FIRECRAWL_PROPOSAL_STOP` measured credits rather than
degrading quietly.

Cards that predate this flow are set aside with
`cmo_runtime.topic_proposals.hold_legacy_cards()`: the card stays on the board at
`Change status: pending human decision`, both selectors skip it, and it reappears as a
proposal naming the card as its source.

## Competitor analytics

`cmo_runtime/competitors.py` answers "which website do you want to replicate" from what
we already have: their `sitemap.xml` (a plain GET, free), up to `COMPETITOR_PAGE_CAP` of
their pages scraped directly (one credit each), and our own Search Console position for
each topic they cover. Findings are `uncontested`, `weak_position` or `covered`.

What it cannot answer — what they actually rank for, their traffic, and search volume
for terms we do not already rank for — renders as unavailable and names what would
supply it. Nothing is estimated and nothing shows as zero. Search volume slots in behind
`VolumeProvider` when Google Ads Keyword Planner credentials arrive:

```dotenv
GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=
GOOGLE_ADS_CREDENTIALS_PATH=
```

## Site crawl cadence

`scripts/morning-seo-job.py` crawls itarang.com when the deployed commit
(`refs/heads/main`) differs from the last crawled SHA, with a weekly floor for drift a
SHA cannot see and a one-per-day ceiling. The page limit is 20, matching the sitemap.
An unreadable SHA holds until the weekly floor rather than crawling every cycle.

## Behavior

- The browser polls `GET /api/state` every 10 seconds.
- The server re-reads `tasks.md` on every request.
- tmux health is read from `/opt/data/profiles/itarang_cmo/bin/tmux ls`.
- The UI has agent tabs and a four-column board: Task List, Under Review (CMO), Under Review (Human), Completed.
- All state endpoints are GET-only. POST, PUT, PATCH, and DELETE return 405.
- No database, task actions, or file writes are used by the dashboard.
- Basic Auth credentials are read only from `CMO_DASHBOARD_USERNAME` and `CMO_DASHBOARD_PASSWORD`.
