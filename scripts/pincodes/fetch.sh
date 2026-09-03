#!/usr/bin/env bash
# Download the GeoNames postal-code file for India.
#
#   bash scripts/pincodes/fetch.sh [work-dir]   # default: scripts/pincodes/.work (gitignored)
#
# Only curl and unzip are needed. The download is ~1.7 MB and expands to ~11 MB,
# which is why it is not committed; scripts/build-pincode-areas.ts reduces it to
# the ~400-row table that is. Source and licence: README.md next to this file.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${1:-$HERE/.work}"
URL="https://download.geonames.org/export/zip/IN.zip"

mkdir -p "$WORK"
[ -s "$WORK/IN.zip" ] || curl -fsSL -o "$WORK/IN.zip" "$URL"
# The readme carries the licence text; keep it beside the data it applies to.
[ -s "$WORK/geonames-readme.txt" ] || curl -fsSL -o "$WORK/geonames-readme.txt" \
  "https://download.geonames.org/export/zip/readme.txt"
unzip -o -q "$WORK/IN.zip" -d "$WORK"

echo "IN.txt: $(wc -l < "$WORK/IN.txt") rows in $WORK"
