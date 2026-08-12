#!/usr/bin/env bash
# What has to be added to the container's /entrypoint.sh, kept here because
# /entrypoint.sh is not in this repository.
#
# /entrypoint.sh lives in the image, is owned by root, and is what PID 1 runs. It
# starts the hermes gateway and the hermes dashboard and nothing else — which
# means anything else this box relies on comes back only if a human remembers to
# start it. The content worker cannot be one of those things: if it is down, an
# approved topic sits in Backlog and Sanchit sees a console that looks fine and
# does nothing.
#
# A container *restart* keeps /entrypoint.sh, so editing it there is what makes
# the worker survive one. A container *rebuild* replaces it, and this file is how
# the edit is reapplied — run it as root, or paste the block below by hand.
#
#   sudo ./scripts/entrypoint-additions.sh          # apply, idempotent
#   sudo ./scripts/entrypoint-additions.sh --check  # report, change nothing
set -euo pipefail

ENTRYPOINT="${CMO_ENTRYPOINT:-/entrypoint.sh}"
MARKER='run-content-worker'

# Same shape as the gateway block already in /entrypoint.sh: guard on the process
# not already running, drop to hermes with gosu, log to /opt/data/logs, and never
# let a failure here stop the container from coming up.
read -r -d '' BLOCK <<'ADDITION' || true

# The content worker turns an approved topic into a writer run. Without it the
# board fills up with approved cards that nothing ever starts.
if [[ -x /opt/data/profiles/itarang_cmo/bin/run-content-worker ]]; then
  gosu hermes /opt/data/profiles/itarang_cmo/bin/run-content-worker \
    >>/opt/data/logs/content-worker.log 2>&1 || true
fi
ADDITION

if grep -qF "$MARKER" "$ENTRYPOINT" 2>/dev/null; then
  printf 'already present in %s\n' "$ENTRYPOINT"
  exit 0
fi

if [[ "${1:-}" == "--check" ]]; then
  printf 'MISSING from %s — the worker will not survive a container restart\n' "$ENTRYPOINT" >&2
  exit 1
fi

# Insert before the final `hermes dashboard` line: that one runs in the
# foreground and is what keeps PID 1 alive, so anything after it never executes.
python3 - "$ENTRYPOINT" "$BLOCK" <<'PYTHON'
import sys
from pathlib import Path

path, block = Path(sys.argv[1]), sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
anchor = next(
    (index for index, line in enumerate(lines) if "hermes dashboard" in line and "gosu" in line),
    len(lines),
)
lines.insert(anchor, block.rstrip("\n") + "\n\n")
path.write_text("".join(lines), encoding="utf-8")
print(f"added the content worker to {path} before line {anchor + 1}")
PYTHON
