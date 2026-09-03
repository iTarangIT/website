/** One pin on the dealer map: a city or town with its dealer counts. */
export interface DealerLocation {
  /** Town or city name; the state name when only the state could be resolved. */
  name: string;
  /** Canonical state or UT name, spelled as in `src/data/india-map-paths.ts`. */
  state: string;
  lat: number;
  lng: number;
  /** Active dealer partners here. */
  dealers: number;
  /** Onboarding applications submitted here but not yet approved. */
  onboarding: number;
  /** "active" when at least one dealer is live, otherwise "planned". */
  status: "active" | "planned";
  /** True when the address could only be placed at state level. */
  approximate?: boolean;
}
