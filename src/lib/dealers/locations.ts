/**
 * Dealer locations for the map on /for-dealers, read from the CRM database.
 *
 * Server-only. The page is force-dynamic, so nothing here runs during
 * `next build` (where DATABASE_URL is a placeholder); the first request on
 * the server fills the cache and it is refreshed hourly.
 */
import { unstable_cache } from "next/cache";
import { eq, inArray, sql } from "drizzle-orm";
import { GAZETTEER } from "./gazetteer";
import { INTERNAL_DEALER_IDS, REVALIDATE_SECONDS, getTowns, readAddress, stateCentres } from "./crm";
import { resolvePlace, type KnownTown, type PlaceInput, type StateCentre } from "./locate";
import type { DealerLocation } from "./types";

/** Applications that are real submissions but not approved yet. */
const PIPELINE_STATUSES = ["submitted", "correction_requested"];

const FAILURE_BACKOFF_MS = 60 * 1000;

// Re-exported: the map's own tests and callers have imported it from here since
// before the shared module existed.
export { readAddress };

interface Bucket extends DealerLocation {
  key: string;
}

function aggregate(
  live: PlaceInput[],
  pipeline: PlaceInput[],
  towns: readonly KnownTown[],
  centres: ReadonlyMap<string, StateCentre>,
): DealerLocation[] {
  const buckets = new Map<string, Bucket>();
  const add = (input: PlaceInput, field: "dealers" | "onboarding") => {
    const resolved = resolvePlace(input, towns, centres);
    if (!resolved) return;
    const key = `${resolved.state}|${resolved.name}`;
    const bucket =
      buckets.get(key) ??
      ({
        key,
        name: resolved.name,
        state: resolved.state,
        lat: resolved.lat,
        lng: resolved.lng,
        dealers: 0,
        onboarding: 0,
        status: "planned",
        approximate: resolved.precision === "state",
      } satisfies Bucket);
    bucket[field] += 1;
    if (bucket.dealers > 0) bucket.status = "active";
    buckets.set(key, bucket);
  };
  for (const input of live) add(input, "dealers");
  for (const input of pipeline) add(input, "onboarding");

  return Array.from(buckets.values())
    .sort((a, b) => {
      if (a.status !== b.status) return a.status === "active" ? -1 : 1;
      if (b.dealers !== a.dealers) return b.dealers - a.dealers;
      if (b.onboarding !== a.onboarding) return b.onboarding - a.onboarding;
      return a.name.localeCompare(b.name);
    })
    .map(({ key: _key, ...location }) => location);
}

async function fetchDealerLocations(): Promise<DealerLocation[]> {
  // Imported lazily so a missing DATABASE_URL fails this call, not the module graph.
  const { db } = await import("@/lib/db");
  const { dealers, dealerOnboardingApplications } = await import("@/lib/db/dealer-schema");

  const [dealerRows, pipelineRows, towns] = await Promise.all([
    db
      .select({
        dealerId: dealers.dealerId,
        registeredAddress: dealers.registeredAddress,
        businessAddress: dealerOnboardingApplications.businessAddress,
        city: dealerOnboardingApplications.city,
        state: dealerOnboardingApplications.state,
        pincode: dealerOnboardingApplications.pincode,
      })
      .from(dealers)
      .leftJoin(dealerOnboardingApplications, eq(sql`${dealerOnboardingApplications.id}::text`, dealers.applicationId))
      .where(eq(dealers.onboardingStatus, "active")),
    db
      .select({
        businessAddress: dealerOnboardingApplications.businessAddress,
        city: dealerOnboardingApplications.city,
        state: dealerOnboardingApplications.state,
        pincode: dealerOnboardingApplications.pincode,
      })
      .from(dealerOnboardingApplications)
      .where(inArray(dealerOnboardingApplications.onboardingStatus, PIPELINE_STATUSES)),
    getTowns(),
  ]);

  const live: PlaceInput[] = dealerRows
    .filter((d) => !INTERNAL_DEALER_IDS.has(d.dealerId ?? ""))
    .map((d) => ({
      address: readAddress(d.registeredAddress) ?? readAddress(d.businessAddress),
      city: d.city,
      state: d.state,
      pincode: d.pincode,
    }))
    .filter((d) => d.address || d.city || d.state || d.pincode);

  const pipeline: PlaceInput[] = pipelineRows
    .map((a) => ({ address: readAddress(a.businessAddress), city: a.city, state: a.state, pincode: a.pincode }))
    .filter((a) => a.address || a.city || a.state || a.pincode);

  return aggregate(live, pipeline, towns, stateCentres());
}

const getCachedDealerLocations = unstable_cache(fetchDealerLocations, ["dealer-locations-v2"], {
  revalidate: REVALIDATE_SECONDS,
  tags: ["dealer-locations"],
});

let lastFailureAt = 0;

/**
 * Dealer pins for the map, or null when the database cannot be reached. The
 * page hides the section on null rather than showing stale or invented data.
 */
export async function getDealerLocations(): Promise<DealerLocation[] | null> {
  if (Date.now() - lastFailureAt < FAILURE_BACKOFF_MS) return null;
  try {
    return await getCachedDealerLocations();
  } catch (error) {
    lastFailureAt = Date.now();
    console.error("[dealer-map] could not load dealer locations:", error instanceof Error ? error.message : error);
    return null;
  }
}

/** Exported for tests. */
export const __internal = { aggregate, GAZETTEER_SIZE: GAZETTEER.length };
