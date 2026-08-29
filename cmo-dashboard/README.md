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

## Blog imagery

Two producers, two jobs. The writer hand-authors an accessible **SVG diagram** — the
right tool for labels, numbers and steps. Google's Nano Banana 2 generates the
**photographic illustration** that sits beside a paragraph and the **cover** that goes
on the blog card and the Open Graph tag. Neither replaces the other.

| Setting | Value |
| --- | --- |
| Model | `gemini-3.1-flash-image` (Nano Banana 2); override with `GEMINI_IMAGE_MODEL` |
| Endpoint | `https://generativelanguage.googleapis.com/v1beta/interactions`; override with `GEMINI_API_URL` |
| Key | `GEMINI_API_KEY` in `$CMO_DASHBOARD_PROFILE_DIR/.env` (mode 600) |
| Cost | $0.067 per 1K image, standard tier. **No free tier** — an unbilled key fails on the first call. |
| Output | 16:9 WebP, long edge capped at 1600px, quality stepped down toward 250 KB |

At up to three articles a day and two images each, that is roughly **$12 a month**
against the profile's $50 budget. Every call is recorded through
`scripts/spend-tracker.py` as `provider: gemini`, and a generation that would cross the
$40 warning is refused *before* the request goes out rather than discovered afterwards.

Where it runs:

- **Automatically**, in the write stage. The writer emits a scene for each image in the
  same call that writes the article, so the picture comes from the piece rather than
  from its headline. `cmo_runtime/image_gen.py` wraps each scene in the house rules —
  no text, no faces, no logos, no documents — and writes the WebP into the artifact
  store.
- **By hand**, from the console's Files tab. Each slot carries the description it was
  drawn from, editable, with a Generate button beside the existing upload. A diagram
  slot says so and offers no button: the writer draws that one.

A failed generation never fails a run. The article has already cost Firecrawl credits
and a writer call; a missing picture leaves the slot unbound, which the console renders
as an empty frame and the publisher treats as a post that simply has no cover.

Generated images carry an invisible SynthID watermark, and an illustration publishes
with `Illustration generated with AI.` in its caption (`AI_FIGURE_CREDIT` in
`cmo_runtime/blog_publisher.py`; set it to `""` to stop disclosing).

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

## Showing the work: the recorded stages

A blog used to go from an approved topic to a finished article with nothing visible in
between. `pipeline_stages` is the record of what actually happened, stage by stage, in
the order they are meant to be read:

```text
1  Topic selection    the topic, and why it was chosen
2  Keyword selection  the keywords, and the Search Console rows behind them
3  Summary            what the article will say, as approved
4  Outline            the sections it will carry
5  Research           every page fetched, and every one that failed
6  Writing            words, sections, trim passes, refusals
```

**Rows, and only rows.** Every stage is written by the pipeline while it runs; a reader
of this table gets the query result directly. A stage that never ran has no row — there
is no notion of a stage that "should" be there and therefore no way to imply work that
did not happen. Cards written before this existed have no rows at all, which is the
honest answer rather than a reconstructed one.

**There is no longer a Process tab.** The blog detail is Read and Files (see *One
article, one screen* below); the stage rows are not drawn on it. Everything below still
holds — the pipeline records exactly as it did, `console_board.process_payload()` still
assembles the rows and `/ceo/api/state` still serves them under `process` on each blog.
They are read from `state/console.db` or off that payload, not from a tab.

**A stage completed is a stage recorded.** `pipeline_stages` rows are opened before the
work (`status='running'`, `started_at` set) and closed after it, in two separate
`ConsoleDB.write()` transactions. A process killed mid-run therefore leaves every
finished stage committed and the interrupted one readable as `running` — which is also
exactly what an elapsed-time reading needs. `tests/test_pipeline_stages.py` proves this
by `SIGKILL`ing a real subprocess and reading the database back.

**The source list comes from the fetch ledger, never from the article.** `stage_fetches`
holds one row per attempt to read something, failures included, and
`console_board.process_payload()` builds the research stage from that table alone. An
article can cite any URL it likes; a URL with no fetch record cannot reach the payload.
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

The payload updates live through the existing token: `ceo_version.py` already watches
`console.db` and its `-wal` sidecar, so a stage row committed by the writer reaches an
open console within three seconds with no new mechanism.

## One article, one screen

Opening a blog card used to be a three-tab errand. The article was on **Read**, Approve
and Ask for changes were on **Discussion**, and Publish to website was on **Impact** —
so shipping one piece meant Read, then Discussion, then Impact: two clicks in two places
for one decision, with two tabs in between that carried no action at all.

The blog detail is now **Read** and **Files**. Everything a human does to an article is
on Read, under the article it is being done to:

- the rendered piece, its word count and the Edit / Download / Print bar, as before;
- **Ask for changes** — the same field and the same `POST /ceo/api/revision`, shown only
  where `request_revision` will accept it;
- **Publish to website** — the same eligibility check and the same
  `POST /ceo/blog-publish`, listing the three files it will write before it writes them.

Files is unchanged.

**There is one button, and pressing it is the approval.** `ceo_blog_publish.publish()`
records Gate 1 under the name of the human who pressed it, before anything reaches the
working tree. `approvals.log`, `state/human-approvals.json` and the `Gate 1 approved by`
trailer on the commit are all exactly what they were — the second button is gone, the
record it wrote is not. `GET /ceo/blog-publish-check` therefore asks
`preflight(require_approval=False)`: whether this article *can* be published, not whether
somebody already said it should be.

Two things that click cannot resolve, and both still grey the button out with the reason
on screen. An article that is not finished has nothing to approve — `preflight` refuses
it and `DecisionStore.decide` refuses the same card for the same reason, so the recording
is not a way around the lane. And an approval written before fingerprinting existed cannot
be shown to be stale, so it cannot be superseded either; no click clears it, and saying so
is better than a button that fails.

**Gate 2 is not on this console.** `SOUL.md` section 12 clause 4 offers a human two ways
to merge `cmo-changes` to `main` — directly on GitHub, or a console control — and this
console takes the first. Publishing stops at the preview, as it always did. The routes
`/ceo/publish-check` and `/ceo/publish` and their suite in `test_ceo_publish.py` are still
here and still proven; nothing in the page reaches them, and `/ceo/publish` cannot be
called without a `request_id` that only its own check mints for an eligible card.

## Renaming an article

A blog title used to be written down four times, and kept in step nowhere:

| Where | Written by | What it drives |
|---|---|---|
| the card heading, `### TASK-095 — ...` | `topic_proposals._mint_card`, from `proposal_versions.title` | what greps find |
| the card's `- Title:` field | the same template | `task.title` — the Blogs list and the detail heading |
| the article's front-matter `title:` | the writer skill | `BlogLayout title=` on the published page |
| the article's `# ` H1 | the writer skill | the console reader; the publisher strips it |

`parse_tasks` reads the heading and then lets the `Title` field overwrite it, so the
field is what the console shows and the heading is what everything else greps. Nothing
could write either of them, and the only way to reach the other two was the Markdown
editor — which could not save at all (below). So the title the writer chose was the
title that shipped.

**The pencil beside the title on an open card moves all four in one press.**
`POST /ceo/api/article/title` → `ceo_actions.rename_article`, which rewrites the
front-matter `title:` line and the first H1 and then hands the article to
`save_article_edit` — the same write path the editor uses, so a rename gets the same
512 KB cap, the same refusals, the same `<stem>.r<n>.md` archive of the version it
replaced, and the same `Approval thread N edit` line naming who did it. The board half
goes through `TaskFile.set_card_title`, which moves the heading and the field under one
lock and one commit so they cannot land apart.

What it does not touch: **the slug**, so the page keeps its address, and
**`meta_title`**, which is the search title and a different sentence on purpose.

Refusals, all with the reason on screen and the button greyed rather than failing:

- an article a human decision still covers — the headline is part of what was approved,
  so it is closed with the rest of it (`Ask for a revision instead`);
- a title that would not read back as typed. The header is not YAML: `ceo_reader`
  strips surrounding quotes and the publisher does not, so `title: "Foo"` would show
  bare here and publish with the quotes on. Refused rather than silently picking one;
- empty, or longer than 180 characters — the cap `proposal_versions.title` already has.

The article and the board are two files and cannot be one transaction. The article is
written first, because that is where the refusals are; if the board write then fails the
error says so, and "unchanged" is judged on the article **and** the card, so pressing
Save again finishes the rename without minting a second revision.

### The editor posts back the whole file

`artifact_payload` splits an article into `front_matter` and `text`. `text` is the prose
— what the reader renders and the Blogs search box reads, with the header deliberately
not in it — and `front_matter` is the block as text, not as the parsed dict, because the
parse lowercases keys, drops quotes and forgets the order.

The browser rejoins them in `articleSource()`, and `ceo_reader.split_source` guarantees
`front_matter + text` is the file byte for byte, on every path including a BOM.

This is load-bearing. The editor used to seed its textarea from `text` alone, and
`check_edited_front_matter` refuses a save that lost the header — so **Save revision
was refused on every article**, with `the front matter is gone`, from the day that guard
landed. Download Markdown had the same hole and produced a file that could not be
published back. Both now carry the header.

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
`PROPOSAL_PAGE_CAP` of them. Search Console answers demand questions first because
it is free. A repeat subject replays cached research for nothing. Runs refuse above
`FIRECRAWL_PROPOSAL_STOP` measured credits rather than degrading quietly.

**A page is not a credit, and neither is a search.** This section used to say the
scrape cost "roughly one credit each"; measured on 2026-08-27 a page cost between
1.5 and **17** credits, and a discovery search — the step described here as
returning URLs only — cost about **3.7**. `PROPOSAL_PAGE_CAP` bounds pages and
does not bound spend, which is why the accounting in `research_runs` is a measured
before/after delta rather than a count, and why the news radar below carries a
credit ceiling instead of trusting the page cap.

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

**Five standing beats, one per kind of development it promises to watch:**

```text
ev-industry   India electric three-wheeler e-rickshaw battery swapping news
policy        India EV policy news
battery-tech  EV battery technology news sodium-ion solid-state
market        India EV sales funding investment news
competitors   built from the console's competitor list, or a general query
```

`competitors` used to be a leftover — appended after the watchlist and kept only if a
slot survived under `RADAR_MAX_BEATS`. That made it silently conditional on the
watchlist being empty: one keyword added on Analytics took the last slot and competitor
news stopped being swept, with nothing saying so. It is standing now, and the watchlist
takes whatever is left instead. Its query rotates one competitor per sweep rather than
naming them all in one — the measured comparison above is why — so several competitors
are covered over a few days at the same flat 2 credits.

**A candidate says which beat found it.** The triager returns a beat with each subject;
that used to be dropped between the triager and the pipeline, so a candidate could not
say which of the five produced it. It is recorded on the `subjects` row (schema 4) and
shown as a pill on the card. A subject typed into the box carries no beat rather than
an invented one.

**A beat that returned nothing is recorded as dry.** `empty_beats` holds the beats that
were searched and contributed no new headline, and the Topics tab names them beside the
ones that worked. Searched-and-quiet and never-searched look identical in a list of
candidates, and only one of them is a reason to change a query.

1. **Live budget check.** Refuses if Firecrawl is not ready, or if remaining credits
   are below `RADAR_CREDIT_FLOOR` — an unattended daily job must never be why the CEO
   cannot research a subject by hand. Refusals are recorded, because a sweep that left
   no trace reads as one that never ran.
2. **Discovery** across every beat — `DEFAULT_BEATS` (EV industry including
   swapping, policy, battery technology, market), plus watchlist entries from
   `state/ceo-watchlist.json` and rows from `competitors` filling whatever slots
   `RADAR_MAX_BEATS` leaves, so the beat is steerable from surfaces the CEO
   already controls without a redeploy.
   `/v2/search` without `scrapeOptions` returns titles, narrowed to
   `RADAR_RECENCY` (`qdr:w`). One dead beat does not end the sweep. **This is
   billed** — see the costs below — so the balance is read after it and the spend
   counts against the ceiling.
3. **One Hermes triage call** turns the pooled headlines into at most
   `RADAR_MAX_SUBJECTS` rough subjects. The cap is enforced in `_subjects_from`, not in
   the prompt: a model asked for three and returning nine must cost three subjects'
   worth of credits, not nine. An empty answer is a correct answer.
4. **`propose()` per subject**, at `PROPOSAL_PAGE_CAP` pages each, until the
   ceiling is reached. One refused subject does not lose the others, and whatever
   the ceiling drops is named in the sweep's messages rather than skipped
   silently.

Note the recency window applies to discovery only. The research behind a topic is
deliberately unbounded: a 2023 gazette notification is exactly the source a policy
piece needs.

#### What it costs, measured

The page caps bound pages and do not bound money. Measured on this account on
2026-08-27, from `research_runs` and the Firecrawl balance:

| | measured |
|---|---|
| one beat search (`/v2/search`, no `scrapeOptions`) | **flat 2 credits** — limits 3, 5 and 8 each cost exactly 2 on fresh uncached queries |
| retrieval, typical | 5 credits for 3 pages; 4 for 2 |
| retrieval, worst seen | **85 for 5 pages**, and **79 for 2** |
| the first unbounded sweep, end to end | **114 credits** (~20 discovery, 94 research) |

Two things follow, and both are counter-intuitive enough to be worth stating.

**`RADAR_DISCOVERY_LIMIT` is free to raise.** A search costs the same at limit 8
as at limit 3, so asking for more headlines per beat costs nothing and gives the
triage prompt more to work with. Cutting it saves nothing.

**The beat count is the entire discovery bill.** At 2 credits a beat it is the only
lever, which is why `RADAR_MAX_BEATS` caps defaults and dynamic additions
*together*. The watchlist and competitor list used to take up to five slots each,
so a filled watchlist could put fifteen searches — 30 credits — in front of a
sweep that had not researched anything yet. Defaults are placed first and the
additions fill what is left, so the standing beat can never be crowded out.

The budget is sized so **three subjects fit a normal day**: 5 beats at 2 credits is
10, three typical subjects are about 5 each, and 25–27 sits under the 28-credit
ceiling. That projects to roughly **795 of the 1000-credit month**, leaving about
205 for manual research — comfortable, not generous. A larger plan is what buys
either a wider beat or a fourth subject.

`RADAR_SWEEP_CREDIT_CEILING` reads the balance after discovery and again after
each subject and stops when it has spent enough, so **how many subjects a sweep
researches is decided by what they cost** — `RADAR_MAX_SUBJECTS` is only the cap
on how many it may consider. The ceiling bounds the sweep, not a single run,
because the check happens between subjects: worst case is the ceiling plus one
expensive run. Bounding one run would need a per-page cost limit Firecrawl does
not offer.

A `--dry-run` skips retrieval but still pays for discovery. It reports that
figure rather than claiming to be free, because it is the thing you run in a loop
while tuning the beats.

Every sweep, refusals included, lands in `radar_runs` and the latest is rendered on the
console as `topics.radar`.

Two ways to run it by hand:

```bash
# what it would research, spending nothing
python -m cmo_runtime.news_radar --profile "$CMO_DASHBOARD_PROFILE_DIR" --dry-run

# one sweep, subject to the daily clock
python -m cmo_runtime.news_radar --profile "$CMO_DASHBOARD_PROFILE_DIR" --due
```

It lives in `cmo_runtime/` and not in `scripts/` on purpose: `deploy-dashboard` copies
`cmo-dashboard/*.py`, `*.js` and `cmo_runtime/*.py`, and nothing under `scripts/`. A
radar under `scripts/` would be committed and never shipped.

### What actually schedules the sweep

**There is no cron on this box.** No `crontab` binary, no `/etc/cron.d`;
`cron/cmo-agents.crontab` was never installed and its own header tells you to install it
with a command that does not exist. The hermes cron ticker holds zero jobs and last beat
2026-08-10.

**And the watchdog that used to be the scheduler is gone.** `start-cmo-agents:31` ran
`hourly-cycle.py --once` then `morning-seo-job.py --due` on a `sleep 3600` loop — *"the
watchdog is the scheduler when cron/systemd are unavailable"*. Both it and
`ensure-cmo-agents` have refused to run since **2026-08-04**: *"v1 orchestration
decommissioned. Two parallel stacks ran against one tasks.md for 11 days. Do not
re-enable without explicit founder approval."* `hourly-cycle.log` ends that same day.
So "add a line to the watchdog" is not an available option, and adding one would be a
re-enablement decision, not a wiring detail.

The radar therefore carries its own supervisor, `bin/run-news-radar`, modelled on
`bin/run-content-worker` — the one long-lived pattern here that has survived. It holds a
`cmo-news-radar` tmux session running `--due` every 30 minutes; the clock lives in the
Python, so a tick outside the 07:00 IST window is a cheap no-op and a container restart
at 06:59 cannot skip the day. Liveness is the pane's `#{pane_dead}`, not a `pgrep`:
between sweeps this loop is a `sleep`, so there is no process of its own to find.

```bash
bin/run-news-radar          # idempotent; exits 0 if a healthy session is already up
tail -f "$CMO_DASHBOARD_PROFILE_DIR/logs/news-radar.log"
```

**This is not a revival of v1 orchestration**, and the reason is structural rather than
a promise: the radar writes to `state/console.db` only, and `propose()` mints no board
card, so nothing on this path can touch `tasks.md`. The failure that got v1
decommissioned — two stacks writing one board — is not reachable from here.

`bin/` is **not** copied by `deploy-dashboard` either. Install the supervisor by hand,
as hermes:

```bash
install -o hermes -g hermes -m 0755 bin/run-news-radar "$CMO_DASHBOARD_PROFILE_DIR/bin/"
```

Everything under the profile is hermes-owned. Running the radar as any other user leaves
a lock nobody else can take — that happened, so `main()` now names the cause instead of
raising a `PermissionError` from `touch`, which reads as a missing file.

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
