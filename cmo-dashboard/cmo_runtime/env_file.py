"""Read one configuration value from the process environment or the profile `.env`.

Two modules had grown identical private copies of this — `content_flow` and
`topic_proposals` — and a third was about to. The lookup order matters and is the
reason it is not just `os.getenv`: the content worker inherits an environment, the
dashboard is started by `run-dashboard` which sources `$PROFILE_DIR/.env`, and a
test harness sets neither and writes a `.env` into a temporary root. All three have
to resolve the same key.

Nothing here logs, echoes, or returns the value anywhere but to its caller. A key
read through this function must never reach a log line, a Discord post, task state,
or a commit message.
"""

from __future__ import annotations

import os
from pathlib import Path


def read_env_value(root: str | Path, name: str) -> str:
    """Return `name` from the environment, else from `root/.env`, else empty."""
    direct = os.getenv(name, "").strip()
    if direct:
        return direct
    env_path = Path(root) / ".env"
    if not env_path.is_file():
        return ""
    for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() == name:
            return value.strip().strip("'\"")
    return ""
