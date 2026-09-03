/**
 * Coordinates for cities and towns that dealer addresses mention. This is
 * reference data, not dealer data: which dealers exist and where they are
 * comes from the CRM database at request time (see locations.ts). The CRM's
 * own `cities` table is consulted too, but it has coordinates for only a
 * third of its rows, so the towns dealers actually trade from are pinned here.
 *
 * `npm run map:build` checks that every entry lies inside its state's polygon.
 *
 * Fields:
 *   aliases  other spellings seen in addresses (normalised: lowercase, no punctuation)
 *   pins     3-digit pincode prefixes that belong to this town alone; used when the
 *            town name is misspelt in the address
 */
export interface GazetteerEntry {
  name: string;
  state: string;
  lat: number;
  lng: number;
  aliases?: string[];
  pins?: string[];
}

export const GAZETTEER: readonly GazetteerEntry[] = [
  // Delhi NCR
  { name: "Delhi", state: "Delhi", lat: 28.6139, lng: 77.209, aliases: ["new delhi", "delhi ncr"], pins: ["110"] },
  { name: "Faridabad", state: "Haryana", lat: 28.4089, lng: 77.3178, pins: ["121"] },
  { name: "Gurugram", state: "Haryana", lat: 28.4595, lng: 77.0266, aliases: ["gurgaon"], pins: ["122"] },
  { name: "Noida", state: "Uttar Pradesh", lat: 28.5355, lng: 77.391 },
  { name: "Ghaziabad", state: "Uttar Pradesh", lat: 28.6692, lng: 77.4538 },
  { name: "Hapur", state: "Uttar Pradesh", lat: 28.7306, lng: 77.7759, pins: ["245"] },

  // Uttar Pradesh
  { name: "Meerut", state: "Uttar Pradesh", lat: 28.9845, lng: 77.7064, pins: ["250"] },
  { name: "Muzaffarnagar", state: "Uttar Pradesh", lat: 29.4727, lng: 77.7085, aliases: ["muzzafarnagar", "muzaffar nagar"], pins: ["251"] },
  { name: "Saharanpur", state: "Uttar Pradesh", lat: 29.968, lng: 77.546, pins: ["247"] },
  { name: "Moradabad", state: "Uttar Pradesh", lat: 28.8386, lng: 78.7733 },
  { name: "Bareilly", state: "Uttar Pradesh", lat: 28.367, lng: 79.4304, pins: ["243"] },
  { name: "Pilibhit", state: "Uttar Pradesh", lat: 28.6318, lng: 79.8043, aliases: ["bisalpur"] },
  { name: "Aligarh", state: "Uttar Pradesh", lat: 27.8974, lng: 78.088, pins: ["202"] },
  { name: "Mathura", state: "Uttar Pradesh", lat: 27.4924, lng: 77.6737, pins: ["281"] },
  { name: "Agra", state: "Uttar Pradesh", lat: 27.1767, lng: 78.0081, pins: ["282"] },
  { name: "Jhansi", state: "Uttar Pradesh", lat: 25.4484, lng: 78.5685, aliases: ["jhanshi"], pins: ["284"] },
  { name: "Kanpur", state: "Uttar Pradesh", lat: 26.4499, lng: 80.3319, pins: ["208"] },
  { name: "Lucknow", state: "Uttar Pradesh", lat: 26.8467, lng: 80.9462, pins: ["226"] },
  { name: "Prayagraj", state: "Uttar Pradesh", lat: 25.4358, lng: 81.8463, aliases: ["allahabad", "naini"], pins: ["211"] },
  { name: "Varanasi", state: "Uttar Pradesh", lat: 25.3176, lng: 82.9739, aliases: ["banaras", "benares"], pins: ["221"] },
  { name: "Mughalsarai", state: "Uttar Pradesh", lat: 25.2815, lng: 83.1198, aliases: ["mugalsarai", "pandit deen dayal upadhyaya nagar"] },
  { name: "Chandauli", state: "Uttar Pradesh", lat: 25.26, lng: 83.265, pins: ["232"] },
  { name: "Ghazipur", state: "Uttar Pradesh", lat: 25.5878, lng: 83.5783, pins: ["233"] },
  { name: "Gorakhpur", state: "Uttar Pradesh", lat: 26.7606, lng: 83.3732, pins: ["273"] },
  { name: "Siddharthnagar", state: "Uttar Pradesh", lat: 27.2818, lng: 83.0834, aliases: ["siddharth nagar", "naugarh"] },

  // Uttarakhand
  { name: "Dehradun", state: "Uttarakhand", lat: 30.3165, lng: 78.0322, pins: ["248"] },
  { name: "Haridwar", state: "Uttarakhand", lat: 29.9457, lng: 78.1642, pins: ["249"] },
  { name: "Kashipur", state: "Uttarakhand", lat: 29.2104, lng: 78.9619 },
  { name: "Bazpur", state: "Uttarakhand", lat: 29.1527, lng: 79.1085 },
  { name: "Rudrapur", state: "Uttarakhand", lat: 28.9845, lng: 79.4077 },
  { name: "Haldwani", state: "Uttarakhand", lat: 29.2183, lng: 79.513 },

  // Rajasthan
  { name: "Jaipur", state: "Rajasthan", lat: 26.9124, lng: 75.7873, pins: ["302", "303"] },
  { name: "Jodhpur", state: "Rajasthan", lat: 26.2389, lng: 73.0243, pins: ["342"] },
  { name: "Ajmer", state: "Rajasthan", lat: 26.4499, lng: 74.6399 },
  { name: "Beawar", state: "Rajasthan", lat: 26.1013, lng: 74.3204 },
  { name: "Didwana", state: "Rajasthan", lat: 27.4008, lng: 74.5744 },
  { name: "Nagaur", state: "Rajasthan", lat: 27.202, lng: 73.7339 },
  { name: "Balotra", state: "Rajasthan", lat: 25.8322, lng: 72.2405 },
  { name: "Barmer", state: "Rajasthan", lat: 25.7521, lng: 71.3967 },
  { name: "Udaipur", state: "Rajasthan", lat: 24.5854, lng: 73.7125, pins: ["313"] },
  { name: "Kota", state: "Rajasthan", lat: 25.2138, lng: 75.8648, pins: ["324"] },
  { name: "Bikaner", state: "Rajasthan", lat: 28.0229, lng: 73.3119, pins: ["334"] },
  { name: "Bharatpur", state: "Rajasthan", lat: 27.2173, lng: 77.4901, pins: ["321"] },

  // Madhya Pradesh
  { name: "Bhopal", state: "Madhya Pradesh", lat: 23.2599, lng: 77.4126, pins: ["462"] },
  { name: "Indore", state: "Madhya Pradesh", lat: 22.7196, lng: 75.8577, pins: ["452"] },
  { name: "Ujjain", state: "Madhya Pradesh", lat: 23.1765, lng: 75.7885, pins: ["456"] },
  { name: "Gwalior", state: "Madhya Pradesh", lat: 26.2183, lng: 78.1828, pins: ["474"] },
  { name: "Bhind", state: "Madhya Pradesh", lat: 26.5648, lng: 78.7873, pins: ["477"] },
  { name: "Jabalpur", state: "Madhya Pradesh", lat: 23.1815, lng: 79.9864, pins: ["482"] },

  // Bihar and Jharkhand
  { name: "Patna", state: "Bihar", lat: 25.5941, lng: 85.1376, aliases: ["danapur"], pins: ["800", "801"] },
  { name: "Gaya", state: "Bihar", lat: 24.7955, lng: 84.9994, pins: ["823"] },
  { name: "Darbhanga", state: "Bihar", lat: 26.1542, lng: 85.8918, pins: ["846"] },
  { name: "Muzaffarpur", state: "Bihar", lat: 26.1209, lng: 85.3647, pins: ["842"] },
  { name: "Samastipur", state: "Bihar", lat: 25.863, lng: 85.7811, pins: ["848"] },
  { name: "Jamui", state: "Bihar", lat: 24.927, lng: 86.224, pins: ["811"] },
  { name: "Bhagalpur", state: "Bihar", lat: 25.2425, lng: 86.9842, pins: ["812"] },
  { name: "Ranchi", state: "Jharkhand", lat: 23.3441, lng: 85.3096, pins: ["834"] },
  { name: "Jamshedpur", state: "Jharkhand", lat: 22.8046, lng: 86.2029, pins: ["831"] },
  { name: "Dhanbad", state: "Jharkhand", lat: 23.7957, lng: 86.4304, pins: ["826"] },

  // West Bengal
  { name: "Kolkata", state: "West Bengal", lat: 22.5726, lng: 88.3639, aliases: ["calcutta"], pins: ["700"] },
  { name: "Howrah", state: "West Bengal", lat: 22.5958, lng: 88.2636, pins: ["711"] },
  { name: "Suri", state: "West Bengal", lat: 23.9105, lng: 87.527, aliases: ["birbhum"], pins: ["731"] },
  { name: "Durgapur", state: "West Bengal", lat: 23.5204, lng: 87.3119 },
  { name: "Siliguri", state: "West Bengal", lat: 26.7271, lng: 88.3953, pins: ["734"] },

  // Elsewhere
  { name: "Chandigarh", state: "Chandigarh", lat: 30.7333, lng: 76.7794, pins: ["160"] },
  { name: "Ludhiana", state: "Punjab", lat: 30.901, lng: 75.8573, pins: ["141"] },
  { name: "Amritsar", state: "Punjab", lat: 31.634, lng: 74.8723, pins: ["143"] },
  { name: "Ahmedabad", state: "Gujarat", lat: 23.0225, lng: 72.5714, pins: ["380"] },
  { name: "Surat", state: "Gujarat", lat: 21.1702, lng: 72.8311, pins: ["395"] },
  { name: "Mumbai", state: "Maharashtra", lat: 19.076, lng: 72.8777, aliases: ["bombay"], pins: ["400"] },
  { name: "Pune", state: "Maharashtra", lat: 18.5204, lng: 73.8567, pins: ["411"] },
  { name: "Nagpur", state: "Maharashtra", lat: 21.1458, lng: 79.0882, pins: ["440"] },
  { name: "Hyderabad", state: "Telangana", lat: 17.385, lng: 78.4867, pins: ["500"] },
  { name: "Bengaluru", state: "Karnataka", lat: 12.9716, lng: 77.5946, aliases: ["bangalore"], pins: ["560"] },
  { name: "Chennai", state: "Tamil Nadu", lat: 13.0827, lng: 80.2707, aliases: ["madras"], pins: ["600"] },
  { name: "Guwahati", state: "Assam", lat: 26.1445, lng: 91.7362, pins: ["781"] },
  { name: "Bhubaneswar", state: "Odisha", lat: 20.2961, lng: 85.8245, pins: ["751"] },
  { name: "Raipur", state: "Chhattisgarh", lat: 21.2514, lng: 81.6296, pins: ["492"] },
];
