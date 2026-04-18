"use client";

import { useExecutiveMode } from "@/components/portal/shared/ExecutiveSummaryToggle";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RecoveryPipelineStrip from "@/components/portal/nbfc/recovery/RecoveryPipelineStrip";
import EvaluationForm from "@/components/portal/nbfc/recovery/EvaluationForm";
import AuctionMarketplace from "@/components/portal/nbfc/recovery/AuctionMarketplace";
import SettlementTable from "@/components/portal/nbfc/recovery/SettlementTable";
import BuybackRequests from "@/components/portal/nbfc/recovery/BuybackRequests";

export default function RecoveryPage() {
  const { executiveMode } = useExecutiveMode();

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Recovery &amp; Auction</h1>
          <p className="text-sm text-gray-400 mt-1">Act 3 · close the loop · recycle capital through compliant auctions</p>
        </div>
        <DataFreshnessBadge />
      </header>

      <RecoveryPipelineStrip />

      {!executiveMode && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <div className="xl:col-span-2">
            <AuctionMarketplace />
          </div>
          <EvaluationForm />
        </div>
      )}

      <SettlementTable />

      {!executiveMode && <BuybackRequests />}

      <p className="text-[10px] text-gray-500 border-t border-white/10 pt-4">
        Recovery workflows comply with RBI Digital Lending Directions 2025. Every auction action + bid is logged to the audit trail.
      </p>
    </div>
  );
}
