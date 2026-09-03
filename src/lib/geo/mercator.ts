/**
 * Plain spherical Mercator shared by the map generator
 * (scripts/build-india-map.ts) and the runtime pin projection
 * (src/lib/geo/india-projection.ts). Both sides read the same constants from
 * the generated module, so state outlines and city pins cannot drift apart.
 */

export interface MercatorParams {
  /** Projection origin as [lng, lat] in degrees. */
  center: readonly [number, number];
  /** Canvas units per radian of longitude. */
  scale: number;
  /** Canvas [x, y] that `center` lands on. */
  translate: readonly [number, number];
}

const RAD = Math.PI / 180;

function mercY(latDeg: number): number {
  return Math.log(Math.tan(Math.PI / 4 + (latDeg * RAD) / 2));
}

/** Project a [lng, lat] pair to canvas [x, y]. */
export function mercator(lng: number, lat: number, p: MercatorParams): [number, number] {
  const x = p.translate[0] + p.scale * (lng - p.center[0]) * RAD;
  const y = p.translate[1] - p.scale * (mercY(lat) - mercY(p.center[1]));
  return [x, y];
}

/**
 * Fit a projection so every point in `points` lands inside a `width` x `height`
 * canvas with `padding` on each side, with the whole extent centred.
 */
export function fitMercator(
  points: Iterable<readonly [number, number]>,
  width: number,
  height: number,
  padding: number,
): MercatorParams {
  let minLng = Infinity;
  let maxLng = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;
  for (const [lng, lat] of points) {
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }
  if (!Number.isFinite(minLng)) throw new Error("fitMercator: no points to fit");

  const center: [number, number] = [(minLng + maxLng) / 2, (minLat + maxLat) / 2];
  const unit: MercatorParams = { center, scale: 1, translate: [0, 0] };
  const [x0, y0] = mercator(minLng, maxLat, unit); // top-left in unit space
  const [x1, y1] = mercator(maxLng, minLat, unit); // bottom-right in unit space

  const scale = Math.min((width - 2 * padding) / (x1 - x0), (height - 2 * padding) / (y1 - y0));
  const translate: [number, number] = [
    width / 2 - (scale * (x0 + x1)) / 2,
    height / 2 - (scale * (y0 + y1)) / 2,
  ];
  return { center, scale, translate };
}
