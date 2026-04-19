"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import BatteryRiskTable, {
  type SignalFilter,
  type SeverityFilter,
} from "@/components/portal/nbfc/batteries/BatteryRiskTable";
import CaseWorkspace from "@/components/portal/nbfc/batteries/CaseWorkspace";
import RealTimeAlertPanel from "@/components/portal/nbfc/batteries/RealTimeAlertPanel";
import ScoreExplainer from "@/components/portal/shared/ScoreExplainer";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";
import { allBatteryRows, type BatteryRow } from "@/data/portal/loans";

const VALID_SIGNALS: SignalFilter[] = ["all", "low-usage", "irregular-charging", "idle-2d", "geo-shift"];
const VALID_SEVERITIES: SeverityFilter[] = ["all", "critical", "warning", "info", "geo-variation"];

function parseSignal(v: string | null): SignalFilter {
  if (!v) return "all";
  return (VALID_SIGNALS as string[]).includes(v) ? (v as SignalFilter) : "all";
}

function parseSeverity(v: string | null): SeverityFilter {
  if (!v) return "all";
  return (VALID_SEVERITIES as string[]).includes(v) ? (v as SeverityFilter) : "all";
}

function BatteriesContent() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();

  const initialCaseId = searchParams.get("case");

  const [selected, setSelected] = useState<BatteryRow | null>(() => {
    if (!initialCaseId) return null;
    return (
      allBatteryRows.find((r) => r.driverId === initialCaseId || r.batteryId === initialCaseId) ?? null
    );
  });
  const [scoreRow, setScoreRow] = useState<BatteryRow | null>(null);
  const [scoreType, setScoreType] = useState<"cds" | "pci" | null>(null);

  const [signal, setSignal] = useState<SignalFilter>(() => parseSignal(searchParams.get("filter")));
  const [severity, setSeverity] = useState<SeverityFilter>(() => parseSeverity(searchParams.get("severity")));

  // Keep URL in sync — shallow replace so deep links work and reloads preserve filter
  useEffect(() => {
    const next = new URLSearchParams();
    if (signal !== "all") next.set("filter", signal);
    if (severity !== "all") next.set("severity", severity);
    const query = next.toString();
    const target = query ? `${pathname}?${query}` : pathname;
    router.replace(target, { scroll: false });
  }, [signal, severity, pathname, router]);

  const clearSignal = useCallback(() => setSignal("all"), []);
  const clearSeverity = useCallback(() => setSeverity("all"), []);

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Battery Monitoring</h1>
          <p className="text-sm text-gray-400 mt-1">
            Post-disbursement control · tiles and headers filter + sort the master table
          </p>
        </div>
        <DataFreshnessBadge />
      </div>

      <RealTimeAlertPanel severity={severity} onSelect={setSeverity} />

      <BatteryRiskTable
        onRowClick={setSelected}
        onBadgeClick={(r, type) => {
          setScoreRow(r);
          setScoreType(type);
        }}
        signal={signal}
        severity={severity}
        onClearSignal={clearSignal}
        onClearSeverity={clearSeverity}
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
