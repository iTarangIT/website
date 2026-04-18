"use client";

import { useState } from "react";
import { UserPlus, Package, BatteryPlus, Wrench } from "lucide-react";
import DealerKpiGrid from "@/components/portal/dealer/DealerKpiGrid";
import CollectionsPreview from "@/components/portal/dealer/CollectionsPreview";
import ServiceQueuePreview from "@/components/portal/dealer/ServiceQueuePreview";
import InventoryTable from "@/components/portal/dealer/InventoryTable";
import Badge from "@/components/ui/Badge";

const QUICK_ACTIONS = [
  { id: "add-consumer", label: "Add Consumer", icon: UserPlus, toast: "Consumer onboarding started" },
  { id: "receive-inv", label: "Receive Inventory", icon: Package, toast: "Inventory receipt form opened" },
  { id: "deploy-bat", label: "Deploy Battery", icon: BatteryPlus, toast: "Deployment flow started" },
  { id: "create-ticket", label: "Create Service Ticket", icon: Wrench, toast: "Service ticket created (demo)" },
];

export default function DealerDashboardPage() {
  const [toast, setToast] = useState<string | null>(null);
  const fire = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-7">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Dealer Workspace</h1>
          <p className="text-sm text-gray-400 mt-1">Sharma E-Motors · Delhi NCR</p>
        </div>
        <Badge variant="success">
          <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-accent-green animate-pulse" />
          Operational
        </Badge>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {QUICK_ACTIONS.map((a) => {
          const Icon = a.icon;
          return (
            <button
              key={a.id}
              onClick={() => fire(a.toast)}
              className="flex items-center justify-center gap-2 rounded-xl bg-brand-500/10 border border-brand-500/20 px-3 py-3 text-xs font-semibold text-brand-200 hover:bg-brand-500/20 transition-colors"
            >
              <Icon className="h-4 w-4" />
              {a.label}
            </button>
          );
        })}
      </div>

      <DealerKpiGrid />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <CollectionsPreview />
        </div>
        <ServiceQueuePreview />
      </div>

      <InventoryTable />

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 border border-white/10 text-white text-xs px-3.5 py-2 rounded-lg shadow-xl z-50">
          {toast}
        </div>
      )}
    </div>
  );
}
