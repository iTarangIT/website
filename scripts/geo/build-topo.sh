#!/usr/bin/env bash
# Rebuild scripts/geo/india-states.topo.json from its sources.
#
#   bash scripts/geo/build-topo.sh [work-dir]     # default work-dir: scripts/geo/.work (gitignored)
#
# Needs curl and node; mapshaper is fetched by npx. Sources, licences and the
# reasoning behind each step are in README.md next to this file. Downloads are
# skipped when the work dir already holds them, so re-runs are cheap.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${1:-$HERE/.work}"
OUT="$HERE/india-states.topo.json"
M="npx --yes mapshaper"

mkdir -p "$WORK/soi"
SOI="https://raw.githubusercontent.com/datameet/maps/master/Survey-of-India-Index-Maps/StateBoundary/StateBoundary"
for ext in cpg dbf prj shx shp; do
  [ -s "$WORK/soi/StateBoundary.$ext" ] || curl -fsSL -C - -o "$WORK/soi/StateBoundary.$ext" "$SOI.$ext"
done
UDIT="https://cdn.jsdelivr.net/gh/udit-001/india-maps-data@2884453/topojson/india.json"
[ -s "$WORK/udit-india.json" ] || curl -fsSL -o "$WORK/udit-india.json" "$UDIT"

cd "$WORK"

# 1. Survey of India state polygons -> WGS84 with display names. The download
#    lists Daman & Diu and Dadra & Nagar Haveli separately (merged as one UT in
#    2020) and Puducherry as two rows, so dissolve on the display name.
$M soi/StateBoundary.shp -proj wgs84 \
  -each 'name = ({"ANDAMAN & NICOBAR":"Andaman and Nicobar Islands","DADAR & NAGAR HAVELI":"Dadra and Nagar Haveli and Daman and Diu","DAMAN & DIU":"Dadra and Nagar Haveli and Daman and Diu","JAMMU & KASHMIR":"Jammu and Kashmir"})[state] || state.toLowerCase().replace(/(^|\s)\S/g, function (c) { return c.toUpperCase(); })' \
  -dissolve fields=name \
  -o soi_named.json format=geojson

# 2. The SoI download predates the 2019 split of Ladakh from J&K. Only the
#    internal dividing line is taken from the fallback dataset; the outer
#    outline stays Survey of India's.
$M udit-india.json -target states -filter "st_nm=='Ladakh'" -o udit_ladakh.json format=geojson
$M soi_named.json -filter "name=='Jammu and Kashmir'" -o jk.json format=geojson
# main J&K body = SoI J&K minus the Ladakh cutter, largest piece only (drops edge slivers)
$M jk.json -erase udit_ladakh.json -explode -filter 'this.area > 1e10' -dissolve \
  -each 'name="Jammu and Kashmir"' -o jkmain.json format=geojson
# Ladakh = SoI J&K minus that body, so the two tile the original polygon exactly
$M jk.json -erase jkmain.json -dissolve -each 'name="Ladakh"' -o ladakh.json format=geojson

# 3. Combine, clean, simplify (2.5 km tolerance is sub-pixel on a 600 px map),
#    drop islands under 2 km2, and write TopoJSON with only the name property.
$M soi_named.json jkmain.json ladakh.json combine-files \
  -filter "name!='Jammu and Kashmir'" target=soi_named \
  -merge-layers target=soi_named,jkmain,ladakh name=states \
  -filter-fields name \
  -clean \
  -simplify interval=2500 keep-shapes \
  -filter-islands min-area=2km2 remove-empty \
  -clean \
  -o "$OUT" format=topojson

node -e '
const t = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
const n = t.objects.states.geometries.length;
if (n !== 36) { console.error("expected 36 features, got " + n); process.exit(1); }
console.log("wrote " + process.argv[1] + " with " + n + " features, " + t.arcs.length + " arcs");
' "$OUT"
