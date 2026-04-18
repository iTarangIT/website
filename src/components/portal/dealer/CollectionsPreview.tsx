"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { dealerEMIs, dealerKpi, type EMIRow } from "@/data/portal/dealer-mock";
import { formatCurrency } from "@/lib/utils";

type Filter = "all" | "due-today" | "overdue" | "next-7-days";

const STATUS_STYLES: Record<EMIRow["status"], string> = {
  Overdue: "bg-red-500/20 text-red-400 border-red-500/30",
  "Due Today": "bg-accent-amber/20 text-accent-amber border-accent-amber/30",
  Upcoming: "bg-brand-500/20 text-brand-300 border-brand-500/30",
  Paid: "bg-accent-green/20 text-accent-green border-accent-green/30",
};

export default function CollectionsPreview() {
  const [filter, setFilter] = useState<Filter>("all");
  const [toast, setToast] = useState<string | null>(null);

  const filtered = dealerEMIs.filter((row) => {
    if (filter === "all") return true;
    if (filter === "due-today") return row.status === "Due Today";
    if (filter === "overdue") return row.status === "Overdue";
    if (filter === "next-7-days") return row.status === "Upcoming";
    return true;
  });

  const action = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2200);
  };

  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Collections</h4>
          <p className="text-xs text-gray-500 mt-0.5">
            Collection efficiency this month: <span className="text-accent-green font-semibold">{dealerKpi.emiCollectionPct}%</span>
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          {(["all", "due-today", "overdue", "next-7-days"] as Filter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-2.5 py-1 rounded-md transition-colors capitalize",
                filter === f ? "bg-brand-500 text-white" : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10",
              )}
            >
              {f.replaceAll("-", " ")}
            </button>
          ))}
        </div>
      </div>
      <div className="divide-y divide-white/5">
        {filtered.map((row) => (
          <div key={`${row.consumer}-${row.battery}`} className="flex items-center justify-between gap-3 px-5 py-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">{row.consumer}</p>
              <p className="text-[11px] text-gray-500">{row.battery} · Due {row.dueDate}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-white tabular-nums">{formatCurrency(row.amount)}</span>
              <span className={cn("inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold tracking-wider", STATUS_STYLES[row.status])}>
                {row.status.toUpperCase()}
                {row.dpd !== undefined && ` · ${row.dpd}d`}
              </span>
              <div className="hidden sm:flex items-center gap-1">
                <button
                  onClick={() => action(`Reminder sent to ${row.consumer}`)}
                  className="text-[11px] font-medium px-2 py-1 rounded-md bg-brand-500/10 text-brand-300 hover:bg-brand-500/20"
                >
                  Remind
                </button>
                <button
                  onClick={() => action(`Escalated ${row.consumer} to NBFC`)}
                  className="text-[11px] font-medium px-2 py-1 rounded-md bg-white/5 text-gray-300 hover:bg-white/10"
                >
                  Escalate
                </button>
              </div>
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="px-5 py-6 text-center text-xs text-gray-500">No accounts match this filter.</div>
        )}
      </div>
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 border border-white/10 text-white text-xs px-3.5 py-2 rounded-lg shadow-xl z-50">
          {toast}
        </div>
      )}
    </section>
  );
}
