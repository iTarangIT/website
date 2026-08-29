#!/usr/bin/env bash
# What has to be added to the container's /entrypoint.sh, kept here because
# /entrypoint.sh is not in this repository.
#
# /entrypoint.sh lives in the image, is owned by root, and is what PID 1 runs. It
# starts the hermes gateway and the hermes dashboard and nothing else — which
# means anything else this box relies on comes back only if a human remembers to
# start it.
#
# This is also where scheduling lives, because there is nowhere else. There is no
# cron on this box: no `crontab` binary, no /etc/cron.d, and `apt-get install
# cron` pulls exim4-daemon-light, bsd-mailx and systemd-cryptsetup onto a
# container whose PID 1 is a shell script — an MTA and init fragments to run one
# job a day, with nothing to supervise crond afterwards. The watchdog that used
# to be the scheduler was decommissioned on 2026-08-04 and its scripts refuse to
# run. So each scheduled thing carries its own loop, and this file is what makes
# those loops start.
#
# A container *restart* keeps /entrypoint.sh, so editing it there is what makes
# them survive one. A container *rebuild* replaces it, and this file is how the
# edit is reapplied — run it as root, or paste the blocks below by hand.
#
#   sudo ./scripts/entrypoint-additions.sh          # apply, idempotent
#   sudo ./scripts/entrypoint-additions.sh --check  # report, change nothing
set -euo pipefail

ENTRYPOINT="${CMO_ENTRYPOINT:-/entrypoint.sh}"

# Same shape as the gateway block already in /entrypoint.sh: guard on the thing
# not already being up, drop to hermes with gosu, log under /opt/data/logs, and
# never let a failure here stop the container from coming up. Each supervisor is
# idempotent, so running them on every boot is safe.
#
# Marker → block. The marker is what makes reapplying a no-op; it must appear in
# the block and nowhere else in /entrypoint.sh.
MARKERS=(run-content-worker run-news-radar)

block_for() {
  case "$1" in
    run-content-worker)
      cat <<'ADDITION'

# The content worker turns an approved topic into a writer run. Without it the
# board fills up with approved cards that nothing ever starts.
if [[ -x /opt/data/profiles/itarang_cmo/bin/run-content-worker ]]; then
  gosu hermes /opt/data/profiles/itarang_cmo/bin/run-content-worker \
    >>/opt/data/logs/content-worker.log 2>&1 || true
fi
ADDITION
      ;;
    run-news-radar)
      cat <<'ADDITION'

# The news radar sweeps the EV beat once a day at 07:00 IST and turns what it
# finds into topic proposals. This box has no cron, so the schedule is a loop in
# a tmux session and this is what starts it. Without it nothing produces a topic
# and the console only ever shows what a human typed in.
if [[ -x /opt/data/profiles/itarang_cmo/bin/run-news-radar ]]; then
  gosu hermes /opt/data/profiles/itarang_cmo/bin/run-news-radar \
    >>/opt/data/logs/news-radar-boot.log 2>&1 || true
fi
ADDITION
      ;;
    *) return 1 ;;
  esac
}

missing=()
for marker in "${MARKERS[@]}"; do
  grep -qF "$marker" "$ENTRYPOINT" 2>/dev/null || missing+=("$marker")
done

if ((${#missing[@]} == 0)); then
  printf 'all present in %s: %s\n' "$ENTRYPOINT" "${MARKERS[*]}"
  exit 0
fi

if [[ "${1:-}" == "--check" ]]; then
  printf 'MISSING from %s: %s — these will not survive a container restart\n' \
    "$ENTRYPOINT" "${missing[*]}" >&2
  exit 1
fi

for marker in "${missing[@]}"; do
  # The block goes in argv, not on stdin: `python3 -` reads its *program* from
  # stdin, so piping the block there leaves sys.stdin at EOF and inserts nothing
  # while still reporting success. That happened; hence this comment.
  block="$(block_for "$marker")"
  # Insert before the final `hermes dashboard` line: that one runs in the
  # foreground and is what keeps PID 1 alive, so anything after it never
  # executes. Re-read the file each time so two insertions cannot race the
  # anchor they both aim at.
  python3 - "$ENTRYPOINT" "$marker" "$block" <<'PYTHON'
import sys
from pathlib import Path

path, marker, block = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if marker not in block:
    raise SystemExit(f"refusing to insert a block that does not contain its marker {marker!r}")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
anchor = next(
    (index for index, line in enumerate(lines) if "hermes dashboard" in line and "gosu" in line),
    len(lines),
)
lines.insert(anchor, block.rstrip("\n") + "\n\n")
path.write_text("".join(lines), encoding="utf-8")
print(f"added {marker} to {path} before line {anchor + 1}")
PYTHON
done
