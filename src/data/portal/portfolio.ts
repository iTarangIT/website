// Portfolio-level aggregates, narrative content, hero personas.
// Aggregate numbers are demo values anchored to the brief (~₹12.4 Cr portfolio, 4,856 active loans, 1,124 at-risk).

export const portfolioKPIs = {
  activeLoans: 4856,
  activeLoansDeltaPct: 3.2,
  atRiskAccounts: 1124,
  atRiskPct: 23.1,
  atRiskDeltaPct: -1.6,
  delinquencyRatePct: 9.2,
  delinquencyDeltaPctMoM: -0.8,
  delinquencyBaselinePct: 12.0,
  recoveryInMotionLakhs: 78,
  recoveryPct: 67,
  portfolioValueCr: 12.4,
  preventedLossLakhsQtd: 34.7,
  collectionEfficiencyPct: 91.4,
  collectionEfficiencyBaselinePct: 79.0,
  recoveryRatePct: 64.2,
  recoveryRateBaselinePct: 50.0,
};

export const narrativeHeader =
  "Portfolio health is improving. Delinquency down 0.8% MoM, ₹34.7 L in prevented losses this quarter.";

export const threeActStrip = [
  {
    act: "acquire" as const,
    icon: "🎯",
    title: "Acquire",
    headline: "Pre-disbursement underwriting",
    metric: "+150 bps on high-risk clusters",
    href: "/nbfc/risk",
  },
  {
    act: "monitor" as const,
    icon: "🛡️",
    title: "Monitor",
    headline: "1,124 at-risk prevented",
    metric: "from default last quarter",
    href: "/nbfc/batteries",
  },
  {
    act: "recover" as const,
    icon: "♻️",
    title: "Recover",
    headline: "₹78 L recycled",
    metric: "64.2% recovery rate",
    href: "/nbfc/recovery",
  },
];

export const whatChangedThisWeek = [
  "Delinquency dropped 0.8 pp after the Lucknow reminder campaign closed — 78 overdue EMIs settled in 4 days.",
  "142 new at-risk flags triggered by a charging-pattern anomaly in the Patna cluster — auto-escalated to ground team.",
  "Recovery pipeline grew by ₹12 L as 34 idle batteries were reclassified refurbishable after technician inspection.",
];

export const recentActions = {
  reMobilizations: 12,
  fieldVisits: 5,
  restructuringReviews: 8,
};

export interface RegionalRisk {
  region: string;
  activeLoans: number;
  defaultProbabilityPct: number;
  avgSoh: number;
}

export const regionalRisk: RegionalRisk[] = [
  { region: "Varanasi", activeLoans: 412, defaultProbabilityPct: 14.2, avgSoh: 91.8 },
  { region: "Patna", activeLoans: 634, defaultProbabilityPct: 11.8, avgSoh: 93.4 },
  { region: "Kanpur", activeLoans: 518, defaultProbabilityPct: 10.5, avgSoh: 93.9 },
  { region: "Lucknow", activeLoans: 982, defaultProbabilityPct: 8.9, avgSoh: 95.1 },
  { region: "Kolkata", activeLoans: 805, defaultProbabilityPct: 8.1, avgSoh: 95.8 },
  { region: "Delhi NCR", activeLoans: 1505, defaultProbabilityPct: 6.4, avgSoh: 96.4 },
];

// Hero personas that recur across Risk Intelligence + Battery Monitoring + Case Workspace
export const heroPersonas = {
  mohan: {
    id: "drv-014", // Raju Kumar in batteries data — we'll re-slot as Mohan for the demo narrative
    batteryId: "BT-3567",
    name: "Mohan Sharma",
    city: "Prayagraj",
    dealer: "XYZ Battery Trading",
    loanId: "LN-2024-08932",
    loanStartDate: "2024-08-14",
    tenureMonths: 18,
    outstanding: 24680,
    sohPct: 82.3,
    sohTrend: "down" as const,
    dailyKm: 28,
    previousDailyKm: 65,
    emiOverdueDays: 9,
    offlineHours: 14,
    irregularChargingIn7d: 3,
    cds: 72,
    pci: 0.38,
    riskLevel: "high" as const,
    status: "IMMOBILIZATION ELIGIBLE",
  },
  rajesh: {
    id: "drv-001",
    batteryId: "BT-8983",
    name: "Rajesh Kumar",
    city: "Lucknow",
    dealer: "ABC Dealers",
    loanId: "LN-2024-04421",
    loanStartDate: "2024-04-20",
    tenureMonths: 18,
    outstanding: 6240,
    sohPct: 91.0,
    sohTrend: "steady" as const,
    dailyKm: 67,
    previousDailyKm: 64,
    emiOverdueDays: 0,
    offlineHours: 0.3,
    irregularChargingIn7d: 0,
    cds: 12,
    pci: 0.92,
    riskLevel: "low" as const,
    status: "ACTIVE",
  },
};

export const methodologyNotes = {
  delinquency:
    "Baseline: industry average 12.0% (Aug-2024). Measurement: NBFC EMI reconciliation over last 90 days. Period: Feb-Apr 2026.",
  collectionEfficiency:
    "Baseline: 79% (NBFC pre-telemetry). Computed as (EMIs collected within 7 days of due) / (EMIs due) over last 90 days.",
  recoveryRate:
    "Baseline: industry 50% (post-default recovery of principal). Measurement: recovered value / defaulted outstanding. Period: rolling 12 months.",
  preventedLoss:
    "Estimated as (atRiskAccounts × avgTicket × baselineDefaultRate) − (observed defaults × avgTicket). Demo value, for illustration.",
};
