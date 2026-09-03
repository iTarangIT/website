/**
 * Unit tests for the address resolver. Run with: npm run test:unit
 *
 * Fixtures mirror the address formats the CRM actually stores (comma lists,
 * GST-portal labels, misspelt towns, bare state codes) with made-up street
 * details; no real dealer address is committed here.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { indiaMap } from "../../data/india-map-paths";
import { GAZETTEER } from "./gazetteer";
import { ALL_STATES, STATE_ALIASES, canonicalState, stateFromPincode } from "./india-states";
import { extractPincode, gazetteerTowns, resolvePlace, type KnownTown, type StateCentre } from "./locate";
import { __internal, readAddress } from "./locations";

const stateNames = new Set(indiaMap.states.map((s) => s.name));
const centres = new Map<string, StateCentre>(
  indiaMap.states.map((s) => [s.name, { name: s.name, lng: s.center[0], lat: s.center[1] }]),
);
const crmTowns: KnownTown[] = [
  { name: "Udham Singh Nagar", state: "Uttarakhand", lat: null, lng: null },
  { name: "Gola", state: "Uttar Pradesh", lat: 28.08, lng: 80.47 },
  { name: "Sitamarhi", state: "Bihar", lat: 26.59, lng: 85.49 },
  { name: "Ad", state: "Uttar Pradesh", lat: 26.4, lng: 80.39 },
];
const towns = [...gazetteerTowns(), ...crmTowns];
const resolve = (address: string, extra: Partial<Parameters<typeof resolvePlace>[0]> = {}) =>
  resolvePlace({ address, ...extra }, towns, centres);

describe("reference data is consistent with the generated map", () => {
  it("every canonical state name exists in india-map-paths", () => {
    for (const s of ALL_STATES) assert.ok(stateNames.has(s), `unknown state "${s}"`);
    for (const s of Object.values(STATE_ALIASES)) assert.ok(stateNames.has(s), `alias points at unknown state "${s}"`);
    for (const g of GAZETTEER) assert.ok(stateNames.has(g.state), `${g.name}: unknown state "${g.state}"`);
  });
  it("gazetteer names are unique within a state and pincode prefixes are unique overall", () => {
    const names = new Set<string>();
    const pins = new Map<string, string>();
    for (const g of GAZETTEER) {
      const key = `${g.state}|${g.name.toLowerCase()}`;
      assert.ok(!names.has(key), `duplicate town ${key}`);
      names.add(key);
      for (const p of g.pins ?? []) {
        assert.ok(!pins.has(p), `pincode prefix ${p} claimed by ${pins.get(p)} and ${g.name}`);
        pins.set(p, g.name);
      }
    }
    assert.equal(__internal.GAZETTEER_SIZE, GAZETTEER.length);
  });
});

describe("helpers", () => {
  it("canonicalState accepts names, codes and common misspellings", () => {
    assert.equal(canonicalState("Uttar Pradesh"), "Uttar Pradesh");
    assert.equal(canonicalState("up"), "Uttar Pradesh");
    assert.equal(canonicalState("Orissa"), "Odisha");
    assert.equal(canonicalState("haryana"), "Haryana");
    assert.equal(canonicalState("Mars"), null);
  });
  it("extractPincode takes the last six-digit group and ignores longer numbers", () => {
    assert.equal(extractPincode("Plot 454/130, phone 9876543210, Jodhpur 342008"), "342008");
    assert.equal(extractPincode("no pin here"), null);
  });
  it("stateFromPincode uses three-digit overrides before two-digit ranges", () => {
    assert.equal(stateFromPincode("248001"), "Uttarakhand");
    assert.equal(stateFromPincode("226010"), "Uttar Pradesh");
    assert.equal(stateFromPincode("834001"), "Jharkhand");
    assert.equal(stateFromPincode("12345"), null);
  });
  it("readAddress unwraps the three shapes the CRM stores", () => {
    assert.equal(readAddress({ address: " 12 Main Road, Jamui, Bihar, 811307 " }), "12 Main Road, Jamui, Bihar, 811307");
    assert.equal(readAddress('{"address":"Shop 4, Suri, Birbhum, West Bengal, 731101"}'), "Shop 4, Suri, Birbhum, West Bengal, 731101");
    assert.equal(readAddress("Rampur Road Bazpur, Uttarakhand, 262401"), "Rampur Road Bazpur, Uttarakhand, 262401");
    assert.equal(readAddress({}), null);
    assert.equal(readAddress(null), null);
  });
});

describe("resolvePlace", () => {
  it("comma-separated address with town, state and pincode", () => {
    const r = resolve("AZAD NAGAR, MAIN ROAD, Jamui, Bihar, 811307");
    assert.deepEqual([r?.name, r?.state, r?.precision], ["Jamui", "Bihar", "town"]);
  });
  it("GST-portal labels pick the City/Town/Village value", () => {
    const r = resolve(
      "Building No./Flat No.: A-27, Name Of Premises/Building: Near Tower, Road/Street: Pratap Nagar Road, Locality/Sub Locality: Circle, City/Town/Village: Jodhpur, District: Jodhpur, State: Rajasthan, PIN Code: 342008",
    );
    assert.deepEqual([r?.name, r?.state, r?.precision], ["Jodhpur", "Rajasthan", "town"]);
  });
  it("misspelt town falls back to the pincode prefix", () => {
    const r = resolve("NEAR NURSING HOME, SHIV NAGAR JHANSHI, GHALIOR ROAD JHANSHI UTTAR PRADESH - 284001");
    assert.deepEqual([r?.name, r?.precision], ["Jhansi", "town"]);
    const m = resolve("495/5 ROORKEE ROAD MUZZAFARNAGAR UTTAR PRADESH-251001");
    assert.equal(m?.name, "Muzaffarnagar");
  });
  it("bare two-letter state code before the pincode", () => {
    const r = resolve("ward no. 4 bisalpur mohalla habibulla khan railway crossing bisalpur pilibhit up - 262201");
    assert.deepEqual([r?.name, r?.state], ["Pilibhit", "Uttar Pradesh"]);
  });
  it("prefers a curated town with coordinates over a CRM district without them", () => {
    const r = resolve("859a/69 ALI GANJ ROAD TANDA KASHIPUR UDHAM SINGH NAGAR UTTARAKHAND -244713");
    assert.deepEqual([r?.name, r?.precision], ["Kashipur", "town"]);
  });
  it("state filter stops a same-named town in another state from matching", () => {
    // "Ujjain" is a locality name here; the state is Uttarakhand so Ujjain (MP) must not win.
    const r = resolve("NEAR SHIV MANDIR TANDA UJJAIN BAZPUR UTTARAKHAND 262401");
    assert.deepEqual([r?.name, r?.state], ["Bazpur", "Uttarakhand"]);
  });
  it("prefers the town over the district that follows it", () => {
    const r = resolve("MAIN BUS STAND SHERANI ABAD, DIDWANA, Nagaur, Rajasthan, 341302");
    assert.deepEqual([r?.name, r?.state], ["Didwana", "Rajasthan"]);
    const b = resolve("kanstiya street pipliya bazar, beawar, Ajmer, Rajasthan 305901");
    assert.equal(b?.name, "Beawar");
  });
  it("a town used as a street name does not count", () => {
    const r = resolve("Shop 3, Agra Road, Aligarh, Uttar Pradesh 202001");
    assert.equal(r?.name, "Aligarh");
    const g = resolve("GOLA ROAD DANAPUR, PATNA, BIHAR - 801503");
    assert.deepEqual([g?.name, g?.state], ["Patna", "Bihar"]);
  });
  it("very short CRM names never match", () => {
    const r = resolve("Shop 2, Ad Road, Kanpur, Uttar Pradesh 208001");
    assert.equal(r?.name, "Kanpur");
  });
  it("explicit city/state columns win over the address text", () => {
    const r = resolve("some old text mentioning Delhi", { city: "Gaya", state: "Bihar" });
    assert.deepEqual([r?.name, r?.state], ["Gaya", "Bihar"]);
  });
  it("unknown town in a known state lands on the state centre, flagged approximate", () => {
    const r = resolve("Village Kotwali, Tehsil Nowhere, Bihar, 000000");
    assert.equal(r?.state, "Bihar");
    assert.equal(r?.name, "Bihar");
    assert.equal(r?.precision, "state");
    const c = centres.get("Bihar");
    assert.deepEqual([r?.lat, r?.lng], [c?.lat, c?.lng]);
  });
  it("GST city label with no coordinates keeps the town name but is approximate", () => {
    const r = resolve("City/Town/Village: Rampur Hat, District: Somewhere, State: West Bengal, PIN Code: 000000");
    assert.deepEqual([r?.name, r?.state, r?.precision], ["Rampur Hat", "West Bengal", "state"]);
  });
  it("returns null when nothing can be placed", () => {
    assert.equal(resolve("no usable location at all"), null);
    assert.equal(resolvePlace({ address: null }, towns, centres), null);
  });
});

describe("aggregate", () => {
  it("groups by town, sums counts and orders live places first", () => {
    const rows = __internal.aggregate(
      [
        { address: "Naini, Prayagraj, Uttar Pradesh, 211008" },
        { address: "Civil Lines, Prayagraj, Uttar Pradesh, 211001" },
        { address: "Station Road, Howrah, West Bengal, 711302" },
      ],
      [
        { address: "Bus Stand, Gaya, Bihar, 823001" },
        { address: "Katra, Prayagraj, Uttar Pradesh, 211002" },
      ],
      towns,
      centres,
    );
    assert.deepEqual(
      rows.map((r) => [r.name, r.status, r.dealers, r.onboarding]),
      [
        ["Prayagraj", "active", 2, 1],
        ["Howrah", "active", 1, 0],
        ["Gaya", "planned", 0, 1],
      ],
    );
  });
});
