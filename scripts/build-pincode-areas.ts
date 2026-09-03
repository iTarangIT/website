/**
 * Generate src/data/pincode-areas.ts from the GeoNames postal-code file.
 *
 * Usage:
 *   bash scripts/pincodes/fetch.sh     # once, downloads into .work/
 *   npm run pincodes:build
 *
 * Source, licence and the reasoning behind the three-digit granularity are in
 * scripts/pincodes/README.md. In short: reduce ~155k post offices to one point
 * per three-digit prefix, and let the state polygons decide which state each
 * point belongs to rather than trusting the file's own (stale) state column.
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { indiaMap } from "../src/data/india-map-paths";
import { canonicalState, stateFromPincode } from "../src/lib/dealers/india-states";
import { mercator } from "../src/lib/geo/mercator";
import { parsePathRings, pointInRings, type Ring } from "../src/lib/geo/rings";

const ROOT = process.cwd();
const SOURCE = resolve(ROOT, "scripts/pincodes/.work/IN.txt");
const OUTPUT = resolve(ROOT, "src/data/pincode-areas.ts");

/** Guard rails from the run recorded in scripts/pincodes/README.md. */
const MIN_ROWS = 150_000;
const MIN_PREFIXES = 380;
const MAX_UNPLACED = 20;

interface Office {
  pin: string;
  state: string;
  district: string;
  lat: number;
  lng: number;
}

function median(values: number[]): number {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = sorted.length >> 1;
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function commonest(values: string[]): string {
  const counts = new Map<string, number>();
  for (const v of values) if (v) counts.set(v, (counts.get(v) ?? 0) + 1);
  let best = "";
  let bestCount = 0;
  for (const [value, count] of counts) {
    if (count > bestCount) {
      best = value;
      bestCount = count;
    }
  }
  return best;
}

function readOffices(): Office[] {
  if (!existsSync(SOURCE)) {
    throw new Error(`${SOURCE} is missing — run: bash scripts/pincodes/fetch.sh`);
  }
  const offices: Office[] = [];
  for (const line of readFileSync(SOURCE, "utf8").split("\n")) {
    if (!line) continue;
    const f = line.split("\t");
    const pin = f[1];
    const lat = Number(f[9]);
    const lng = Number(f[10]);
    if (!/^[1-9][0-9]{5}$/.test(pin) || !Number.isFinite(lat) || !Number.isFinite(lng)) continue;
    offices.push({ pin, state: f[3] ?? "", district: f[5] ?? "", lat, lng });
  }
  return offices;
}

function main(): void {
  const offices = readOffices();
  if (offices.length < MIN_ROWS) {
    throw new Error(`only ${offices.length} usable rows, expected at least ${MIN_ROWS} — is the download truncated?`);
  }

  // Two medians, not one. Averaging offices directly would let a pin code with
  // fifty branches outvote twenty other pin codes in the same prefix.
  const byPin = new Map<string, Office[]>();
  for (const office of offices) {
    const list = byPin.get(office.pin);
    if (list) list.push(office);
    else byPin.set(office.pin, [office]);
  }
  const byPrefix = new Map<string, { points: [number, number][]; states: string[]; districts: string[] }>();
  for (const [pin, rows] of byPin) {
    const prefix = pin.slice(0, 3);
    const bucket = byPrefix.get(prefix) ?? { points: [], states: [], districts: [] };
    bucket.points.push([median(rows.map((r) => r.lat)), median(rows.map((r) => r.lng))]);
    bucket.states.push(...rows.map((r) => r.state));
    bucket.districts.push(...rows.map((r) => r.district));
    byPrefix.set(prefix, bucket);
  }

  const polygons = new Map<string, Ring[]>(indiaMap.states.map((s) => [s.name, parsePathRings(s.d)]));

  const areas: { prefix: string; name: string; state: string; lat: number; lng: number }[] = [];
  const unplaced: string[] = [];
  const disagreed: string[] = [];

  for (const prefix of [...byPrefix.keys()].sort()) {
    const bucket = byPrefix.get(prefix)!;
    const lat = median(bucket.points.map((p) => p[0]));
    const lng = median(bucket.points.map((p) => p[1]));
    const [x, y] = mercator(lng, lat, indiaMap);

    // Whichever polygon actually contains the point wins. GeoNames still files
    // Ladakh under Jammu & Kashmir; this puts the 194x prefixes back without a
    // hand-written exception, and catches any other stale row the same way.
    let state = "";
    for (const [name, rings] of polygons) {
      if (pointInRings(x, y, rings)) {
        state = name;
        break;
      }
    }
    const claimed = canonicalState(commonest(bucket.states));
    const byPin3 = stateFromPincode(`${prefix}001`);
    if (!state) {
      // Coastal and island points can fall just outside a simplified outline.
      state = claimed ?? byPin3 ?? "";
      if (state) unplaced.push(`${prefix} -> ${state} (outside every polygon, took the file's own state)`);
    }
    if (!state) continue;
    if (claimed && claimed !== state) disagreed.push(`${prefix}: file says ${claimed}, polygon says ${state}`);

    const district = commonest(bucket.districts) || state;
    areas.push({
      prefix,
      name: district,
      state,
      lat: Math.round(lat * 1e4) / 1e4,
      lng: Math.round(lng * 1e4) / 1e4,
    });
  }

  if (areas.length < MIN_PREFIXES) {
    throw new Error(`only ${areas.length} prefixes resolved, expected at least ${MIN_PREFIXES}`);
  }
  if (unplaced.length > MAX_UNPLACED) {
    throw new Error(`${unplaced.length} prefixes fell outside every polygon (limit ${MAX_UNPLACED}):\n  - ${unplaced.join("\n  - ")}`);
  }

  const lines = [
    "// GENERATED by scripts/build-pincode-areas.ts — do not edit by hand.",
    "// Postal code data © GeoNames, CC BY 4.0, https://www.geonames.org",
    "// Rebuild: bash scripts/pincodes/fetch.sh && npm run pincodes:build",
    "// See scripts/pincodes/README.md for the source, the licence and why this",
    "// table is three-digit prefixes rather than full pin codes.",
    "",
    "export interface PincodeArea {",
    "  /** First three digits of a pin code: an India Post sorting district. */",
    "  prefix: string;",
    "  /** District the prefix mostly covers; shown to say where a search landed. */",
    "  name: string;",
    "  /** Canonical state name, matching src/data/india-map-paths.ts. */",
    "  state: string;",
    "  lat: number;",
    "  lng: number;",
    "}",
    "",
    "export const PINCODE_AREAS: readonly PincodeArea[] = [",
    ...areas.map(
      (a) =>
        `  { prefix: ${JSON.stringify(a.prefix)}, name: ${JSON.stringify(a.name)}, state: ${JSON.stringify(a.state)}, lat: ${a.lat}, lng: ${a.lng} },`,
    ),
    "];",
    "",
  ];
  const output = lines.join("\n");
  writeFileSync(OUTPUT, output);

  console.log(`wrote ${OUTPUT} (${(Buffer.byteLength(output) / 1024).toFixed(1)} KB, ${areas.length} prefixes)`);
  console.log(`from ${offices.length} offices across ${byPin.size} pin codes`);
  if (unplaced.length) console.log(`outside every polygon (${unplaced.length}):\n  - ${unplaced.join("\n  - ")}`);
  console.log(`state disagreements resolved by polygon (${disagreed.length}):`);
  for (const d of disagreed.slice(0, 15)) console.log(`  - ${d}`);
  if (disagreed.length > 15) console.log(`  … and ${disagreed.length - 15} more`);
}

main();
