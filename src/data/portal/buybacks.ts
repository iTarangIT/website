export type BuybackStatus = "pending-evaluation" | "offer-made" | "accepted" | "rejected";

export interface BuybackRequest {
  id: string;
  customer: string;
  batteryId: string;
  sohPct: number;
  requestDate: string;
  originalValue: number;
  evaluationStatus: "awaiting-inspection" | "in-progress" | "complete";
  offer: number | null;
  status: BuybackStatus;
}

export const buybackRequests: BuybackRequest[] = [
  {
    id: "BB-2026-101",
    customer: "Ramesh Yadav",
    batteryId: "BT-DL-0142",
    sohPct: 87.2,
    requestDate: "2026-04-08",
    originalValue: 62000,
    evaluationStatus: "complete",
    offer: 40300, // 65% of original (SOH > 85%)
    status: "offer-made",
  },
  {
    id: "BB-2026-102",
    customer: "Santosh Mandal",
    batteryId: "BT-KOL-0082",
    sohPct: 78.5,
    requestDate: "2026-04-10",
    originalValue: 55000,
    evaluationStatus: "in-progress",
    offer: null,
    status: "pending-evaluation",
  },
  {
    id: "BB-2026-103",
    customer: "Deepak Thakur",
    batteryId: "BT-LKO-0112",
    sohPct: 91.8,
    requestDate: "2026-04-12",
    originalValue: 58000,
    evaluationStatus: "complete",
    offer: 40600, // 70% of original
    status: "accepted",
  },
  {
    id: "BB-2026-104",
    customer: "Dilip Kumar",
    batteryId: "BT-EDGE-04",
    sohPct: 64.2,
    requestDate: "2026-04-14",
    originalValue: 52000,
    evaluationStatus: "complete",
    offer: null, // Below 70% SOH → rejected per pricing logic
    status: "rejected",
  },
  {
    id: "BB-2026-105",
    customer: "Kamlesh Kumar",
    batteryId: "BT-PAT-0078",
    sohPct: 82.1,
    requestDate: "2026-04-15",
    originalValue: 58000,
    evaluationStatus: "awaiting-inspection",
    offer: null,
    status: "pending-evaluation",
  },
];

export const buybackPricingRules = {
  highSoh: { threshold: 85, minPct: 65, maxPct: 70, note: "SOH > 85% → 65-70% of original value" },
  midSoh: { threshold: 70, minPct: 50, maxPct: 65, note: "70% ≤ SOH ≤ 85% → 50-65% of original value" },
  lowSoh: { threshold: 0, minPct: 30, maxPct: 50, note: "SOH < 70% → 30-50% of original, or rejected" },
};
