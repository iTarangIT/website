export type LeadStatus = "hot" | "warm" | "cold" | "converted" | "lost";
export type LeadSource = "apify" | "gmaps" | "firecrawl" | "referral";

export interface Lead {
  id: string;
  name: string;
  businessType: string;
  location: string;
  phone: string;
  intentScore: number; // 0-100
  status: LeadStatus;
  nextAction: string;
  lastContact: string;
  source: LeadSource;
  confidence: "low" | "medium" | "high";
  // Intent score inputs (for explainability modal)
  inputs: {
    questionType: string;
    toneKeywords: string[];
    callbackRequested: boolean;
    budgetSignaled: boolean;
    timelineStated: string;
  };
}

export const leadFunnel = {
  cold: 14000,
  warm: 4000,
  hot: 1500,
  converted: 500,
  // Conversion % to next stage
  coldToWarm: 28.6,
  warmToHot: 37.5,
  hotToConverted: 33.3,
};

export const leadKPIs = {
  leadsContactedToday: 847,
  leadsContactedDeltaPct: 12,
  aiCallsToday: 1243,
  hotLeadsGenerated: 156,
  conversionRatePct: 2.8,
};

const FIRST_NAMES = ["Anil", "Ravi", "Subhash", "Shyam", "Manoj", "Rohan", "Farid", "Debashis", "Vikram", "Rajiv", "Praveen", "Priya", "Kiran", "Rakesh", "Santosh", "Amit", "Naveen", "Dinesh", "Mukesh", "Arun"];
const SURNAMES = ["Sharma", "Agarwal", "Bose", "Mishra", "Pathak", "Malhotra", "Khan", "Paul", "Kumar", "Srivastava", "Tyagi", "Banerjee", "Gupta", "Yadav", "Mandal", "Singh", "Thakur", "Verma", "Das", "Rai"];
const BIZ = ["E-rickshaw fleet owner", "Battery retailer", "Charging station operator", "Driver union head", "E-rickshaw dealer", "NBFC / Finance agent", "Fleet operator", "Battery distributor"];
const LOCS = ["Delhi NCR · Noida", "Lucknow · Chowk", "Kolkata · Park Street", "Patna · Kankarbagh", "Varanasi · Lanka", "Delhi NCR · Dwarka", "Lucknow · Aminabad", "Kolkata · Howrah", "Patna · Boring Road", "Varanasi · Sarnath", "Delhi NCR · Ghaziabad", "Kolkata · Salt Lake"];

// Deterministic small PRNG so rows are stable across renders
function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const rand = mulberry32(42);

function pick<T>(arr: T[]): T {
  return arr[Math.floor(rand() * arr.length)];
}

function statusFromScore(score: number): LeadStatus {
  if (score >= 80) return "hot";
  if (score >= 50) return "warm";
  return "cold";
}

function nextActionFor(status: LeadStatus): string {
  switch (status) {
    case "hot": return "Assign to ground team";
    case "warm": return "Call centre follow-up";
    case "cold": return "AI nurture campaign";
    case "converted": return "Onboard to NBFC";
    case "lost": return "Archive";
  }
}

// 50 representative leads
export const leads: Lead[] = Array.from({ length: 50 }, (_, i) => {
  // Distribute status: a few converted, a few hot (80+), many warm (50-79), some cold (<50)
  let score: number;
  if (i < 4) score = 88 + Math.floor(rand() * 10); // converted-ish, hot
  else if (i < 14) score = 80 + Math.floor(rand() * 15);
  else if (i < 34) score = 50 + Math.floor(rand() * 30);
  else score = 20 + Math.floor(rand() * 30);

  const status: LeadStatus = i < 3 ? "converted" : statusFromScore(score);

  const callback = rand() > 0.4;
  const budget = rand() > 0.5;
  const timelines = ["1-2 weeks", "within a month", "2-3 months", "exploring", "immediate"];
  const tones = [
    ["interested", "keen", "ready"],
    ["curious", "exploring", "considering"],
    ["hesitant", "not sure", "busy"],
    ["asked about EMI", "asked about price", "asked about warranty"],
  ];

  return {
    id: `ld-${String(i + 1).padStart(3, "0")}`,
    name: `${pick(FIRST_NAMES)} ${pick(SURNAMES)}`,
    businessType: pick(BIZ),
    location: pick(LOCS),
    phone: `+91 9${Math.floor(10000000 + rand() * 89999999)}`,
    intentScore: score,
    status,
    nextAction: nextActionFor(status),
    lastContact: `${Math.floor(1 + rand() * 7)}d ago`,
    source: pick<LeadSource>(["apify", "gmaps", "firecrawl", "referral"]),
    confidence: score > 70 ? "medium" : "low",
    inputs: {
      questionType: callback && budget ? "Cost + timeline" : callback ? "Follow-up" : budget ? "Pricing" : "General",
      toneKeywords: pick(tones),
      callbackRequested: callback,
      budgetSignaled: budget,
      timelineStated: pick(timelines),
    },
  };
});

export const SOURCE_LABEL: Record<LeadSource, string> = {
  apify: "Apify",
  gmaps: "Google Maps",
  firecrawl: "Firecrawl",
  referral: "Referral",
};

export interface CallSlot {
  dayOffset: number; // 0 = today
  hour: number;      // 24h
  status: "scheduled" | "in-progress" | "completed" | "missed";
  leadId?: string;
  leadName?: string;
}

// 7-day AI call scheduler — a handful of slots per day
export const callSchedule: CallSlot[] = [
  { dayOffset: 0, hour: 10, status: "completed", leadId: "ld-001", leadName: "Anil Sharma" },
  { dayOffset: 0, hour: 11, status: "completed", leadId: "ld-002", leadName: "Ravi Agarwal" },
  { dayOffset: 0, hour: 14, status: "in-progress", leadId: "ld-003", leadName: "Subhash Bose" },
  { dayOffset: 0, hour: 15, status: "scheduled", leadId: "ld-004", leadName: "Shyam Mishra" },
  { dayOffset: 0, hour: 16, status: "scheduled", leadId: "ld-005", leadName: "Manoj Pathak" },
  { dayOffset: 1, hour: 10, status: "scheduled", leadId: "ld-006", leadName: "Rohan Malhotra" },
  { dayOffset: 1, hour: 12, status: "scheduled", leadId: "ld-007", leadName: "Farid Khan" },
  { dayOffset: 2, hour: 11, status: "scheduled", leadId: "ld-008", leadName: "Debashis Paul" },
  { dayOffset: 3, hour: 10, status: "scheduled", leadId: "ld-009", leadName: "Vikram Kumar" },
  { dayOffset: 4, hour: 14, status: "scheduled", leadId: "ld-010", leadName: "Rajiv Srivastava" },
  { dayOffset: 0, hour: 17, status: "missed", leadId: "ld-011", leadName: "Praveen Tyagi" },
];
