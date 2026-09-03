/**
 * Shared reads of the CRM's dealer tables.
 *
 * Server-only. Both the map (locations.ts) and the nearest-dealer search
 * (nearest.ts) have to turn the same free-text addresses into points, and they
 * must agree: the search highlights a pin the map drew, so the two have to
 * resolve an address to the same town. Defining the resolution inputs once is
 * what makes that true by construction rather than by coincidence.
 */
import { unstable_cache } from "next/cache";
import { indiaMap } from "@/data/india-map-paths";
import { STATE_BY_CODE } from "./india-states";
import { gazetteerTowns, type KnownTown, type StateCentre } from "./locate";

/** Internal test / house accounts that exist in the dealers table. */
export const INTERNAL_DEALER_IDS = new Set(["ACC-ITARANG-DEALER", "ACC-ITARANG-HOUSE"]);

export const REVALIDATE_SECONDS = 60 * 60;

/** Address blobs come as `{ "address": "..." }`, a JSON string of that, or plain text. */
export function readAddress(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (trimmed.startsWith("{")) {
      try {
        return readAddress(JSON.parse(trimmed));
      } catch {
        return trimmed;
      }
    }
    return trimmed || null;
  }
  if (typeof value === "object" && "address" in value) {
    return readAddress((value as { address?: unknown }).address);
  }
  return null;
}

/** Canonical state name → a point inside it, for addresses that name no town. */
export function stateCentres(): Map<string, StateCentre> {
  return new Map(indiaMap.states.map((s) => [s.name, { name: s.name, lng: s.center[0], lat: s.center[1] }]));
}

async function fetchTowns(): Promise<KnownTown[]> {
  // Imported lazily so a missing DATABASE_URL fails this call, not the module graph.
  const { db } = await import("@/lib/db");
  const { crmCities, crmCityAliases } = await import("@/lib/db/dealer-schema");

  const [cityRows, aliasRows] = await Promise.all([
    db.select({ id: crmCities.id, name: crmCities.name, stateCode: crmCities.stateCode, lat: crmCities.lat, lng: crmCities.lng }).from(crmCities),
    db.select({ aliasLower: crmCityAliases.aliasLower, cityId: crmCityAliases.cityId }).from(crmCityAliases),
  ]);

  const aliasesByCity = new Map<string, string[]>();
  for (const a of aliasRows) {
    const list = aliasesByCity.get(a.cityId) ?? [];
    list.push(a.aliasLower);
    aliasesByCity.set(a.cityId, list);
  }

  const crmTowns: KnownTown[] = [];
  for (const c of cityRows) {
    const state = STATE_BY_CODE[c.stateCode?.toUpperCase() ?? ""];
    if (!state) continue;
    crmTowns.push({ name: c.name, state, lat: c.lat, lng: c.lng, aliases: aliasesByCity.get(c.id) ?? [] });
  }
  // Curated entries first; score() in locate.ts makes them win a tie.
  return [...gazetteerTowns(), ...crmTowns];
}

/** The CRM city master plus the curated gazetteer, cached for an hour. */
export const getTowns = unstable_cache(fetchTowns, ["dealer-towns-v1"], {
  revalidate: REVALIDATE_SECONDS,
  tags: ["dealer-locations"],
});
