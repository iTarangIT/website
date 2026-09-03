/**
 * Polygon helpers shared by the map generator, the pincode generator and tests.
 *
 * `src/data/india-map-paths.ts` ships each state as an SVG path string rather
 * than as coordinate arrays, so anything that needs to ask "is this point
 * inside that state?" has to read the rings back out of the path first.
 */

export type Ring = [number, number][];

/**
 * Rings from a generated state path. The generator writes a fixed shape,
 * `M{x} {y}L{x} {y} {x} {y}…Z` once per ring, so this parses exactly that and
 * nothing else — it is not a general SVG path parser.
 */
export function parsePathRings(d: string): Ring[] {
  const rings: Ring[] = [];
  for (const part of d.split("M").slice(1)) {
    const numbers = part.replace(/Z$/, "").split(/[L\s,]+/).filter(Boolean).map(Number);
    const ring: Ring = [];
    for (let i = 0; i + 1 < numbers.length; i += 2) {
      const x = numbers[i];
      const y = numbers[i + 1];
      if (Number.isFinite(x) && Number.isFinite(y)) ring.push([x, y]);
    }
    if (ring.length >= 3) rings.push(ring);
  }
  return rings;
}

/** Even-odd ray cast: inside if the point crosses an odd number of ring edges. */
export function pointInRings(x: number, y: number, rings: readonly Ring[]): boolean {
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
