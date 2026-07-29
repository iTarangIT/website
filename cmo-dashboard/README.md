# CMO website preview and metrics workflow

This directory contains the dashboard approval endpoint and the hourly website evidence cycle.

## Website change flow

1. The implementation worker changes and pushes `cmo-changes` and returns a commit hash plus three review lines. After a rejection, it must also return a non-empty `reply` field in the same compact JSON result, describing what changed in response to the outstanding rejection comment; otherwise the hourly cycle bounces the resubmission back to In Progress.
2. The hourly cycle captures Lighthouse baseline metrics before dispatching website implementation. A website task without explicit `Affected pages` URLs is not dispatched.
3. Gate 1 is the dashboard approval. Approval requires the pre-existing captured baseline and an implementation commit. The approval endpoint triggers the Vercel deploy hook for `cmo-changes`, records the fixed preview URL, and posts the preview URL, live URL, and three “what to look at” lines to Discord.
4. The system records the task as awaiting merge. It never merges.
5. A human merges to `main` on GitHub. Existing CI deploys live. The hourly cycle waits for the live deployment to settle, captures the same Lighthouse and SEO metrics, writes a before/after/delta table to the task card, and posts the evidence to Discord.
6. The Monday hourly cycle posts the cumulative weekly page-weight, performance-score, and SEO-fix summary. No additional always-on loop is created.

`VERCEL_TOKEN` is read only from the process environment and is sent as an Authorization header to the deploy hook. It is never written to task state, logs, Discord, or the hook response.

## Environment variables

Required for the production dashboard and website preview gate:

- `CMO_DASHBOARD_USERNAME` — dashboard Basic Auth username.
- `CMO_DASHBOARD_PASSWORD` — dashboard Basic Auth password.
- `CMO_DASHBOARD_PROFILE_DIR` — profile directory containing `tasks.md`, state, and logs.
- `CMO_DASHBOARD_GIT_REPO` — absolute website repository path.
- `VERCEL_DEPLOY_HOOK_URL` — Vercel project deploy-hook URL configured for the `cmo-changes` branch.
- `VERCEL_TOKEN` — Vercel API token; environment-only, never store in the repository or task state.
- `CMO_PREVIEW_URL` — fixed preview URL reviewers open (`https://itarangwebsite.vercel.app`).
- `CMO_LIVE_URL` — production URL reviewers compare against.
- `CMO_DISCORD_WEBHOOK_URL` — Discord webhook used for immediate Gate 1 preview notices and evidence posts.

Required for baseline/live measurements:

- `LIGHTHOUSE_BIN` — optional executable override; defaults to `npx` and runs Lighthouse with performance and SEO categories.
- `CMO_SPEND_TRACKER` — absolute path to `spend-tracker.py`; measurement and notification calls are recorded with zero/none cost entries.

Optional runtime settings:

- `CMO_DASHBOARD_HOST` — bind address, default `0.0.0.0`.
- `CMO_DASHBOARD_PORT` — bind port, default `8080`.
- `CMO_DASHBOARD_PREVIEW` — set to `true` only on a non-production dashboard; approval POSTs are disabled there.
- `CMO_LIVE_SETTLE_SECONDS` — hourly-cycle wait after detecting the merge, default `600`.
- `CMO_DISCORD_TARGET` — target used by the hourly cycle’s existing Discord CLI path.

## Run and verify

From the repository root:

```bash
python3 -m unittest discover -s cmo-dashboard -p 'test_*.py' -v
python3 cmo-dashboard/dashboard_server.py
```

The hourly job remains the existing once-per-hour invocation:

```bash
python3 cmo-dashboard/scripts/hourly-cycle.py --once
```
