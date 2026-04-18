"use client";

import { useMemo, useSyncExternalStore } from "react";
import { getAuditEntries, subscribeToAudit } from "@/lib/audit-store";
import type { BatteryRow } from "@/data/portal/loans";
import { CheckCircle2, Clock, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  row: BatteryRow;
}

export default function ActionHistoryTab({ row }: Props) {
  const entries = useSyncExternalStore(
    (cb) => subscribeToAudit(cb),
    () => getAuditEntries(),
    () => getAuditEntries(),
  );

  const relevant = useMemo(
    () => entries.filter((e) => e.entity === row.batteryId || e.entity === row.imei || e.entity === row.loanId),
    [entries, row],
  );

  if (relevant.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 p-6 text-center text-xs text-gray-500">
        No actions have been taken on this account yet.
      </div>
    );
  }

  return (
    <ol className="space-y-2">
      {relevant.map((e) => {
        const StatusIcon = e.status === "completed" ? CheckCircle2 : e.status === "rejected" ? XCircle : Clock;
        const color = e.status === "completed" ? "text-accent-green" : e.status === "rejected" ? "text-red-400" : "text-accent-amber";
        return (
          <li key={e.id} className="flex items-start gap-3 rounded-lg bg-black/20 border border-white/10 p-3">
            <StatusIcon className={cn("h-4 w-4 mt-0.5 shrink-0", color)} />
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <p className="text-xs font-semibold text-white">{e.actionLabel}</p>
                <span className="text-[10px] text-gray-500 font-mono">{e.timestamp}</span>
              </div>
              <p className="text-[11px] text-gray-400 mt-0.5">
                {e.reasonCode} · by <span className="text-gray-300">{e.requestedBy}</span>
                {e.approvedBy && <> · approved by <span className="text-gray-300">{e.approvedBy}</span></>}
              </p>
              {e.details && <p className="text-[11px] text-gray-500 mt-1 italic border-l-2 border-white/10 pl-2">{e.details}</p>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
