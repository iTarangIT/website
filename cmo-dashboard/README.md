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
- `test_console_live.py` executes the browser script under `console_live_harness.js`,
  whose DOM has node identity, a settable `document.hidden` and a `fetch` that can be
  made to fail or to never answer. That is what makes "the button went dead before the
  reply came back", "the unchanged row is still the same node" and "the textarea was
  not overwritten" checkable at all.

## Showing the work: the Process tab

A blog used to go from an approved topic to a finished article with nothing visible in
between. The **Process** tab on a blog card is the record of what actually happened,
stage by stage, in the order they are meant to be read:

```text
1  Topic selection    the topic, and why it was chosen
2  Keyword selection  the keywords, and the Search Console rows behind them
3  Summary            what the article will say, as approved
4  Outline            the sections it will carry
5  Research           every page fetched, and every one that failed
6  Writing            words, sections, trim passes, refusals
```

**Rows, and only rows.** Every stage is written by the pipeline while it runs; the tab
renders the query result directly. A stage that never ran has no row, so it is not
drawn — there is no notion of a stage that "should" be there and therefore no way to
imply work that did not happen. Cards written before this existed show an empty tab,
which is the honest answer rather than a reconstructed one.

**A stage completed is a stage recorded.** `pipeline_stages` rows are opened before the
work (`status='running'`, `started_at` set) and closed after it, in two separate
`ConsoleDB.write()` transactions. A process killed mid-run therefore leaves every
finished stage committed and the interrupted one readable as `running` — which is also
exactly what the tab needs to show elapsed time. `tests/test_pipeline_stages.py` proves
this by `SIGKILL`ing a real subprocess and reading the database back.

**The source list comes from the fetch ledger, never from the article.** `stage_fetches`
holds one row per attempt to read something, failures included, and
`console_board.process_payload()` builds the research stage from that table alone. An
article can cite any URL it likes; a URL with no fetch record cannot reach the page.
There is a test for exactly that, because "here are six sources" and "we asked for eight
and six came back" read identically until someone writes the second one down.

**Retries do not overwrite.** `attempt` increments, so three failed generations are three
rows rather than one row that eventually says `completed`.

Two of the six stages did not exist as discrete steps and now do. `Topic selection`
gained a `why` — one more key in the proposer's existing JSON contract, not a second
call. `Outline` is new: `HermesContentWriter.outline()` agrees 4-6 section headings from
the approved scope and the research brief before `write()` is called, and those headings
are passed into the writer as a constraint. `Keyword selection` was deliberately *not*
split into its own generation — the keywords come back attached to the title they belong
to, and a second call would drift from it; the stage records them with the Search Console
demand rows that justify them, and says so.

The tab updates live through the existing token: `ceo_version.py` already watches
`console.db` and its `-wal` sidecar, so a stage row committed by the writer reaches an
open console within three seconds with no new mechanism.

## The console updates itself

Sanchit never presses refresh. Two separate mechanisms, because the two problems are
not the same problem.

**An action he just triggered.** Every slow action — research a subject, suggest
changes, ask for changes, save an edit, queue a subject, analyse a competitor, publish
— goes through one helper, `runAction()` in `ceo_script.py`. There is no second way to
look busy. It disables the button, relabels it (`Researching… 7s`, ticking), drops a
skeleton at the real height where the results will land, and on failure leaves the
reason on screen in that same space. `Firecrawl returned 402: monthly credits
exhausted` is useful; a toast that fades in three seconds is not.

**A change made somewhere else.** `GET /ceo/api/version` (`ceo_version.py`) returns one
short token computed from `tasks.md`'s mtime and size, `console.db`'s own file change
counter plus its `-wal` sidecar, the newest entry in `artifacts/`, and the newest
`state/*.json`. No board parse, no Search Console, no Firecrawl, no network — a handful
of `stat` calls, two shallow `scandir`s and a 28-byte read. The browser polls it every
3 seconds and refetches `/ceo/api/state` **only when the token differs**. It backs off
3s → 6s → 12s → 30s on failure and resets on the first success, and it stops entirely
while `document.hidden`, resuming on `visibilitychange` or `focus`.

SSE at `/api/events` was not reused: a stdlib `ThreadingHTTPServer` holds a thread per
open connection, and this console needs to survive two people and a phone, not scale.
**The old blind 60-second reload is gone** — one mechanism, not two.

What a background update is not allowed to disturb: an open editor with unsaved text
(it shows `This article changed elsewhere. Save yours, or reload to see theirs.` and
touches nothing), the open article and its scroll position, pagination, sort, filter,
the search box, or an action still in flight. Lists are **patched, not re-rendered**:
rows carry `data-key`, and a row whose markup is byte-identical is not touched, so
scroll, focus and open `<details>` all survive. Anything that arrives on a tab or a
page he is not looking at is counted — `Blogs 2` on the tab, or a `1 new` line above
the list — never jumped to.

## The topic flow

A rough subject typed into the CEO Console is **not** a writing instruction. It is
researched into candidate topics, each carrying a title, its keywords, an outline and
the source that produced it; the CEO then approves, suggests changes to, or rejects
each candidate. Only an approved candidate mints a board card.

**The approved scope reaches the writer.** An approved candidate mints a card carrying
`Topic outline` and `Topic keywords`, and the acceptance criterion "Cover the approved
outline recorded on this card". `ContentRuntime` passes both fields to all three writer
prompts — `write()`, `correct()` and `revise()`. `correct()` is not an afterthought: it is
the retry path, and a correction fixing a word count while blind to the approved scope can
walk out of what was agreed. A card carrying neither field (anything held from before the
topic flow) produces no scope block at all, because an empty `OUTLINE:` line reads as "no
constraints" rather than "not recorded".

A scope that does not fit is its own outcome. `content.skill` caps an article at 900–1,400
words and says "a task needing more is split rather than extended", so the writer is asked
to answer `OUTLINE TOO BROAD:` naming what needs its own article, instead of overrunning
and being rejected after the fact. `_refuse_if_outline_too_broad` turns that into a board
refusal, deliberately outside the `correct()` retry — too much scope is not something a
correction pass can fix, and retrying costs a full generation to get the same answer. Nine
consecutive TASK-084 generations overran the ceiling before this existed, and the board
only ever learned "writer article has N words".

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

### Approving one candidate archives the rest

One subject fans out to up to `MAX_CANDIDATES` candidates and exactly one of them
becomes a card. Approving sweeps the others — same subject, still `proposed` or
`revising` — to `status = 'archived'` and onto the **Archived** tab. Before this
existed they stayed on Topics forever; 31 of 39 live proposals were leftovers of
decisions already made, which is the pile-up the sweep ends.

**Archiving is not rejecting, and the difference is load-bearing.** A rejection writes
a `rejected_topics` row keyed by the reworded-proof fingerprint and suppresses the idea
until it is explicitly undone. Archiving writes nothing there. An archived candidate
can be restored by hand (`POST /ceo/api/proposal/restore`), and `add_candidates`
**resurfaces** one on its own when research produces the same fingerprint again,
reporting it as `resurfaced` rather than swallowing it as a duplicate. That last part
is the reason the liveness probe excludes `archived` as well as `rejected`: without it
the archive would be a silent veto with none of a rejection's deliberateness.

The sweep runs only after the board card exists, so a failed mint archives nothing, and
a second approval of the same proposal archives nothing either — it is not a second
decision. `POST /ceo/api/proposal/archive` sets one aside by hand, with the same
reversibility.

### The news radar

`cmo_runtime/news_radar.py` is what makes a topic arrive without anyone typing one.
It does not add a second research path: it produces subject strings and hands each to
`TopicProposalService.propose`, which keeps its cache, accounting, dedup and stage
recording unchanged.

One sweep:

1. **Live budget check.** Refuses if Firecrawl is not ready, or if remaining credits
   are below `RADAR_CREDIT_FLOOR` — an unattended daily job must never be why the CEO
   cannot research a subject by hand. Refusals are recorded, because a sweep that left
   no trace reads as one that never ran.
2. **Free discovery** across every beat — `DEFAULT_BEATS` (EV industry, policy,
   battery technology, market, charging and swapping), plus one beat per
   `state/ceo-watchlist.json` entry and per row in `competitors`, so the beat is
   steerable from surfaces the CEO already controls without a redeploy. `/v2/search`
   without `scrapeOptions` bills nothing and returns titles, narrowed to
   `RADAR_RECENCY` (`qdr:w`). One dead beat does not end the sweep.
3. **One Hermes triage call** turns the pooled headlines into at most
   `RADAR_MAX_SUBJECTS` rough subjects. The cap is enforced in `_subjects_from`, not in
   the prompt: a model asked for three and returning nine must cost three subjects'
   worth of credits, not nine. An empty answer is a correct answer.
4. **`propose()` per subject.** The only paid step, at `PROPOSAL_PAGE_CAP` pages each —
   worst case `RADAR_MAX_SUBJECTS × PROPOSAL_PAGE_CAP` credits a day. One refused
   subject does not lose the others.

Note the recency window applies to discovery only. The research behind a topic is
deliberately unbounded: a 2023 gazette notification is exactly the source a policy
piece needs.

Every sweep, refusals included, lands in `radar_runs` and the latest is rendered on the
console as `topics.radar`.

Two ways to run it:

```bash
# what it would research, spending nothing
python -m cmo_runtime.news_radar --profile "$CMO_DASHBOARD_PROFILE_DIR" --dry-run

# the daily sweep: clock-driven, flock on state/news-radar.lock, stamp in
# state/news-radar-last-run. A late cycle runs late rather than being skipped.
python -m cmo_runtime.news_radar --profile "$CMO_DASHBOARD_PROFILE_DIR" --due
```

**The watchdog must be told to call it.** The `--due` line has to be added to the
cmo-watchdog next to the `morning-seo-job.py --due` line; that file lives outside this
repo. Until it is, the radar only fires from the console's **Scan EV news now** button,
which posts to `/ceo/api/radar/scan` and runs exactly the same sweep.

It lives in `cmo_runtime/` and not in `scripts/` on purpose: `deploy-dashboard` copies
`cmo-dashboard/*.py`, `*.js` and `cmo_runtime/*.py`, and nothing under `scripts/`. A
radar under `scripts/` would be committed and never shipped.

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
