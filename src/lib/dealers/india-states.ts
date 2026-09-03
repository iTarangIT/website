/**
 * Reference data for turning free-text addresses into a canonical state name.
 * Canonical names must match `indiaMap.states[].name` in
 * `src/data/india-map-paths.ts`; `locate.test.ts` checks that.
 */

const AN = "Andaman and Nicobar Islands";
const DNHDD = "Dadra and Nagar Haveli and Daman and Diu";

/** Two-letter codes as used by the CRM `cities.state_code` column and in addresses. */
export const STATE_BY_CODE: Readonly<Record<string, string>> = {
  AN,
  AP: "Andhra Pradesh",
  AR: "Arunachal Pradesh",
  AS: "Assam",
  BR: "Bihar",
  CH: "Chandigarh",
  CG: "Chhattisgarh",
  CT: "Chhattisgarh",
  DD: DNHDD,
  DH: DNHDD,
  DN: DNHDD,
  DL: "Delhi",
  GA: "Goa",
  GJ: "Gujarat",
  HR: "Haryana",
  HP: "Himachal Pradesh",
  JK: "Jammu and Kashmir",
  JH: "Jharkhand",
  KA: "Karnataka",
  KL: "Kerala",
  LA: "Ladakh",
  LD: "Lakshadweep",
  MP: "Madhya Pradesh",
  MH: "Maharashtra",
  MN: "Manipur",
  ML: "Meghalaya",
  MZ: "Mizoram",
  NL: "Nagaland",
  OD: "Odisha",
  OR: "Odisha",
  PY: "Puducherry",
  PB: "Punjab",
  RJ: "Rajasthan",
  SK: "Sikkim",
  TN: "Tamil Nadu",
  TS: "Telangana",
  TG: "Telangana",
  TR: "Tripura",
  UP: "Uttar Pradesh",
  UK: "Uttarakhand",
  UT: "Uttarakhand",
  WB: "West Bengal",
};

export const ALL_STATES: readonly string[] = Array.from(new Set(Object.values(STATE_BY_CODE))).sort();

/**
 * Spellings found in addresses, already normalised (lowercase, punctuation
 * collapsed to single spaces). Every canonical name is included as its own
 * alias. Two-letter codes are deliberately NOT here; `locate.ts` accepts
 * those only right before the pincode or at the end of the text.
 */
export const STATE_ALIASES: Readonly<Record<string, string>> = {
  ...Object.fromEntries(ALL_STATES.map((s) => [s.toLowerCase(), s])),
  andaman: AN,
  "andaman nicobar": AN,
  "andaman nicobar islands": AN,
  "dadra nagar haveli": DNHDD,
  "dadra and nagar haveli": DNHDD,
  "daman diu": DNHDD,
  "daman and diu": DNHDD,
  "new delhi": "Delhi",
  "delhi ncr": "Delhi",
  "nct of delhi": "Delhi",
  "jammu kashmir": "Jammu and Kashmir",
  "jammu and kashmir": "Jammu and Kashmir",
  "j and k": "Jammu and Kashmir",
  orissa: "Odisha",
  pondicherry: "Puducherry",
  uttaranchal: "Uttarakhand",
  bengal: "West Bengal",
  chattisgarh: "Chhattisgarh",
  chhatisgarh: "Chhattisgarh",
  "tamilnadu": "Tamil Nadu",
  "telengana": "Telangana",
};

/** Map any spelling or code to the canonical state name, or null. */
export function canonicalState(value: string | null | undefined): string | null {
  if (!value) return null;
  const key = value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  if (!key) return null;
  return STATE_ALIASES[key] ?? STATE_BY_CODE[key.toUpperCase()] ?? null;
}

/**
 * Coarse pincode → state map, used only when an address names no state.
 * Three-digit rows win over two-digit rows. Border sorting districts that
 * straddle two states (for example 262 across UP and Uttarakhand) are left
 * on the larger state; the address text almost always settles it first.
 */
const PIN3: Readonly<Record<string, string>> = {
  "160": "Chandigarh",
  "194": "Ladakh",
  "248": "Uttarakhand",
  "249": "Uttarakhand",
  "263": "Uttarakhand",
  "396": DNHDD,
  "403": "Goa",
  "605": "Puducherry",
  "682": "Lakshadweep",
  "737": "Sikkim",
  "744": AN,
  "790": "Arunachal Pradesh",
  "791": "Arunachal Pradesh",
  "792": "Arunachal Pradesh",
  "793": "Meghalaya",
  "794": "Meghalaya",
  "795": "Manipur",
  "796": "Mizoram",
  "797": "Nagaland",
  "798": "Nagaland",
  "799": "Tripura",
  "814": "Jharkhand",
  "815": "Jharkhand",
  "816": "Jharkhand",
  "822": "Jharkhand",
  "825": "Jharkhand",
  "826": "Jharkhand",
  "827": "Jharkhand",
  "828": "Jharkhand",
  "829": "Jharkhand",
  "831": "Jharkhand",
  "832": "Jharkhand",
  "833": "Jharkhand",
  "834": "Jharkhand",
  "835": "Jharkhand",
};

const PIN2: Readonly<Record<string, string>> = {
  "11": "Delhi",
  "12": "Haryana",
  "13": "Haryana",
  "14": "Punjab",
  "15": "Punjab",
  "16": "Punjab",
  "17": "Himachal Pradesh",
  "18": "Jammu and Kashmir",
  "19": "Jammu and Kashmir",
  "20": "Uttar Pradesh",
  "21": "Uttar Pradesh",
  "22": "Uttar Pradesh",
  "23": "Uttar Pradesh",
  "24": "Uttar Pradesh",
  "25": "Uttar Pradesh",
  "26": "Uttar Pradesh",
  "27": "Uttar Pradesh",
  "28": "Uttar Pradesh",
  "30": "Rajasthan",
  "31": "Rajasthan",
  "32": "Rajasthan",
  "33": "Rajasthan",
  "34": "Rajasthan",
  "36": "Gujarat",
  "37": "Gujarat",
  "38": "Gujarat",
  "39": "Gujarat",
  "40": "Maharashtra",
  "41": "Maharashtra",
  "42": "Maharashtra",
  "43": "Maharashtra",
  "44": "Maharashtra",
  "45": "Madhya Pradesh",
  "46": "Madhya Pradesh",
  "47": "Madhya Pradesh",
  "48": "Madhya Pradesh",
  "49": "Chhattisgarh",
  "50": "Telangana",
  "51": "Andhra Pradesh",
  "52": "Andhra Pradesh",
  "53": "Andhra Pradesh",
  "56": "Karnataka",
  "57": "Karnataka",
  "58": "Karnataka",
  "59": "Karnataka",
  "60": "Tamil Nadu",
  "61": "Tamil Nadu",
  "62": "Tamil Nadu",
  "63": "Tamil Nadu",
  "64": "Tamil Nadu",
  "67": "Kerala",
  "68": "Kerala",
  "69": "Kerala",
  "70": "West Bengal",
  "71": "West Bengal",
  "72": "West Bengal",
  "73": "West Bengal",
  "74": "West Bengal",
  "75": "Odisha",
  "76": "Odisha",
  "77": "Odisha",
  "78": "Assam",
  "80": "Bihar",
  "81": "Bihar",
  "82": "Bihar",
  "83": "Bihar",
  "84": "Bihar",
  "85": "Bihar",
};

export function stateFromPincode(pincode: string | null | undefined): string | null {
  if (!pincode || !/^[1-9][0-9]{5}$/.test(pincode)) return null;
  return PIN3[pincode.slice(0, 3)] ?? PIN2[pincode.slice(0, 2)] ?? null;
}
