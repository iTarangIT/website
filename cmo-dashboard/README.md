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

## Behavior

- The browser polls `GET /api/state` every 10 seconds.
- The server re-reads `tasks.md` on every request.
- tmux health is read from `/opt/data/profiles/itarang_cmo/bin/tmux ls`.
- The UI has agent tabs and a four-column board: Task List, Under Review (CMO), Under Review (Human), Completed.
- All state endpoints are GET-only. POST, PUT, PATCH, and DELETE return 405.
- No database, task actions, or file writes are used by the dashboard.
- Basic Auth credentials are read only from `CMO_DASHBOARD_USERNAME` and `CMO_DASHBOARD_PASSWORD`.
