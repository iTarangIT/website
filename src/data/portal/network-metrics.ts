export const networkKPIs = {
  leadsAcquired30d: 8420,
  aiPickupRatePct: 48.2,
  costPerAcquisitionRupees: 180,
  dialerUptimePct: 99.1,
};

export interface RegionalDialer {
  region: string;
  pickupRatePct: number;
  avgCallDurationSec: number;
  conversionPct: number;
  cpa: number;
}

export const regionalDialerPerformance: RegionalDialer[] = [
  { region: "Delhi NCR", pickupRatePct: 54.1, avgCallDurationSec: 148, conversionPct: 3.2, cpa: 162 },
  { region: "Lucknow", pickupRatePct: 51.3, avgCallDurationSec: 132, conversionPct: 2.9, cpa: 174 },
  { region: "Kolkata", pickupRatePct: 49.8, avgCallDurationSec: 125, conversionPct: 2.6, cpa: 185 },
  { region: "Patna", pickupRatePct: 44.2, avgCallDurationSec: 108, conversionPct: 2.1, cpa: 210 },
  { region: "Varanasi", pickupRatePct: 39.7, avgCallDurationSec: 94, conversionPct: 1.7, cpa: 228 },
];

export interface RegionalFunnel {
  region: string;
  cold: number;
  warm: number;
  hot: number;
  converted: number;
}

export const regionalFunnels: RegionalFunnel[] = [
  { region: "Delhi NCR", cold: 4800, warm: 1440, hot: 540, converted: 172 },
  { region: "Lucknow", cold: 3200, warm: 890, hot: 340, converted: 98 },
  { region: "Kolkata", cold: 2900, warm: 760, hot: 280, converted: 72 },
];

export interface CallRecording {
  id: string;
  leadName: string;
  businessType: string;
  city: string;
  durationSec: number;
  outcome: "hot" | "warm" | "cold" | "do-not-call";
  timeAgo: string;
  transcriptSnippet: string;
}

export const recentCallRecordings: CallRecording[] = [
  {
    id: "rec-4221",
    leadName: "Anil Sharma",
    businessType: "E-rickshaw fleet owner",
    city: "Delhi NCR",
    durationSec: 183,
    outcome: "hot",
    timeAgo: "18 min ago",
    transcriptSnippet: "\"Haan, 14 rickshaw hai. Agar 6 mahine ki EMI thik hogi to Tuesday demo kar sakte ho…\"",
  },
  {
    id: "rec-4220",
    leadName: "Ravi Agarwal",
    businessType: "Battery retailer",
    city: "Lucknow",
    durationSec: 142,
    outcome: "warm",
    timeAgo: "34 min ago",
    transcriptSnippet: "\"Price mein discount milega kya bulk order pe? Main next month aata hu Delhi…\"",
  },
  {
    id: "rec-4219",
    leadName: "Subhash Bose",
    businessType: "NBFC agent",
    city: "Kolkata",
    durationSec: 226,
    outcome: "hot",
    timeAgo: "52 min ago",
    transcriptSnippet: "\"We have 50 lakh pilot budget. Telemetry integration is the critical piece for us…\"",
  },
  {
    id: "rec-4218",
    leadName: "Manoj Pathak",
    businessType: "Driver union head",
    city: "Varanasi",
    durationSec: 98,
    outcome: "warm",
    timeAgo: "1 hr ago",
    transcriptSnippet: "\"Union ke 60 drivers hain, sab lead-acid pe. Pricing bhej do WhatsApp pe.\"",
  },
  {
    id: "rec-4217",
    leadName: "Farid Khan",
    businessType: "Battery retailer",
    city: "Lucknow",
    durationSec: 48,
    outcome: "cold",
    timeAgo: "1 hr ago",
    transcriptSnippet: "\"Hum lead-acid hi rakhte hain. Customer nahi maanta.\"",
  },
];

export const cpaBreakdown = {
  dialerCostPerLeadRupees: 28,
  manualFollowupCostRupees: 112,
  telemetrySetupAmortizedRupees: 40,
  totalCpa: 180,
  industryAverageCpa: 420,
};
