import { NextResponse } from "next/server";
import { getClientIp } from "@/lib/calc-gate";
import { MAX_QUERY_LENGTH, RADIUS_KM, findNearestDealers } from "@/lib/dealers/nearest";

export const dynamic = "force-dynamic";
export const runtime = "nodejs"; // postgres-js cannot run on the edge runtime

// Nearest dealers for a pin code, town or address typed on /for-dealers.
// Public and unauthenticated, and it returns published contact details, so it
// is deliberately not a directory: three results per query, no "list all" mode,
// and a per-IP ceiling below. See src/lib/db/dealer-schema.ts for what is
// published and what stays out.

const WINDOW_MS = 60 * 60 * 1000;
const IP_LIMIT = 60; // searches per IP per hour

// In-memory and therefore per-instance, the same trade-off calc-gate.ts makes:
// it will not stop a distributed scrape, but it stops a single client walking
// the pin-code table from one machine.
const ipHistory = new Map<string, number[]>();

function allowed(ip: string): boolean {
  const now = Date.now();
  const recent = (ipHistory.get(ip) ?? []).filter((t) => now - t < WINDOW_MS);
  ipHistory.set(ip, recent);
  if (recent.length >= IP_LIMIT) return false;
  recent.push(now);
  return true;
}

export async function GET(req: Request) {
  const query = (new URL(req.url).searchParams.get("q") ?? "").trim().slice(0, MAX_QUERY_LENGTH);
  if (!query) {
    return NextResponse.json({ error: "Enter a pin code, town or address." }, { status: 400 });
  }
  if (!allowed(getClientIp(req))) {
    return NextResponse.json({ error: "Too many searches. Please try again later." }, { status: 429 });
  }

  const result = await findNearestDealers(query);
  if (!result) {
    return NextResponse.json({ error: "Dealer search is unavailable right now." }, { status: 503 });
  }

  // A query we could not place is a 200 with an empty result, not an error:
  // the caller needs to tell the visitor their input was not recognised, which
  // is a different message from "no dealers near you".
  return NextResponse.json(
    { ...result, radiusKm: RADIUS_KM },
    { headers: { "Cache-Control": "private, no-store" } },
  );
}
