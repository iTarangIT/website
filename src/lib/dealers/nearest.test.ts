/**
 * Unit tests for the nearest-dealer core. Run with: npm run test:unit
 *
 * Pure functions only — no database, no network. Dealer fixtures are invented;
 * no real dealer name, phone or address is committed here.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { indiaMap } from "../../data/india-map-paths";
import { PINCODE_AREAS } from "../../data/pincode-areas";
import { gazetteerTowns, type KnownTown, type StateCentre } from "./locate";
import {
  RADIUS_KM,
  haversineKm,
  normalisePhone,
  rankNearest,
  resolveQuery,
  type DealerContact,
  type ResolvedQuery,
} from "./nearest";

const centres = new Map<string, StateCentre>(
  indiaMap.states.map((s) => [s.name, { name: s.name, lng: s.center[0], lat: s.center[1] }]),
);
const towns: KnownTown[] = gazetteerTowns();
const ask = (query: string) => resolveQuery(query, towns, centres);

const dealer = (over: Partial<DealerContact> = {}): DealerContact => ({
  company: "Test Batteries",
  phone: "9800000000",
  address: "12 Test Road",
  town: "Lucknow",
  state: "Uttar Pradesh",
  lat: 26.8467,
  lng: 80.9462,
  approximate: false,
  ...over,
});

describe("pincode area table", () => {
  it("every area names a state the map knows, with a plausible point", () => {
    const stateNames = new Set(indiaMap.states.map((s) => s.name));
    assert.ok(PINCODE_AREAS.length > 380, `only ${PINCODE_AREAS.length} prefixes`);
    const prefixes = new Set<string>();
    for (const area of PINCODE_AREAS) {
      assert.match(area.prefix, /^[1-9][0-9]{2}$/, `bad prefix ${area.prefix}`);
      assert.ok(!prefixes.has(area.prefix), `duplicate prefix ${area.prefix}`);
      prefixes.add(area.prefix);
      assert.ok(stateNames.has(area.state), `${area.prefix}: unknown state "${area.state}"`);
      // India's land extent, generously bounded.
      assert.ok(area.lat > 6 && area.lat < 37, `${area.prefix}: lat ${area.lat} is not in India`);
      assert.ok(area.lng > 68 && area.lng < 98, `${area.prefix}: lng ${area.lng} is not in India`);
    }
  });
});

describe("haversineKm", () => {
  it("matches known distances between Indian cities", () => {
    // Delhi -> Mumbai is about 1150 km; Delhi -> Agra about 180 km.
    assert.ok(Math.abs(haversineKm(28.6139, 77.209, 19.076, 72.8777) - 1150) < 30);
    assert.ok(Math.abs(haversineKm(28.6139, 77.209, 27.1767, 78.0081) - 180) < 15);
  });
  it("is zero for the same point and symmetric", () => {
    assert.equal(haversineKm(26.8, 80.9, 26.8, 80.9), 0);
    assert.equal(
      Math.round(haversineKm(26.8, 80.9, 25.4, 81.8)),
      Math.round(haversineKm(25.4, 81.8, 26.8, 80.9)),
    );
  });
});

describe("normalisePhone", () => {
  it("keeps a dialable number and drops the rest", () => {
    assert.equal(normalisePhone("98000 00000"), "9800000000");
    assert.equal(normalisePhone("+91 98000-00000"), "+919800000000");
    assert.equal(normalisePhone("  9800000000  "), "9800000000");
  });
  it("rejects anything that cannot be dialled", () => {
    assert.equal(normalisePhone(null), null);
    assert.equal(normalisePhone(""), null);
    assert.equal(normalisePhone("N/A"), null);
    assert.equal(normalisePhone("12345"), null);
    assert.equal(normalisePhone("00000000000000000"), null);
  });
});

describe("resolveQuery", () => {
  it("places a bare pin code", () => {
    const delhi = ask("110001");
    assert.ok(delhi, "110001 did not resolve");
    assert.equal(delhi.state, "Delhi");
    assert.ok(Math.abs(delhi.lat - 28.6) < 1 && Math.abs(delhi.lng - 77.2) < 1);

    // Kerala: no gazetteer town, so this must come from the pincode table.
    const kochi = ask("682001");
    assert.ok(kochi, "682001 did not resolve");
    assert.equal(kochi.state, "Kerala");
    assert.equal(kochi.precision, "area");
  });

  it("prefers a named town over the pin code's district centre", () => {
    const withTown = ask("MG Road, Prayagraj 211001");
    assert.ok(withTown);
    assert.equal(withTown.precision, "town");
    assert.equal(withTown.label, "Prayagraj");
  });

  it("understands a town alias and a misspelling", () => {
    assert.equal(ask("Allahabad")?.label, "Prayagraj");
    assert.equal(ask("JHANSHI 284001")?.state, "Uttar Pradesh");
  });

  it("reports state precision when only a state is named", () => {
    const bihar = ask("Bihar");
    assert.ok(bihar);
    assert.equal(bihar.state, "Bihar");
    assert.equal(bihar.precision, "state");
  });

  it("returns null for empty or unplaceable input", () => {
    assert.equal(ask(""), null);
    assert.equal(ask("   "), null);
    assert.equal(ask("qqqq zzzz"), null);
  });

  it("caps a very long query instead of parsing it all", () => {
    // Trailing text past the cap must not influence the answer.
    const padded = "Lucknow" + " x".repeat(400);
    assert.equal(ask(padded)?.label, "Lucknow");
  });
});

describe("rankNearest", () => {
  const from: ResolvedQuery = { label: "Lucknow", state: "Uttar Pradesh", lat: 26.8467, lng: 80.9462, precision: "town" };

  it("orders by distance and reports the closest three", () => {
    const result = rankNearest(from, [
      dealer({ company: "Far", lat: 28.6139, lng: 77.209, town: "Delhi", state: "Delhi" }),
      dealer({ company: "Near", lat: 26.86, lng: 80.95 }),
      dealer({ company: "Middle", lat: 25.4358, lng: 81.8463, town: "Prayagraj" }),
      dealer({ company: "Furthest", lat: 19.076, lng: 72.8777, town: "Mumbai", state: "Maharashtra" }),
    ]);
    assert.deepEqual(result.dealers.map((d) => d.company), ["Near", "Middle", "Far"]);
    assert.equal(result.dealers[0].distanceKm, 2);
    assert.equal(result.withinRadius, true);
    assert.equal(result.scope, "radius");
  });

  it("never puts a distance on a state-level dealer, and ranks it last", () => {
    const result = rankNearest(from, [
      dealer({ company: "Vague", approximate: true, lat: 27, lng: 80.5 }),
      dealer({ company: "Placed", lat: 25.4358, lng: 81.8463 }),
    ]);
    assert.deepEqual(result.dealers.map((d) => d.company), ["Placed", "Vague"]);
    assert.equal(result.dealers[1].distanceKm, null);
  });

  it("flags when nothing is within the radius but still answers", () => {
    const far = rankNearest(from, [dealer({ company: "Mumbai Co", lat: 19.076, lng: 72.8777, state: "Maharashtra" })]);
    assert.equal(far.withinRadius, false);
    assert.equal(far.dealers.length, 1, "a far dealer is still worth showing");
    assert.ok((far.dealers[0].distanceKm ?? 0) > RADIUS_KM);
  });

  it("treats the radius as inclusive at its boundary", () => {
    // Due north of Lucknow: ~1 degree of latitude is ~111 km.
    const inside = rankNearest(from, [dealer({ company: "A", lat: 26.8467 + 149 / 111, lng: 80.9462 })]);
    const outside = rankNearest(from, [dealer({ company: "A", lat: 26.8467 + 151 / 111, lng: 80.9462 })]);
    assert.equal(inside.withinRadius, true);
    assert.equal(outside.withinRadius, false);
  });

  it("answers a state query with that state's dealers rather than a radius", () => {
    const bihar: ResolvedQuery = { label: "Bihar", state: "Bihar", lat: 25.68, lng: 85.7, precision: "state" };
    const result = rankNearest(bihar, [
      dealer({ company: "UP Co", lat: 26.8467, lng: 80.9462 }),
      dealer({ company: "Bihar Co", town: "Muzaffarpur", state: "Bihar", lat: 26.12, lng: 85.39 }),
    ]);
    assert.equal(result.scope, "state");
    assert.equal(result.dealers[0].company, "Bihar Co");
  });

  it("breaks ties by name so repeated searches are stable", () => {
    const same = { lat: 26.8467, lng: 80.9462 };
    const result = rankNearest(from, [dealer({ company: "Zebra", ...same }), dealer({ company: "Alpha", ...same })]);
    assert.deepEqual(result.dealers.map((d) => d.company), ["Alpha", "Zebra"]);
  });

  it("returns nothing rather than inventing a dealer when there are none", () => {
    const result = rankNearest(from, []);
    assert.deepEqual(result.dealers, []);
    assert.equal(result.withinRadius, false);
  });
});
