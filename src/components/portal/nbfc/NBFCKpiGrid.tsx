"use client";

import { Battery, IndianRupee, HeartPulse, TrendingDown, Target, AlertTriangle } from "lucide-react";
import KPICard from "@/components/dashboard-widget/KPICard";
import { portfolioHealth } from "@/data/portal/nbfc-extra-kpis";
import { countsByBand } from "@/data/portal/drivers";
import { fleetMockData } from "@/data/fleet-mock";

export default function NBFCKpiGrid() {
  const bands = countsByBand();
  const highRisk = bands.high + bands.medium;

  const kpis = [
    { label: "Financed Batteries", value: String(fleetMockData.totalBatteriesMonitored), icon: Battery, trend: "up" as const },
    { label: "Portfolio AUM", value: `₹${portfolioHealth.portfolioAumLakhs} L`, icon: IndianRupee, trend: "up" as const },
    { label: "Fleet SOH", value: `${portfolioHealth.fleetAvgSohPct}%`, icon: HeartPulse, trend: "neutral" as const },
    { label: "NPA % (90+ DPD)", value: `${portfolioHealth.npaPct}%`, icon: TrendingDown, trend: "down" as const },
    { label: "Collection Efficiency", value: `${portfolioHealth.collectionEfficiencyPct}%`, icon: Target, trend: "up" as const },
    { label: "High-Risk Assets", value: String(highRisk), icon: AlertTriangle, trend: "down" as const },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {kpis.map((kpi) => (
        <KPICard key={kpi.label} {...kpi} />
      ))}
    </div>
  );
}
