export type LeadSource = "apify" | "gmaps" | "firecrawl";
export type LeadStage = "scraped" | "calling" | "qualified" | "handoff";

export interface IntentFactors {
  capability: number;   // 0-100
  response: number;
  timing: number;
  budget: number;
  readiness: number;
}

export interface Lead {
  id: string;
  businessName: string;
  contactName: string;
  phone: string;
  source: LeadSource;
  leadType: string;
  city: string;
  area: string;
  scrapedAt: string;
  stage: LeadStage;
  intentScore: number; // only meaningful once qualified+
  factors: IntentFactors;
  notes?: string;
}

export const initialLeads: Lead[] = [
  {
    id: "ld-001",
    businessName: "Sharma E-Rickshaw Rentals",
    contactName: "Anil Sharma",
    phone: "+91 98110 12345",
    source: "apify",
    leadType: "E-rickshaw fleet owner",
    city: "Delhi NCR",
    area: "Noida Sector 62",
    scrapedAt: "2026-04-18 09:22",
    stage: "scraped",
    intentScore: 82,
    factors: { capability: 85, response: 80, timing: 85, budget: 75, readiness: 85 },
    notes: "Owns 14 e-rickshaws. Lead-acid fleet, aging.",
  },
  {
    id: "ld-002",
    businessName: "Lucknow EV Hub",
    contactName: "Ravi Agarwal",
    phone: "+91 93550 22110",
    source: "gmaps",
    leadType: "Battery retailer",
    city: "Lucknow",
    area: "Chowk",
    scrapedAt: "2026-04-18 09:34",
    stage: "scraped",
    intentScore: 74,
    factors: { capability: 78, response: 72, timing: 70, budget: 80, readiness: 70 },
  },
  {
    id: "ld-003",
    businessName: "Bengal Drive Finance",
    contactName: "Subhash Bose",
    phone: "+91 98330 44002",
    source: "firecrawl",
    leadType: "NBFC / Finance agent",
    city: "Kolkata",
    area: "Park Street",
    scrapedAt: "2026-04-18 10:02",
    stage: "scraped",
    intentScore: 88,
    factors: { capability: 92, response: 88, timing: 85, budget: 90, readiness: 85 },
    notes: "Looking for battery-linked lending partner.",
  },
  {
    id: "ld-004",
    businessName: "Patna E-Cart Co.",
    contactName: "Shyam Mishra",
    phone: "+91 91100 33447",
    source: "apify",
    leadType: "E-rickshaw dealer",
    city: "Patna",
    area: "Kankarbagh",
    scrapedAt: "2026-04-18 10:18",
    stage: "scraped",
    intentScore: 68,
    factors: { capability: 70, response: 65, timing: 65, budget: 72, readiness: 68 },
  },
  {
    id: "ld-005",
    businessName: "Kashi E-Auto Sangh",
    contactName: "Manoj Pathak",
    phone: "+91 99110 80022",
    source: "gmaps",
    leadType: "Driver union head",
    city: "Varanasi",
    area: "Lanka",
    scrapedAt: "2026-04-18 10:45",
    stage: "scraped",
    intentScore: 79,
    factors: { capability: 82, response: 78, timing: 80, budget: 75, readiness: 80 },
    notes: "Represents 60+ drivers seeking loan options.",
  },
  {
    id: "ld-006",
    businessName: "Capital Green Mobility",
    contactName: "Rohan Malhotra",
    phone: "+91 90150 44110",
    source: "firecrawl",
    leadType: "Fleet operator",
    city: "Delhi NCR",
    area: "Dwarka",
    scrapedAt: "2026-04-18 11:02",
    stage: "scraped",
    intentScore: 85,
    factors: { capability: 88, response: 82, timing: 88, budget: 85, readiness: 82 },
  },
  {
    id: "ld-007",
    businessName: "Awadh Battery Point",
    contactName: "Farid Khan",
    phone: "+91 97220 11004",
    source: "gmaps",
    leadType: "Battery retailer",
    city: "Lucknow",
    area: "Aminabad",
    scrapedAt: "2026-04-18 11:15",
    stage: "scraped",
    intentScore: 56,
    factors: { capability: 60, response: 55, timing: 50, budget: 60, readiness: 55 },
    notes: "Currently lead-acid focused, hesitant.",
  },
  {
    id: "ld-008",
    businessName: "Howrah E-Mobility",
    contactName: "Debashis Paul",
    phone: "+91 98330 77110",
    source: "apify",
    leadType: "E-rickshaw dealer",
    city: "Kolkata",
    area: "Howrah",
    scrapedAt: "2026-04-18 11:28",
    stage: "scraped",
    intentScore: 72,
    factors: { capability: 75, response: 70, timing: 72, budget: 72, readiness: 72 },
  },
  // A couple that start in later stages for demo visual balance
  {
    id: "ld-009",
    businessName: "North Bihar Auto Finance",
    contactName: "Vikram Kumar",
    phone: "+91 91100 98832",
    source: "firecrawl",
    leadType: "NBFC / Finance agent",
    city: "Patna",
    area: "Boring Road",
    scrapedAt: "2026-04-18 08:45",
    stage: "qualified",
    intentScore: 91,
    factors: { capability: 95, response: 92, timing: 90, budget: 92, readiness: 85 },
    notes: "Qualified — ready to disburse 50L pilot.",
  },
  {
    id: "ld-010",
    businessName: "Sarnath Lithium Traders",
    contactName: "Rajiv Srivastava",
    phone: "+91 99110 22003",
    source: "gmaps",
    leadType: "Battery retailer",
    city: "Varanasi",
    area: "Sarnath",
    scrapedAt: "2026-04-18 09:02",
    stage: "qualified",
    intentScore: 78,
    factors: { capability: 80, response: 78, timing: 80, budget: 75, readiness: 78 },
  },
  {
    id: "ld-011",
    businessName: "Ghaziabad E-Rides",
    contactName: "Praveen Tyagi",
    phone: "+91 98110 44220",
    source: "apify",
    leadType: "E-rickshaw fleet owner",
    city: "Delhi NCR",
    area: "Ghaziabad",
    scrapedAt: "2026-04-17 17:22",
    stage: "handoff",
    intentScore: 87,
    factors: { capability: 90, response: 86, timing: 88, budget: 85, readiness: 86 },
    notes: "Handed off to sales — Rahul assigned.",
  },
  {
    id: "ld-012",
    businessName: "Salt Lake EV Charging",
    contactName: "Priya Banerjee",
    phone: "+91 98330 02210",
    source: "firecrawl",
    leadType: "Charging station operator",
    city: "Kolkata",
    area: "Salt Lake",
    scrapedAt: "2026-04-17 15:40",
    stage: "handoff",
    intentScore: 83,
    factors: { capability: 85, response: 82, timing: 82, budget: 85, readiness: 80 },
  },
];

export const SOURCE_LABEL: Record<LeadSource, string> = {
  apify: "Apify",
  gmaps: "Google Maps",
  firecrawl: "Firecrawl",
};

export const SOURCE_DESC: Record<LeadSource, string> = {
  apify: "Business directory scraping via Apify actors",
  gmaps: "Location search via Google Maps Places API",
  firecrawl: "Website extraction via Firecrawl",
};

export const QUALIFIED_THRESHOLD = 60;
