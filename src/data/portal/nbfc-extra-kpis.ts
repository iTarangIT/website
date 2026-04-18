export interface DPDBucket {
  label: string;
  count: number;
  pctOfPortfolio: number;
  outstandingLakhs: number;
  color: string;
}

export const dpdBuckets: DPDBucket[] = [
  { label: "Current (0 DPD)", count: 118, pctOfPortfolio: 77.6, outstandingLakhs: 52.4, color: "#10b981" },
  { label: "1–7 days", count: 18, pctOfPortfolio: 11.8, outstandingLakhs: 8.6, color: "#38bdf8" },
  { label: "8–30 days", count: 11, pctOfPortfolio: 7.2, outstandingLakhs: 5.2, color: "#fbbf24" },
  { label: "30+ days", count: 5, pctOfPortfolio: 3.3, outstandingLakhs: 2.8, color: "#ef4444" },
];

export const riskBandDistribution = [
  { band: "Low (0–20)", count: 108, color: "#10b981" },
  { band: "Medium (21–40)", count: 26, color: "#38bdf8" },
  { band: "High (41–60)", count: 12, color: "#fbbf24" },
  { band: "Very High (61–100)", count: 6, color: "#ef4444" },
];

export const nbfcMonthlyFinancial = {
  disbursedThisMonthLakhs: 18.4,
  disbursedDeltaPct: 12.5,
  collectedThisMonthLakhs: 11.2,
  collectedDeltaPct: 4.8,
  overdueOutstandingLakhs: 2.8,
  overdueDeltaPct: -8.2,
};

export const portfolioHealth = {
  portfolioAumLakhs: 74.5,
  fleetAvgSohPct: 94.2,
  npaPct: 1.6,
  npaTargetPct: 2.0,
  collectionEfficiencyPct: 96.8,
  averageCdsScore: 18,
  avgPci: 0.88,
};

export const telemetryAlerts = {
  usageDropCount: 9,
  geoShiftCount: 4,
  offlineGt48hCount: 3,
  immobilizationPending: 2,
};

export const highRiskPreview: { id: string; name: string; city: string; dpd: number; cds: number }[] = [
  { id: "drv-015", name: "Guddu Yadav", city: "Varanasi", dpd: 54, cds: 91 },
  { id: "drv-014", name: "Raju Kumar", city: "Delhi NCR", dpd: 42, cds: 82 },
  { id: "drv-025", name: "Jai Prakash", city: "Lucknow", dpd: 38, cds: 76 },
];
