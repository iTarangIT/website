"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import BatteryRiskTable from "@/components/portal/nbfc/batteries/BatteryRiskTable";
import CaseWorkspace from "@/components/portal/nbfc/batteries/CaseWorkspace";
import RealTimeAlertPanel from "@/components/portal/nbfc/batteries/RealTimeAlertPanel";
import ScoreExplainer from "@/components/portal/shared/ScoreExplainer";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";
import { allBatteryRows, type BatteryRow } from "@/data/portal/loans";

function BatteriesContent() {
  const searchParams = useSearchParams();
  const caseId = searchParams.get("case");
  const severity = searchParams.get("severity");

  const [selected, setSelected] = useState<BatteryRow | null>(() => {
    if (!caseId) return null;
    return allBatteryRows.find((r) => r.driverId === caseId || r.batteryId === caseId) ?? null;
  });
  const [scoreRow, setScoreRow] = useState<BatteryRow | null>(null);
  const [scoreType, setScoreType] = useState<"cds" | "pci" | null>(null);

  const initialRiskFilter =
    severity === "critical" ? "very-high" : severity === "warning" ? "high" : "all";

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Battery Monitoring</h1>
          <p className="text-sm text-gray-400 mt-1">
            Post-disbursement control · click any row to open the Case Workspace
          </p>
        </div>
        <DataFreshnessBadge />
      </div>

      <RealTimeAlertPanel />

      <BatteryRiskTable
        onRowClick={setSelected}
        onBadgeClick={(r, type) => {
          setScoreRow(r);
          setScoreType(type);
        }}
        initialRiskFilter={initialRiskFilter as BatteryRow["riskLevel"] | "all"}
      />

      <CaseWorkspace row={selected} onClose={() => setSelected(null)} />

      {scoreRow && scoreType && (
        <ScoreExplainer
          open={!!scoreRow}
          onClose={() => {
            setScoreRow(null);
            setScoreType(null);
          }}
          type={scoreType}
          value={scoreType === "cds" ? scoreRow.cds : scoreRow.pci}
          entityLabel={`${scoreRow.batteryId} · ${scoreRow.customer}`}
          confidence={scoreRow.isInsufficientHistory ? "low" : "medium"}
        />
      )}

      <RegulatoryFooter />
    </div>
  );
}

export default function BatteriesPage() {
  return (
    <Suspense fallback={<div className="p-8 text-gray-500">Loading batteries…</div>}>
      <BatteriesContent />
    </Suspense>
  );
}
