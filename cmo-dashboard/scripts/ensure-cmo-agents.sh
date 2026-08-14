#!/usr/bin/env bash
# Cron-safe, idempotent self-heal check for the five persistent CMO sessions.
set -euo pipefail
PROFILE_DIR="/opt/data/profiles/itarang_cmo"
TMUX="$PROFILE_DIR/bin/tmux"
START="$PROFILE_DIR/bin/start-cmo-agents"
LOG="$PROFILE_DIR/logs/cmo-self-heal.log"
mkdir -p "$(dirname "$LOG")"
missing=()
for role in social seo ads content ops; do
  if ! "$TMUX" has-session -t "cmo-$role" 2>/dev/null; then
    missing+=("cmo-$role")
  fi
done
if ((${#missing[@]})); then
  "$START" >/dev/null
  printf '%s recreated: %s\n' "$(date -Is)" "${missing[*]}" >> "$LOG"
fi
