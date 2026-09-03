/**
 * Turn a dealer's free-text business address into a place on the map.
 *
 * Pure and synchronous so it can be unit-tested with fixtures; the database
 * work happens in locations.ts. Resolution order:
 *
 *   1. state   explicit field → state name in the text (last occurrence wins)
 *              → two-letter code right before the pincode → pincode prefix
 *   2. town    GST-style "City/Town/Village:" label → any known town named in
 *              the text (curated gazetteer first, then the CRM city master)
 *              → gazetteer town owning the pincode prefix
 *   3. fallback the state's centre, flagged approximate
 */
import { GAZETTEER } from "./gazetteer";
import { STATE_ALIASES, STATE_BY_CODE, canonicalState, stateFromPincode } from "./india-states";

export interface PlaceInput {
  address: string | null | undefined;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
}

/** A town the resolver may match against, from the gazetteer or the CRM. */
export interface KnownTown {
  name: string;
  /** Canonical state name. */
  state: string;
  lat: number | null;
  lng: number | null;
  aliases?: readonly string[];
  /** Curated entries outrank CRM rows when both match. */
  curated?: boolean;
}

export interface StateCentre {
  name: string;
  lat: number;
  lng: number;
}

export interface ResolvedPlace {
  name: string;
  state: string;
  lat: number;
  lng: number;
  precision: "town" | "state";
}

export function normalise(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

/** Last six-digit group in the text; Indian addresses end with the pincode. */
export function extractPincode(text: string): string | null {
  const all = text.match(/(?<![0-9])[1-9][0-9]{5}(?![0-9])/g);
  return all ? all[all.length - 1] : null;
}

function titleCase(s: string): string {
  return s.replace(/\b[a-z]/g, (c) => c.toUpperCase());
}

/** Index just past the last whole-word occurrence of `term`, or -1. */
function lastEnd(text: string, term: string): number {
  if (!term) return -1;
  let end = -1;
  let from = 0;
  for (;;) {
    const i = text.indexOf(term, from);
    if (i === -1) return end;
    const before = i === 0 || text[i - 1] === " ";
    const after = i + term.length === text.length || text[i + term.length] === " ";
    if (before && after) end = i + term.length;
    from = i + 1;
  }
}

/** "agra road", "jaipur highway": a town name used as a street name, not a location. */
const STREET_WORDS = ["road", "rd", "marg", "highway", "bypass", "chowk", "gate"];

/**
 * Index of the first whole-word occurrence of `term` that is not part of a
 * street name, or -1. Addresses run "shop, locality, town, district, state",
 * so the first real town named is the dealer's own town rather than its
 * district headquarters.
 */
function firstTownStart(text: string, term: string): number {
  let from = 0;
  for (;;) {
    const i = text.indexOf(term, from);
    if (i === -1) return -1;
    const before = i === 0 || text[i - 1] === " ";
    const end = i + term.length;
    const after = end === text.length || text[end] === " ";
    if (before && after) {
      const nextWord = text.slice(end + 1).split(" ", 1)[0];
      if (!STREET_WORDS.includes(nextWord)) return i;
    }
    from = i + 1;
  }
}

function gstLabel(text: string, re: RegExp): string | null {
  const m = text.match(re);
  return m?.[1]?.trim() || null;
}

export function gazetteerTowns(): KnownTown[] {
  return GAZETTEER.map((g) => ({ ...g, curated: true }));
}

function findState(text: string, explicit: string | null | undefined, pincode: string | null): string | null {
  const fromExplicit = canonicalState(explicit);
  if (fromExplicit) return fromExplicit;

  const gst = gstLabel(text, /\bstate ([a-z ]+?)(?= pin code| pincode| pin |$)/);
  const fromGst = canonicalState(gst);
  if (fromGst) return fromGst;

  let best: { state: string; end: number; len: number } | null = null;
  for (const [alias, state] of Object.entries(STATE_ALIASES)) {
    const end = lastEnd(text, alias);
    if (end === -1) continue;
    if (!best || end > best.end || (end === best.end && alias.length > best.len)) {
      best = { state, end, len: alias.length };
    }
  }
  if (best) return best.state;

  // "… pilibhit up 262201" — a bare code only counts at the very end.
  const code = text.match(/\b([a-z]{2})(?: [1-9][0-9]{5})?$/)?.[1];
  if (code && STATE_BY_CODE[code.toUpperCase()]) return STATE_BY_CODE[code.toUpperCase()];

  return stateFromPincode(pincode);
}

function score(t: KnownTown): number {
  return (t.lat != null && t.lng != null ? 2 : 0) + (t.curated ? 1 : 0);
}

function findTownInText(text: string, state: string | null, towns: readonly KnownTown[]): KnownTown | null {
  let best: { town: KnownTown; start: number; len: number; score: number } | null = null;
  for (const town of towns) {
    if (state && town.state !== state) continue;
    for (const raw of [town.name, ...(town.aliases ?? [])]) {
      const term = normalise(raw);
      if (term.length < 4) continue; // "Ad", "Gola" style rows false-match too easily
      const start = firstTownStart(text, term);
      if (start === -1) continue;
      const s = score(town);
      const better =
        !best ||
        s > best.score ||
        (s === best.score && (start < best.start || (start === best.start && term.length > best.len)));
      if (better) best = { town, start, len: term.length, score: s };
    }
  }
  return best?.town ?? null;
}

function findTownByLabel(label: string | null, state: string | null, towns: readonly KnownTown[]): KnownTown | null {
  if (!label) return null;
  const key = normalise(label);
  let best: KnownTown | null = null;
  for (const town of towns) {
    if (state && town.state !== state) continue;
    const names = [town.name, ...(town.aliases ?? [])].map(normalise);
    if (names.includes(key) && (!best || score(town) > score(best))) best = town;
  }
  return best;
}

function place(town: KnownTown, state: string | null, centres: ReadonlyMap<string, StateCentre>): ResolvedPlace | null {
  const st = town.state || state;
  if (!st) return null;
  if (town.lat != null && town.lng != null) {
    return { name: town.name, state: st, lat: town.lat, lng: town.lng, precision: "town" };
  }
  const centre = centres.get(st);
  return centre ? { name: town.name, state: st, lat: centre.lat, lng: centre.lng, precision: "state" } : null;
}

/**
 * @param input   address fields as stored by the CRM
 * @param towns   gazetteer entries plus CRM city rows (see gazetteerTowns())
 * @param centres canonical state name → representative point, for the fallback
 */
export function resolvePlace(
  input: PlaceInput,
  towns: readonly KnownTown[],
  centres: ReadonlyMap<string, StateCentre>,
): ResolvedPlace | null {
  const text = normalise(input.address ?? "");
  const pincode =
    (input.pincode && /^[1-9][0-9]{5}$/.test(input.pincode.trim()) ? input.pincode.trim() : null) ??
    extractPincode(input.address ?? "");

  const state = findState(text, input.state, pincode);

  const gstCity = gstLabel(text, /\bcity town village ([a-z ]+?)(?= district| state| pin code| pincode|$)/);
  const gstDistrict = gstLabel(text, /\bdistrict ([a-z ]+?)(?= state| pin code| pincode|$)/);

  const byLabel =
    findTownByLabel(input.city ?? null, state, towns) ??
    findTownByLabel(gstCity, state, towns) ??
    findTownByLabel(gstDistrict, state, towns);
  if (byLabel) return place(byLabel, state, centres);

  const inText = findTownInText(text, state, towns);
  if (inText) return place(inText, state, centres);

  if (pincode) {
    const prefix = pincode.slice(0, 3);
    const byPin = GAZETTEER.find((g) => g.pins?.includes(prefix) && (!state || g.state === state));
    if (byPin) return { name: byPin.name, state: byPin.state, lat: byPin.lat, lng: byPin.lng, precision: "town" };
  }

  if (!state) return null;
  const centre = centres.get(state);
  if (!centre) return null;
  const label = input.city?.trim() || gstCity;
  return {
    name: label ? titleCase(normalise(label)) : state,
    state,
    lat: centre.lat,
    lng: centre.lng,
    precision: "state",
  };
}
