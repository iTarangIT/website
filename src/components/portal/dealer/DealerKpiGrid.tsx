"use client";

import { Battery, Package, ReceiptIndianRupee, Wrench } from "lucide-react";
import KPICard from "@/components/dashboard-widget/KPICard";
import { dealerKpi } from "@/data/portal/dealer-mock";

export default function DealerKpiGrid() {
  const kpis = [
    {
      label: "Active Batteries in Field",
      value: String(dealerKpi.activeBatteriesDeployed),
      icon: Battery,
      trend: "up" as const,
    },
    {
      label: "Inventory In Stock",
      value: String(dealerKpi.inventoryInStock),
      icon: Package,
      trend: "neutral" as const,
    },
    {
      label: "EMI Collected MTD",
      value: `₹${dealerKpi.emiCollectedMtdLakhs} L`,
      icon: ReceiptIndianRupee,
      trend: "up" as const,
    },
    {
      label: "Open Service Tickets",
      value: `${dealerKpi.openServiceTickets} (${dealerKpi.criticalTickets} critical)`,
      icon: Wrench,
      trend: "neutral" as const,
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {kpis.map((kpi) => (
        <KPICard key={kpi.label} {...kpi} />
      ))}
    </div>
  );
}
