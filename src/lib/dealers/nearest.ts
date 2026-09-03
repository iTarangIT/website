/**
 * "Find your nearest dealer" for /for-dealers.
 *
 * The ranking core is pure and synchronous so it can be unit-tested with
 * fixtures; the database work is at the bottom, behind an hourly cache.
 *
 * A visitor's typed text goes through the SAME resolver as the dealers' own
 * addresses (locate.ts). That is deliberate: a result highlights a pin the map
 * already drew, which only holds if both sides resolve a place identically.
 */
import { unstable_cache } from "next/cache";
import { eq, sql } from "drizzle-orm";
import { PINCODE_AREAS, type PincodeArea } from "@/data/pincode-areas";
import { INTERNAL_DEALER_IDS, REVALIDATE_SECONDS, getTowns, readAddress, stateCentres } from "./crm";
import { extractPincode, resolvePlace, type KnownTown, type StateCentre } from "./locate";

/** How far away we still call a dealer "near you". */
export const RADIUS_KM = 150;
export const RESULT_LIMIT = 3;
/** Longest query we will parse: findTownInText is O(towns x text length). */
export const MAX_QUERY_LENGTH = 120;

export interface DealerContact {
  company: string;
  /** Digits as stored, ready for a tel: link; null when the CRM has none. */
  phone: string | null;
  address: string;
  town: string;
  state: string;
  lat: number;
  lng: number;
  /** True when the address only placed at state level: no honest distance. */
  approximate: boolean;
}

export interface RankedDealer extends DealerContact {
  /** Straight-line km. Null for an approximate dealer — see rankNearest. */
  distanceKm: number | null;
}

export interface ResolvedQuery {
  /** What we understood, echoed back: "Lucknow", "Bareilly", "Bihar". */
  label: string;
  state: string;
  lat: number;
  lng: number;
  /** "area" is a pin-code district centre rather than a named town. */
  precision: "town" | "area" | "state";
}

export interface NearestResult {
  resolved: ResolvedQuery | null;
  dealers: RankedDealer[];
  /** Is the closest placed dealer within RADIUS_KM? Ignore when scope is "state". */
  withinRadius: boolean;
  /**
   * "radius" — we know a point, so distances mean something.
   * "state"  — the query named only a state; a radius around its centroid would
   *            be nonsense, so the answer is "dealers in <state>" instead.
   */
  scope: "radius" | "state";
}

const PINCODE_AREA_BY_PREFIX = new Map<string, PincodeArea>(PINCODE_AREAS.map((a) => [a.prefix, a]));

/** Great-circle distance in km. */
export function haversineKm(aLat: number, aLng: number, bLat: number, bLng: number): number {
  const R = 6371;
  const rad = Math.PI / 180;
  const dLat = (bLat - aLat) * rad;
  const dLng = (bLng - aLng) * rad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * rad) * Math.cos(bLat * rad) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** Keep digits and a leading +, so the value is safe in a tel: link. */
export function normalisePhone(value: string | null | undefined): string | null {
  if (!value) return null;
  const cleaned = value.replace(/[^\d+]/g, "").replace(/(?!^)\+/g, "");
  const digits = cleaned.replace(/\D/g, "");
  // Indian mobiles are 10 digits; allow a country code, reject anything shorter.
  if (digits.length < 10 || digits.length > 13) return null;
  return cleaned;
}

/**
 * Turn what the visitor typed into a point.
 *
 * The pin-code table is a fallback, not the first choice: a named town from the
 * curated gazetteer is more precise than a sorting district's centre. It earns
 * its keep when the resolver could otherwise only reach the state.
 */
export function resolveQuery(
  query: string,
  towns: readonly KnownTown[],
  centres: ReadonlyMap<string, StateCentre>,
  areas: ReadonlyMap<string, PincodeArea> = PINCODE_AREA_BY_PREFIX,
): ResolvedQuery | null {
  const text = query.trim().slice(0, MAX_QUERY_LENGTH);
  if (!text) return null;

  const place = resolvePlace({ address: text }, towns, centres);
  const pincode = extractPincode(text);

  if (place && place.precision === "town") {
    return { label: place.name, state: place.state, lat: place.lat, lng: place.lng, precision: "town" };
  }

  if (pincode) {
    const area = areas.get(pincode.slice(0, 3));
    if (area) {
      return { label: area.name, state: area.state, lat: area.lat, lng: area.lng, precision: "area" };
    }
  }

  if (place) {
    return { label: place.name, state: place.state, lat: place.lat, lng: place.lng, precision: "state" };
  }
  return null;
}

/**
 * Nearest dealers first.
 *
 * An approximate dealer — one whose address only placed at state level — never
 * carries a distance. Its coordinates are the state's centroid, so "38 km away"
 * would be a number we cannot stand behind. Those rank behind every placed
 * dealer and are shown without a figure.
 */
export function rankNearest(
  query: ResolvedQuery,
  dealers: readonly DealerContact[],
  limit: number = RESULT_LIMIT,
  radiusKm: number = RADIUS_KM,
): { dealers: RankedDealer[]; withinRadius: boolean; scope: "radius" | "state" } {
  const byName = (a: DealerContact, b: DealerContact) => a.company.localeCompare(b.company);

  const placed: RankedDealer[] = dealers
    .filter((d) => !d.approximate)
    .map((d) => ({ ...d, distanceKm: Math.round(haversineKm(query.lat, query.lng, d.lat, d.lng)) }))
    .sort((a, b) => (a.distanceKm ?? 0) - (b.distanceKm ?? 0) || byName(a, b));

  const approximate: RankedDealer[] = dealers
    .filter((d) => d.approximate)
    .map((d) => ({ ...d, distanceKm: null }))
    .sort(byName);

  // A query naming only a state has no meaningful centre to measure from, so
  // answer "dealers in that state" and put that state's dealers first.
  const scope: "radius" | "state" = query.precision === "state" ? "state" : "radius";
  const here = (d: DealerContact) => d.state === query.state;
  const ordered =
    scope === "state"
      ? [
          ...placed.filter(here),
          ...approximate.filter(here),
          ...placed.filter((d) => !here(d)),
          ...approximate.filter((d) => !here(d)),
        ]
      : [...placed, ...approximate];

  const nearest = placed[0]?.distanceKm;
  return { dealers: ordered.slice(0, limit), withinRadius: nearest != null && nearest <= radiusKm, scope };
}

// ── Database ────────────────────────────────────────────────────────────────

async function fetchActiveDealerContacts(): Promise<DealerContact[]> {
  // Imported lazily so a missing DATABASE_URL fails this call, not the module graph.
  const { db } = await import("@/lib/db");
  const { dealers, dealerOnboardingApplications } = await import("@/lib/db/dealer-schema");

  const [rows, towns] = await Promise.all([
    db
      .select({
        dealerId: dealers.dealerId,
        company: dealers.companyName,
        applicationCompany: dealerOnboardingApplications.companyName,
        ownerPhone: dealers.ownerPhone,
        contactPhone: dealerOnboardingApplications.contactPhone,
        registeredAddress: dealers.registeredAddress,
        businessAddress: dealerOnboardingApplications.businessAddress,
        city: dealerOnboardingApplications.city,
        state: dealerOnboardingApplications.state,
        pincode: dealerOnboardingApplications.pincode,
      })
      .from(dealers)
      .leftJoin(dealerOnboardingApplications, eq(sql`${dealerOnboardingApplications.id}::text`, dealers.applicationId))
      .where(eq(dealers.onboardingStatus, "active")),
    getTowns(),
  ]);

  const centres = stateCentres();
  const contacts: DealerContact[] = [];

  for (const row of rows) {
    if (INTERNAL_DEALER_IDS.has(row.dealerId ?? "")) continue;
    const address = readAddress(row.registeredAddress) ?? readAddress(row.businessAddress);
    if (!address && !row.city && !row.state && !row.pincode) continue;

    const place = resolvePlace({ address, city: row.city, state: row.state, pincode: row.pincode }, towns, centres);
    if (!place) continue;

    contacts.push({
      company: (row.company ?? row.applicationCompany ?? "").trim() || "iTarang dealer partner",
      // The designated business contact first; the owner's own number only
      // where there is no other way to reach the dealership.
      phone: normalisePhone(row.contactPhone) ?? normalisePhone(row.ownerPhone),
      address: address ?? [row.city, row.state, row.pincode].filter(Boolean).join(", "),
      town: place.name,
      state: place.state,
      lat: place.lat,
      lng: place.lng,
      approximate: place.precision === "state",
    });
  }

  return contacts;
}

/**
 * Active dealers with their published contact details, cached for an hour.
 *
 * Cached with no arguments on purpose: unstable_cache keys on the wrapped
 * function's arguments, so caching a per-query function would mint an entry for
 * every string anyone ever typed.
 */
const getActiveDealerContacts = unstable_cache(fetchActiveDealerContacts, ["dealer-contacts-v1"], {
  revalidate: REVALIDATE_SECONDS,
  tags: ["dealer-locations"],
});

/** Nearest dealers for a typed query, or null when the database is unreachable. */
export async function findNearestDealers(query: string): Promise<NearestResult | null> {
  try {
    const [contacts, towns] = await Promise.all([getActiveDealerContacts(), getTowns()]);
    const resolved = resolveQuery(query, towns, stateCentres());
    if (!resolved) return { resolved: null, dealers: [], withinRadius: false, scope: "radius" };
    return { resolved, ...rankNearest(resolved, contacts) };
  } catch (error) {
    console.error("[dealer-search] could not search dealers:", error instanceof Error ? error.message : error);
    return null;
  }
}
