import { portalDrivers, type Driver } from "./drivers";

// Loan records derived from drivers (1 driver = 1 loan) plus some closed / written-off entries.
// This file powers Battery Monitoring master table and Risk Intelligence cohort stats.

export interface BatteryRow {
  batteryId: string;          // Display ID (e.g. BT-3567)
  imei: string;               // Demo IMEI
  customer: string;
  dealer: string;
  city: string;
  sohPct: number;
  sohTrend: "up" | "down" | "steady";
  dailyKm30d: number;
  emiStatus: "current" | "overdue-1-7" | "overdue-8-30" | "overdue-30+" | "skipped";
  overdueDays: number;
  cds: number;
  pci: number;
  riskLevel: "low" | "medium" | "high" | "very-high";
  // Telemetry-derived signals (lifted from driver for client-side filtering)
  imbalanceEvents7d: number;
  offlineHours7d: number;
  geoShiftFlag: boolean;
  idleDays7d: number;
  // Extended from driver
  driverId: string;
  outstanding: number;
  loanId: string;
  // Edge cases
  isInsufficientHistory?: boolean;
  isRecentlyRestructured?: boolean;
  isForceMajeure?: boolean;
  immobilized?: boolean;
  rejectedAction?: { type: string; reason: string };
}

function makeImei(id: string): string {
  // Deterministic synthetic IMEI — 15 digits
  const seed = id.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  let n = seed;
  let out = "86";
  for (let i = 0; i < 13; i++) {
    n = (n * 1103515245 + 12345) & 0x7fffffff;
    out += String(n % 10);
  }
  return out;
}

function makeBatteryId(i: number): string {
  return `BT-${String(3500 + i * 7).padStart(4, "0")}`;
}

function makeLoanId(i: number): string {
  return `LN-2024-${String(8000 + i * 37).padStart(5, "0")}`;
}

function bandToRiskLevel(cds: number): BatteryRow["riskLevel"] {
  if (cds >= 61) return "very-high";
  if (cds >= 41) return "high";
  if (cds >= 21) return "medium";
  return "low";
}

function emiStatusFromDpd(dpd: number): BatteryRow["emiStatus"] {
  if (dpd === 0) return "current";
  if (dpd <= 7) return "overdue-1-7";
  if (dpd <= 30) return "overdue-8-30";
  return "overdue-30+";
}

function trendFromDelta(delta: number): BatteryRow["sohTrend"] {
  if (delta > 0.1) return "up";
  if (delta < -0.2) return "down";
  return "steady";
}

// Map Mohan Sharma to drv-014 as hero persona (needs specific fields for case workspace)
const MOHAN_OVERRIDES: Partial<BatteryRow> = {
  customer: "Mohan Sharma",
  city: "Prayagraj",
  dealer: "XYZ Battery Trading",
  batteryId: "BT-3567",
  loanId: "LN-2024-08932",
  sohPct: 82.3,
  sohTrend: "down",
  dailyKm30d: 28,
  emiStatus: "overdue-8-30",
  overdueDays: 9,
  cds: 72,
  pci: 0.38,
  riskLevel: "very-high",
  immobilized: false,
};
const RAJESH_OVERRIDES: Partial<BatteryRow> = {
  customer: "Rajesh Kumar",
  city: "Lucknow",
  dealer: "ABC Dealers",
  batteryId: "BT-8983",
  sohPct: 91.0,
  sohTrend: "steady",
  dailyKm30d: 67,
  cds: 12,
  pci: 0.92,
  riskLevel: "low",
};

export const batteryRows: BatteryRow[] = portalDrivers.map((d: Driver, i: number) => {
  const base: BatteryRow = {
    batteryId: makeBatteryId(i),
    imei: makeImei(d.id),
    customer: d.name,
    dealer: d.dealerName,
    city: d.city,
    sohPct: d.sohPct,
    sohTrend: trendFromDelta(d.sohDelta30d),
    dailyKm30d: d.avgDailyKm30d,
    emiStatus: emiStatusFromDpd(d.loan.dpd),
    overdueDays: d.loan.dpd,
    cds: d.risk.cdsScore,
    pci: d.risk.pci,
    riskLevel: bandToRiskLevel(d.risk.cdsScore),
    imbalanceEvents7d: d.imbalanceEvents7d,
    offlineHours7d: d.offlineHours7d,
    geoShiftFlag: d.risk.geoShiftFlag,
    idleDays7d: d.risk.idleDays7d,
    driverId: d.id,
    outstanding: d.loan.outstanding,
    loanId: makeLoanId(i),
  };

  if (d.id === "drv-014") return { ...base, ...MOHAN_OVERRIDES };
  if (d.id === "drv-001") return { ...base, ...RAJESH_OVERRIDES };
  return base;
});

// Edge case rows — appended for the Battery Monitoring table.
export const edgeCaseRows: BatteryRow[] = [
  {
    batteryId: "BT-EDGE-01",
    imei: "865000000123401",
    customer: "Ashok Yadav",
    dealer: "Patna E-Mobility",
    city: "Patna",
    sohPct: 96.0,
    sohTrend: "steady",
    dailyKm30d: 42,
    emiStatus: "current",
    overdueDays: 0,
    cds: 0,
    pci: 0.5,
    riskLevel: "low",
    imbalanceEvents7d: 0,
    offlineHours7d: 0.5,
    geoShiftFlag: false,
    idleDays7d: 0,
    driverId: "drv-edge-1",
    outstanding: 45000,
    loanId: "LN-2025-00011",
    isInsufficientHistory: true,
  },
  {
    batteryId: "BT-EDGE-02",
    imei: "865000000123402",
    customer: "Neha Singh",
    dealer: "Sharma E-Motors",
    city: "Delhi NCR",
    sohPct: 93.1,
    sohTrend: "steady",
    dailyKm30d: 40,
    emiStatus: "current",
    overdueDays: 0,
    cds: 34,
    pci: 0.78,
    riskLevel: "medium",
    imbalanceEvents7d: 1,
    offlineHours7d: 1.2,
    geoShiftFlag: false,
    idleDays7d: 0,
    driverId: "drv-edge-2",
    outstanding: 32000,
    loanId: "LN-2024-01234",
    isRecentlyRestructured: true,
  },
  {
    batteryId: "BT-EDGE-03",
    imei: "865000000123403",
    customer: "Bashir Ahmed",
    dealer: "Awadh E-Wheels",
    city: "Lucknow",
    sohPct: 89.0,
    sohTrend: "down",
    dailyKm30d: 15,
    emiStatus: "overdue-8-30",
    overdueDays: 22,
    cds: 58,
    pci: 0.54,
    riskLevel: "high",
    imbalanceEvents7d: 3,
    offlineHours7d: 18.4,
    geoShiftFlag: true,
    idleDays7d: 2,
    driverId: "drv-edge-3",
    outstanding: 18000,
    loanId: "LN-2024-00876",
    isForceMajeure: true,
  },
  {
    batteryId: "BT-EDGE-04",
    imei: "865000000123404",
    customer: "Dilip Kumar",
    dealer: "Bengal E-Rides",
    city: "Kolkata",
    sohPct: 84.0,
    sohTrend: "down",
    dailyKm30d: 10,
    emiStatus: "overdue-30+",
    overdueDays: 48,
    cds: 78,
    pci: 0.31,
    riskLevel: "very-high",
    imbalanceEvents7d: 6,
    offlineHours7d: 92,
    geoShiftFlag: true,
    idleDays7d: 5,
    driverId: "drv-edge-4",
    outstanding: 12000,
    loanId: "LN-2024-00544",
    rejectedAction: {
      type: "Request Immobilization",
      reason: "Dual approval denied by Ops — borrower dispute pending resolution",
    },
  },
];

export const allBatteryRows: BatteryRow[] = [...batteryRows, ...edgeCaseRows];

// Portfolio counts for Risk Intelligence distribution donut
export const portfolioDistribution = {
  low: { count: 3122, pct: 64.3 },
  medium: { count: 607, pct: 12.5 },
  high: { count: 890, pct: 18.3 },
  veryHigh: { count: 237, pct: 4.9 },
};

export interface CohortRow {
  segment: string;
  accounts: number;
  defaultRatePct: number;
  recoveryRatePct: number;
  avgSoh: number;
}

export const cohortRows: CohortRow[] = [
  { segment: "Delhi NCR · E-rickshaw", accounts: 1120, defaultRatePct: 6.8, recoveryRatePct: 74.2, avgSoh: 96.2 },
  { segment: "Delhi NCR · E-auto", accounts: 385, defaultRatePct: 7.4, recoveryRatePct: 68.5, avgSoh: 95.8 },
  { segment: "Kolkata · E-rickshaw", accounts: 610, defaultRatePct: 8.3, recoveryRatePct: 66.1, avgSoh: 95.6 },
  { segment: "Lucknow · E-rickshaw", accounts: 740, defaultRatePct: 9.2, recoveryRatePct: 64.8, avgSoh: 95.1 },
  { segment: "Kolkata · E-auto", accounts: 195, defaultRatePct: 10.1, recoveryRatePct: 61.0, avgSoh: 94.3 },
  { segment: "Patna · E-rickshaw", accounts: 480, defaultRatePct: 11.4, recoveryRatePct: 58.9, avgSoh: 93.6 },
  { segment: "Patna · E-auto", accounts: 154, defaultRatePct: 12.8, recoveryRatePct: 54.2, avgSoh: 92.9 },
  { segment: "Varanasi · E-rickshaw", accounts: 308, defaultRatePct: 13.6, recoveryRatePct: 51.7, avgSoh: 92.4 },
  { segment: "Varanasi · E-auto", accounts: 104, defaultRatePct: 15.8, recoveryRatePct: 47.1, avgSoh: 91.2 },
];
