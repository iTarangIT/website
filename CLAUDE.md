@AGENTS.md

# iTarang website + CMO dashboard

## 1. Project overview

Two deliverables live in this one repo.

**Root — the iTarang marketing/portal site.** Next.js 16.2 (App Router) + React 19,
TypeScript, Tailwind 4, Radix UI. Route groups under `src/app`:

- `(marketing)` — public site: home, products, blog, `for-drivers` / `for-dealers` /
  `for-oems` / `for-partners` / `for-investors`, SEO landing hubs.
- `(portal)` — `itarang/*` (internal ops) and `nbfc/*` (partner demo dashboard,
  static mock data in `src/lib/nbfc-mock-data.ts`, demo `localStorage` auth).
- `api/*` — chat/RAG (Groq + Pinecone), loan calculator (Postgres via
  `src/lib/db`), 2Factor OTP, WhatsApp Cloud API, ElevenLabs AI caller,
  Firecrawl ingest.

Content lives as typed modules in `src/data/*` (blog posts, products, specs,
portal fixtures) — most "content edits" are edits there, not to page components.

Deployment: pushing `main` runs `.github/workflows/deploy.yml`. The GitHub runner
does `npm ci && npm run build`, tars `.next`, scps it to the **Hostinger VPS**, then
over SSH resets the checkout to the pushed SHA, swaps `.next` in, and
`pm2 restart itarang-website`. The VPS never builds — it is a shared 8 GB box that
has OOM'd on `next build`. `.github/workflows/ci-cd.yml` runs typecheck + lint +
build on every PR to `main` (lint is `continue-on-error` for now: pre-existing
errors in unrelated files).

**`cmo-dashboard/` — Python dashboard for the CMO agent system.** Stdlib-only
HTTP server (`dashboard_server.py`, `http.server`), Basic Auth, read-only task
board rendered from `tasks.md` in the profile dir, plus the one write path:
Human Approval (approve/reject) on pending website changes. `preview_metrics.py`
captures Lighthouse/SEO baselines and posts evidence to Discord;
`scripts/hourly-cycle.py` is the once-per-hour orchestration entrypoint.
Runtime state (`tasks.md`, `state/`, `logs/`) lives **outside** the repo under
`CMO_DASHBOARD_PROFILE_DIR` (default `/opt/data/profiles/itarang_cmo`).
Read `cmo-dashboard/README.md` before touching the approval or metrics flow —
it documents the gate sequence and every env var.

Note `deploy.yml` has `paths-ignore: cmo-dashboard/**`, so dashboard changes
never trigger a website deploy.

## 2. Branch discipline

- **All changes go on `cmo-changes`. Never commit to `main`.** Never merge to
  `main`, never push `main`, never open-and-merge your own PR.
- Humans merge via PR on GitHub. Agents stop at "pushed to `cmo-changes`."
- The Vercel preview at **https://itarangwebsite.vercel.app** auto-deploys
  `cmo-changes` — that fixed URL is what reviewers open at Gate 1. It does not
  change per deploy; don't invent per-commit preview URLs.
- Merging `main` triggers the VPS deploy above; the hourly cycle then waits for
  live to settle and captures before/after metrics. The agent system never merges.

## 3. Build rules — do not build in this container

**Never run `npm run build`, `next build`, or `npm run lint` here.** The container
runs at ~460 MB free and these OOM. Builds and lint belong on GitHub runners and
Vercel, which already run them on every PR and on `cmo-changes`.

In-container checks, in order of preference:

```bash
# Python — syntax
python3 -m py_compile cmo-dashboard/dashboard_server.py

# Python — unit tests (fast, safe, no network)
python3 -m unittest discover -s cmo-dashboard -p 'test_*.py' -v

# TypeScript — CHANGED FILES ONLY, never a whole-project tsc --noEmit
npx tsc --noEmit --skipLibCheck --jsx react-jsx --module esnext \
  --moduleResolution bundler --target ES2017 <changed-file.tsx>
```

`npm run dev` is also too heavy to leave running — start it only if a change
genuinely cannot be verified any other way, and kill it immediately after.

## 4. Secrets

- Secrets live in env files only: `.env.local` (website, see `.env.local.example`
  for the full key list) and the process environment for the dashboard
  (`VERCEL_TOKEN`, `CMO_DASHBOARD_PASSWORD`, `CMO_DISCORD_WEBHOOK_URL`, …).
- **Never print a secret value** — not in tool output, logs, Discord posts, task
  state, or commit messages. Grep for a key's *name* to confirm wiring; never
  `cat` an env file. `VERCEL_TOKEN` in particular is env-only by design.
- **Never commit one.** `.gitignore` already excludes `.env*`,
  `cmo-dashboard/state/`, `cmo-dashboard/logs/`, and `__pycache__`. `tasks.md`
  needs no rule — it lives in the profile dir outside the repo. If you ever find
  a `tasks.md`, `state/`, or `logs/` inside the repo tree, that is a bug: move it
  back under `CMO_DASHBOARD_PROFILE_DIR` rather than committing it.
- New secret-bearing config: add the key with an empty value to
  `.env.local.example` and document it in `cmo-dashboard/README.md`.

## 5. Deploy rule for `cmo-dashboard`

**The repo is not the live surface.** `dashboard_server.py` runs from
`$CMO_DASHBOARD_PROFILE_DIR/dashboard/`, which is a **copy** of `cmo-dashboard/` —
not a checkout, not a symlink. Committing a console change makes it visible to
nobody. `cmo_runtime/` is copied to the profile root the same way. Editing a
console file and stopping at the commit is a change that never shipped; this has
happened, and it is why the build stamp in §5.1 exists.

Deploy with the script, which copies, restarts and verifies in one step:

```bash
cd cmo-dashboard
./deploy-dashboard --dry-run   # what would change
./deploy-dashboard             # copy, restart, verify
```

It refuses to report `DEPLOYED` unless the **served** `X-CMO-Build` header
actually changed, so a copy that never reached the running process fails loudly
instead of passing quietly.

Never name a shell variable `TMUX` in any script here. Inside a tmux pane it is
already exported, so assigning to it rewrites tmux's own socket path for every
child; the next server then creates its socket over whatever is at that path.
That is how `$PROFILE_DIR/bin/tmux` — a symlink to the real binary — was once
replaced by a socket.

If you restart by hand instead, the rule is unchanged: **end with a curl health
check on the port**, and leave **no orphan processes**.

Run it as `hermes`. **There is no `sudo` on this box** — it is `gosu`.

```bash
gosu hermes bash -c '
  P=/opt/data/profiles/itarang_cmo

  # 1. stop the old server first — never leave a second one bound to the port.
  #    Scope the pattern to THIS profile: a bare `dashboard_server.py` also
  #    matches the unrelated meet_ops dashboard on port 8090, and an unscoped
  #    pkill takes that down with it.
  "$P/bin/tmux" kill-session -t cmo-dashboard 2>/dev/null || true
  pkill -f "$P/dashboard/dashboard_server.py" || true
  sleep 2

  # 2. start the new one through its supervisor
  "$P/bin/run-dashboard"
'

# 3. MANDATORY: health check. `run-dashboard` returns as soon as tmux has
#    forked, so the port is not bound yet — poll rather than curl once, or a
#    healthy restart reports 000 and reads as a failure.
for _ in $(seq 15); do
  code="$(curl -s -o /dev/null -w '%{http_code}' -m 2 \
    "http://127.0.0.1:${CMO_DASHBOARD_PORT:-8080}/")"
  [ "$code" != "000" ] && break
  sleep 1
done
echo "HTTP $code"
```

A deploy is not done until the curl returns (401 from Basic Auth is a healthy
response — the server is up; so is 200). If the check fails, stop the process you
started and report the failure; do not leave a half-started server behind. Before
declaring done, confirm exactly one server is running — again scoped to this
profile: `pgrep -cf "$PROFILE_DIR/dashboard/dashboard_server.py"` must print `1`.

The supervisor exports `LD_LIBRARY_PATH` for the vendored tmux, which carries its
own libevent. It did not always: the missing export failed as
`libevent_core-2.1.so.7: cannot open shared object file`, which reads exactly like
a missing binary, and because step 1 has already stopped the old server the
console is left **down**. If you ever see that error, the profile's
`bin/run-dashboard` is older than `cmo-dashboard/bin/run-dashboard`.

`deploy-dashboard` copies only `*.py` and `*.js` (plus `cmo_runtime/*.py`), so
**nothing under `bin/` is ever shipped by a deploy** — the repo copy is the source
of truth and the profile copy is installed by hand, as `hermes`, the same way
`run-news-radar` is:

```bash
gosu hermes install -o hermes -g hermes -m 0700 \
  cmo-dashboard/bin/run-dashboard "$PROFILE_DIR/bin/"
```

### 5.1 Say which build you are looking at

Every console page renders a build stamp in its footer and returns the same value
as the `X-CMO-Build` response header: the mtime of the newest `dashboard/*.py` on
the serving box, and a 12-character digest of the assembled page.

```bash
curl -fsS -o /dev/null -D - http://127.0.0.1:8080/ceo | grep -i x-cmo-build
```

Two different questions: the mtime catches a deploy that never ran, the digest
catches one that ran and landed the wrong bytes. Quote both when reporting a
console change.

**Claims about the console need served bytes behind them.** `test_served_bytes.py`
starts the server against a temporary profile, fetches over a socket, and asserts
on what comes back — a rendered `<table>`, the tab order, the editor control, the
build stamp. Assert that something *works*, not that a name is *present* in a
module; every regression on this console has been the second kind of test passing
while the first kind was missing.

## 6. Next.js version warning

See `AGENTS.md` (imported above): this is Next.js 16.2 and it has breaking changes
versus older training data. Read the relevant guide in `node_modules/next/dist/docs/`
before writing App Router, routing, or config code.
