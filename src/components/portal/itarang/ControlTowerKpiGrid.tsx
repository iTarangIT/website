"use client";

import { Battery, Wifi, HeartPulse, TrendingDown, ShieldAlert, AlertOctagon } from "lucide-react";
import KPICard from "@/components/dashboard-widget/KPICard";
import { controlTowerKpi } from "@/data/portal/itarang-mock";

export default function ControlTowerKpiGrid() {
  const k = controlTowerKpi;
  const kpis = [
    { label: "Batteries Under Mgmt", value: String(k.batteriesUnderManagement), icon: Battery, trend: "up" as const },
    { label: "Online % (1h)", value: `${k.onlinePctLastHour}%`, icon: Wifi, trend: "up" as const },
    { label: "Fleet SOH", value: `${k.fleetAvgSoh}%`, icon: HeartPulse, trend: "neutral" as const },
    { label: "Assets < 80% SOH", value: String(k.assetsUnder80Soh), icon: TrendingDown, trend: "down" as const },
    { label: "High-Risk Financed", value: String(k.highRiskFinanced), icon: ShieldAlert, trend: "down" as const },
    { label: "Critical Tickets", value: String(k.openCriticalTickets), icon: AlertOctagon, trend: "neutral" as const },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {kpis.map((kpi) => (
        <KPICard key={kpi.label} {...kpi} />
      ))}
    </div>
  );
}
