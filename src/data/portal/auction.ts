export type LotStatus = "live" | "upcoming" | "closing-soon" | "settled" | "no-bids";

export interface AuctionLot {
  id: string;
  capacity: string;      // "48V 100AH"
  modelMix: string;      // e.g. "iEnerzy / Trontek mix"
  avgSohRange: string;   // "70-85%"
  age: string;           // "12-18 months"
  quantity: number;
  basePrice: number;
  currentBid: number;
  bidderCount: number;
  chargerType: string;   // "Standard / Fast"
  endsAtIsoOffsetMinutes: number; // minutes from "now" when lot ends
  status: LotStatus;
  bidHistory: { bidder: string; amount: number; timeAgo: string }[];
}

export const auctionLots: AuctionLot[] = [
  {
    id: "LOT-2026-041",
    capacity: "48V 100AH",
    modelMix: "iEnerzy refurbishable",
    avgSohRange: "78-85%",
    age: "14-17 months",
    quantity: 24,
    basePrice: 245000,
    currentBid: 273000,
    bidderCount: 6,
    chargerType: "Standard",
    endsAtIsoOffsetMinutes: 42,
    status: "closing-soon",
    bidHistory: [
      { bidder: "Bidder #B-7821", amount: 273000, timeAgo: "3 min ago" },
      { bidder: "Bidder #B-4412", amount: 268000, timeAgo: "8 min ago" },
      { bidder: "Bidder #B-9933", amount: 260000, timeAgo: "19 min ago" },
      { bidder: "Bidder #B-7821", amount: 252000, timeAgo: "31 min ago" },
      { bidder: "Bidder #B-2088", amount: 248000, timeAgo: "46 min ago" },
    ],
  },
  {
    id: "LOT-2026-042",
    capacity: "60V 130AH",
    modelMix: "Trontek refurbishable",
    avgSohRange: "72-80%",
    age: "16-20 months",
    quantity: 18,
    basePrice: 412000,
    currentBid: 428000,
    bidderCount: 4,
    chargerType: "Standard",
    endsAtIsoOffsetMinutes: 128,
    status: "live",
    bidHistory: [
      { bidder: "Bidder #B-4412", amount: 428000, timeAgo: "24 min ago" },
      { bidder: "Bidder #B-6601", amount: 418000, timeAgo: "1 hr ago" },
    ],
  },
  {
    id: "LOT-2026-043",
    capacity: "51V 132AH",
    modelMix: "Mixed OEM",
    avgSohRange: "68-75%",
    age: "18-24 months",
    quantity: 32,
    basePrice: 384000,
    currentBid: 384000,
    bidderCount: 0,
    chargerType: "Standard",
    endsAtIsoOffsetMinutes: 320,
    status: "no-bids",
    bidHistory: [],
  },
  {
    id: "LOT-2026-044",
    capacity: "72V 100AH",
    modelMix: "Premium iEnerzy",
    avgSohRange: "82-88%",
    age: "10-14 months",
    quantity: 12,
    basePrice: 288000,
    currentBid: 312000,
    bidderCount: 8,
    chargerType: "Fast",
    endsAtIsoOffsetMinutes: 65,
    status: "live",
    bidHistory: [
      { bidder: "Bidder #B-9933", amount: 312000, timeAgo: "12 min ago" },
      { bidder: "Bidder #B-7821", amount: 304000, timeAgo: "28 min ago" },
      { bidder: "Bidder #B-2088", amount: 298000, timeAgo: "52 min ago" },
    ],
  },
  {
    id: "LOT-2026-045",
    capacity: "48V 130AH",
    modelMix: "Trontek refurbishable",
    avgSohRange: "75-82%",
    age: "14-18 months",
    quantity: 28,
    basePrice: 322000,
    currentBid: 340000,
    bidderCount: 5,
    chargerType: "Standard",
    endsAtIsoOffsetMinutes: 185,
    status: "live",
    bidHistory: [
      { bidder: "Bidder #B-6601", amount: 340000, timeAgo: "18 min ago" },
      { bidder: "Bidder #B-4412", amount: 332000, timeAgo: "40 min ago" },
    ],
  },
  {
    id: "LOT-2026-046",
    capacity: "60V 100AH",
    modelMix: "GoEl refurbishable",
    avgSohRange: "70-78%",
    age: "16-22 months",
    quantity: 22,
    basePrice: 210000,
    currentBid: 234000,
    bidderCount: 7,
    chargerType: "Standard",
    endsAtIsoOffsetMinutes: 95,
    status: "live",
    bidHistory: [
      { bidder: "Bidder #B-2088", amount: 234000, timeAgo: "7 min ago" },
      { bidder: "Bidder #B-7821", amount: 228000, timeAgo: "22 min ago" },
    ],
  },
  {
    id: "LOT-2026-047",
    capacity: "72V 232AH",
    modelMix: "Premium mixed",
    avgSohRange: "80-88%",
    age: "8-12 months",
    quantity: 8,
    basePrice: 720000,
    currentBid: 768000,
    bidderCount: 3,
    chargerType: "Fast",
    endsAtIsoOffsetMinutes: 265,
    status: "live",
    bidHistory: [
      { bidder: "Bidder #B-4412", amount: 768000, timeAgo: "1 hr ago" },
    ],
  },
  {
    id: "LOT-2026-048",
    capacity: "51V 105AH",
    modelMix: "Mixed refurbishable",
    avgSohRange: "65-72%",
    age: "20-26 months",
    quantity: 34,
    basePrice: 340000,
    currentBid: 356000,
    bidderCount: 4,
    chargerType: "Standard",
    endsAtIsoOffsetMinutes: 225,
    status: "live",
    bidHistory: [
      { bidder: "Bidder #B-6601", amount: 356000, timeAgo: "32 min ago" },
      { bidder: "Bidder #B-9933", amount: 348000, timeAgo: "55 min ago" },
    ],
  },
];

export const recoveryPipeline = {
  total: 342,
  needsInspection: 124,
  refurbishable: 156,
  scrap: 42,
  resold: 20,
  valueLockedCr: 1.24,
  estRecoveryLakhs: 78,
  recoveryRatePct: 63,
};

export interface SettledLot {
  id: string;
  assets: string;
  basePrice: number;
  finalPrice: number;
  winner: string;
  status: "delivered" | "in-transit" | "payment-pending" | "in-progress";
}

export const settledLots: SettledLot[] = [
  { id: "LOT-2026-038", assets: "20× 48V 100AH · Refurb", basePrice: 205000, finalPrice: 238000, winner: "Bidder #B-7821", status: "delivered" },
  { id: "LOT-2026-037", assets: "14× 60V 130AH · Refurb", basePrice: 315000, finalPrice: 348000, winner: "Bidder #B-4412", status: "in-transit" },
  { id: "LOT-2026-036", assets: "26× 51V 132AH · Mixed", basePrice: 302000, finalPrice: 312000, winner: "Bidder #B-6601", status: "payment-pending" },
  { id: "LOT-2026-035", assets: "10× 72V 232AH · Premium", basePrice: 880000, finalPrice: 965000, winner: "Bidder #B-9933", status: "delivered" },
  { id: "LOT-2026-034", assets: "18× 48V 130AH · Refurb", basePrice: 238000, finalPrice: 260000, winner: "Bidder #B-2088", status: "in-progress" },
];

export const revenueSummary = {
  totalAuctionValueLakhs: 42.3,
  recoveryRatePct: 64.2,
  avgPremiumOverBasePct: 11.8,
  assetsResold: 156,
};
