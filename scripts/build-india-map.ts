/**
 * Generate src/data/india-map-paths.ts from scripts/geo/india-states.topo.json.
 *
 * Usage:
 *   npm run map:build
 *
 * Steps:
 *   1. Convert the TopoJSON `states` object to GeoJSON features.
 *   2. Fit a Mercator projection to a fixed canvas (same maths as the runtime,
 *      see src/lib/geo/mercator.ts) and turn every ring into an SVG path.
 *   3. Fail loudly if the data disagrees with src/data/cities.ts: not exactly
 *      36 units, a city whose `state` is not a feature name, or a city that
 *      does not project inside its declared state's polygon.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import type { Feature, FeatureCollection, MultiPolygon, Polygon, Position } from "geojson";
import { cities } from "../src/data/cities";
import { GAZETTEER } from "../src/lib/dealers/gazetteer";
import { fitMercator, mercator, type MercatorParams } from "../src/lib/geo/mercator";

const ROOT = process.cwd();
const SOURCE = resolve(ROOT, "scripts/geo/india-states.topo.json");
const OUTPUT = resolve(ROOT, "src/data/india-map-paths.ts");

const WIDTH = 600;
const HEIGHT = 680;
const PADDING = 16;
const EXPECTED_UNITS = 36;

type StateProps = { name: string };
type StateFeature = Feature<Polygon | MultiPolygon, StateProps>;

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

function ringsOf(geometry: Polygon | MultiPolygon): Position[][] {
  return geometry.type === "Polygon" ? geometry.coordinates : geometry.coordinates.flat();
}

function projectRing(ring: Position[], p: MercatorParams): [number, number][] {
  const out: [number, number][] = [];
  for (const [lng, lat] of ring) {
    const [x, y] = mercator(lng, lat, p);
    const px = Math.round(x * 10) / 10;
    const py = Math.round(y * 10) / 10;
    const last = out[out.length - 1];
    if (!last || last[0] !== px || last[1] !== py) out.push([px, py]);
  }
  // Drop a closing point that repeats the first one; `Z` closes the path.
  if (out.length > 1) {
    const [fx, fy] = out[0];
    const [lx, ly] = out[out.length - 1];
    if (fx === lx && fy === ly) out.pop();
  }
  return out;
}

/** Centroid of the largest ring, in [lng, lat]; a stable point to pin a state-level fallback on. */
function representativePoint(rings: Position[][]): [number, number] {
  let best: { area: number; cx: number; cy: number } | null = null;
  for (const ring of rings) {
    let twice = 0;
    let cx = 0;
    let cy = 0;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      const cross = xj * yi - xi * yj;
      twice += cross;
      cx += (xj + xi) * cross;
      cy += (yj + yi) * cross;
    }
    const area = Math.abs(twice) / 2;
    if (area === 0) continue;
    if (!best || area > best.area) best = { area, cx: cx / (3 * twice), cy: cy / (3 * twice) };
  }
  if (!best) throw new Error("representativePoint: no ring with area");
  return [Math.round(best.cx * 1e4) / 1e4, Math.round(best.cy * 1e4) / 1e4];
}

function ringToPath(ring: [number, number][]): string {
  const [head, ...rest] = ring;
  return `M${head[0]} ${head[1]}L${rest.map(([x, y]) => `${x} ${y}`).join(" ")}Z`;
}

/** Distance from (px, py) to the segment (x1, y1)–(x2, y2). */
function distToSegment(px: number, py: number, x1: number, y1: number, x2: number, y2: number): number {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;
  const t = lenSq === 0 ? 0 : Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / lenSq));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}

/** Distance from a point to the nearest edge of any ring. */
function clearance(x: number, y: number, rings: [number, number][][]): number {
  let best = Infinity;
  for (const ring of rings) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const d = distToSegment(x, y, ring[j][0], ring[j][1], ring[i][0], ring[i][1]);
      if (d < best) best = d;
    }
  }
  return best;
}

/**
 * Pole of inaccessibility: the interior point furthest from any edge, by grid
 * search then local refinement. This is the label anchor.
 *
 * A centroid will not do. `center` above is the centroid of the largest ring —
 * it is validated to be inside the polygon, but it is also exactly where a
 * state-level dealer pin is drawn (see locations.ts), and on concave or
 * multi-part units it can sit close to an edge. The pole stays clear of the
 * outline on every shape, and its clearance radius tells the runtime how much
 * room the name actually has.
 */
function labelAnchor(rings: [number, number][][]): { x: number; y: number; r: number } {
  const xs = rings.flat().map((p) => p[0]);
  const ys = rings.flat().map((p) => p[1]);
  let minX = Math.min(...xs);
  let maxX = Math.max(...xs);
  let minY = Math.min(...ys);
  let maxY = Math.max(...ys);

  let best = { x: (minX + maxX) / 2, y: (minY + maxY) / 2, r: -Infinity };
  // One coarse sweep, then tighten the window around the winner three times.
  for (let pass = 0, steps = 48; pass < 4; pass++, steps = 12) {
    const stepX = (maxX - minX) / steps;
    const stepY = (maxY - minY) / steps;
    for (let i = 0; i <= steps; i++) {
      for (let j = 0; j <= steps; j++) {
        const x = minX + i * stepX;
        const y = minY + j * stepY;
        if (!pointInRings(x, y, rings)) continue;
        const r = clearance(x, y, rings);
        if (r > best.r) best = { x, y, r };
      }
    }
    if (!isFinite(best.r)) break;
    const spanX = (maxX - minX) / steps;
    const spanY = (maxY - minY) / steps;
    minX = best.x - spanX;
    maxX = best.x + spanX;
    minY = best.y - spanY;
    maxY = best.y + spanY;
  }

  const round = (v: number) => Math.round(v * 10) / 10;
  return { x: round(best.x), y: round(best.y), r: round(Math.max(best.r, 0)) };
}

/** Even-odd ray cast: inside if the point crosses an odd number of ring edges. */
function pointInRings(x: number, y: number, rings: [number, number][][]): boolean {
  let inside = false;
  for (const ring of rings) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      const crosses = yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
      if (crosses) inside = !inside;
    }
  }
  return inside;
}

function main(): void {
  const topology = JSON.parse(readFileSync(SOURCE, "utf8")) as Topology<{ states: GeometryCollection<StateProps> }>;
  const collection = feature(topology, topology.objects.states) as FeatureCollection<Polygon | MultiPolygon, StateProps>;
  const features = collection.features as StateFeature[];

  if (features.length !== EXPECTED_UNITS) {
    throw new Error(`expected ${EXPECTED_UNITS} states/UTs in ${SOURCE}, found ${features.length}`);
  }

  const allPoints = features.flatMap((f) => ringsOf(f.geometry).flat()) as [number, number][];
  const projection = fitMercator(allPoints, WIDTH, HEIGHT, PADDING);

  const states = features
    .map((f) => {
      const rings = ringsOf(f.geometry)
        .map((ring) => projectRing(ring, projection))
        .filter((ring) => ring.length >= 3);
      return {
        id: slugify(f.properties.name),
        name: f.properties.name,
        center: representativePoint(ringsOf(f.geometry)),
        label: labelAnchor(rings),
        rings,
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  const ids = new Set<string>();
  for (const s of states) {
    if (ids.has(s.id)) throw new Error(`duplicate state id "${s.id}"`);
    ids.add(s.id);
    if (s.rings.length === 0) throw new Error(`state "${s.name}" has no drawable ring after rounding`);
  }

  // Cities must name a real unit and sit inside it on the projected canvas.
  const byName = new Map(states.map((s) => [s.name, s]));
  const problems: string[] = [];
  for (const city of cities) {
    const state = byName.get(city.state);
    if (!state) {
      problems.push(`${city.name}: state "${city.state}" is not a feature name`);
      continue;
    }
    const [x, y] = mercator(city.lng, city.lat, projection);
    if (!pointInRings(x, y, state.rings)) {
      problems.push(`${city.name}: projects to (${x.toFixed(1)}, ${y.toFixed(1)}), outside "${city.state}"`);
    }
  }
  // The dealer gazetteer must agree with the outline too, and every state's
  // representative point must sit inside its own polygon.
  for (const town of GAZETTEER) {
    const state = byName.get(town.state);
    if (!state) {
      problems.push(`gazetteer ${town.name}: state "${town.state}" is not a feature name`);
      continue;
    }
    const [x, y] = mercator(town.lng, town.lat, projection);
    if (!pointInRings(x, y, state.rings)) {
      problems.push(`gazetteer ${town.name}: (${town.lat}, ${town.lng}) is outside "${town.state}"`);
    }
  }
  for (const s of states) {
    const [x, y] = mercator(s.center[0], s.center[1], projection);
    if (!pointInRings(x, y, s.rings)) {
      problems.push(`state ${s.name}: representative point ${s.center.join(", ")} falls outside its polygon`);
    }
    // The label anchor is drawn, not just stored: it has to be inside the shape
    // and to have real room around it, or the name would sit over the outline.
    if (!pointInRings(s.label.x, s.label.y, s.rings)) {
      problems.push(`state ${s.name}: label anchor (${s.label.x}, ${s.label.y}) falls outside its polygon`);
    }
    if (!(s.label.r > 0)) {
      problems.push(`state ${s.name}: label anchor has no clearance`);
    }
  }
  if (problems.length) {
    throw new Error(`city/state mismatches:\n  - ${problems.join("\n  - ")}`);
  }

  const lines: string[] = [
    "// GENERATED by scripts/build-india-map.ts — do not edit by hand.",
    "// Source: scripts/geo/india-states.topo.json (rebuild: npm run map:build).",
    "// Outline: Survey of India state boundaries via DataMeet India community (CC BY 4.0);",
    "// see scripts/geo/README.md for the Ladakh split and the full attribution.",
    "",
    "export interface IndiaMapState {",
    "  /** URL-safe key, unique per state or union territory. */",
    "  id: string;",
    "  /** Display name; `CityData.state` values must match one of these exactly. */",
    "  name: string;",
    "  /** SVG path in the `width` x `height` canvas. */",
    "  d: string;",
    "  /** A point inside the state as [lng, lat]; where a state-level pin goes. */",
    "  center: readonly [number, number];",
    "  /**",
    "   * Where to write the state's name, as [x, y, clearance] in canvas units:",
    "   * the pole of inaccessibility and its distance to the nearest edge. The map",
    "   * shows the name once the zoom makes `clearance` wide enough to hold it.",
    "   */",
    "  label: readonly [number, number, number];",
    "}",
    "",
    "export interface IndiaMapData {",
    "  width: number;",
    "  height: number;",
    "  /** Mercator origin as [lng, lat]. */",
    "  center: readonly [number, number];",
    "  scale: number;",
    "  translate: readonly [number, number];",
    "  states: readonly IndiaMapState[];",
    "}",
    "",
    "export const indiaMap: IndiaMapData = {",
    `  width: ${WIDTH},`,
    `  height: ${HEIGHT},`,
    `  center: [${projection.center[0]}, ${projection.center[1]}],`,
    `  scale: ${projection.scale},`,
    `  translate: [${projection.translate[0]}, ${projection.translate[1]}],`,
    "  states: [",
    ...states.map(
      (s) =>
        `    { id: ${JSON.stringify(s.id)}, name: ${JSON.stringify(s.name)}, center: [${s.center[0]}, ${s.center[1]}], label: [${s.label.x}, ${s.label.y}, ${s.label.r}], d: ${JSON.stringify(s.rings.map(ringToPath).join(""))} },`,
    ),
    "  ],",
    "};",
    "",
  ];
  const output = lines.join("\n");
  writeFileSync(OUTPUT, output);

  console.log(`wrote ${OUTPUT} (${(Buffer.byteLength(output) / 1024).toFixed(1)} KB, ${states.length} units)`);
  console.log(`canvas ${WIDTH}x${HEIGHT}, scale ${projection.scale.toFixed(2)}`);

  // Label clearance drives when each name appears, so print it tightest-first:
  // the units at the top are the ones that only get named when zoomed well in.
  console.log("label clearance (canvas units), tightest first:");
  for (const s of [...states].sort((a, b) => a.label.r - b.label.r)) {
    console.log(`  ${s.name.padEnd(38)} r=${String(s.label.r).padStart(5)}  at (${s.label.x}, ${s.label.y})`);
  }

  for (const city of cities.filter((c) => c.status === "active")) {
    const [x, y] = mercator(city.lng, city.lat, projection);
    console.log(`  ${city.name.padEnd(12)} -> (${x.toFixed(1)}, ${y.toFixed(1)}) in ${city.state}`);
  }
}

main();
