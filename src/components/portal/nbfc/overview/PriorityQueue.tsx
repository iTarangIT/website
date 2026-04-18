"use client";

import { useState } from "react";
import Link from "next/link";
import { AlertOctagon, AlertTriangle, Info, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { priorityQueue, alertCounts, type AlertSeverity } from "@/data/portal/alerts";

const SEVERITY_META: Record<AlertSeverity, { label: string; color: string; icon: typeof AlertOctagon; dot: string }> = {
  critical: { label: "Critical", color: "text-red-300", icon: AlertOctagon, dot: "bg-red-400" },
  warning: { label: "Warning", color: "text-accent-amber", icon: AlertTriangle, dot: "bg-accent-amber" },
  info: { label: "Info", color: "text-brand-300", icon: Info, dot: "bg-brand-400" },
};

export default function PriorityQueue() {
  const [expanded, setExpanded] = useState<Record<AlertSeverity, boolean>>({ critical: true, warning: false, info: false });
  const totalCount = alertCounts.critical + alertCounts.warning + alertCounts.info;

  const grouped: Record<AlertSeverity, typeof priorityQueue> = {
    critical: priorityQueue.filter((a) => a.severity === "critical"),
    warning: priorityQueue.filter((a) => a.severity === "warning"),
    info: priorityQueue.filter((a) => a.severity === "info"),
  };

  const countMap: Record<AlertSeverity, number> = alertCounts;

  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Needs attention now</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">{totalCount} active alerts · grouped by severity</p>
        </div>
      </div>

      <div className="divide-y divide-white/5">
        {(["critical", "warning", "info"] as AlertSeverity[]).map((sev) => {
          const meta = SEVERITY_META[sev];
          const rows = grouped[sev];
          const Icon = meta.icon;
          const isOpen = expanded[sev];
          return (
            <div key={sev}>
              <button
                onClick={() => setExpanded((prev) => ({ ...prev, [sev]: !prev[sev] }))}
                className="w-full flex items-center justify-between gap-3 px-5 py-3 hover:bg-white/5 transition-colors text-left"
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-3">
                  {isOpen ? <ChevronDown className="h-3.5 w-3.5 text-gray-500" /> : <ChevronRight className="h-3.5 w-3.5 text-gray-500" />}
                  <span className={cn("h-2 w-2 rounded-full", meta.dot)} />
                  <Icon className={cn("h-4 w-4", meta.color)} />
                  <p className="text-sm font-semibold text-white">
                    <span className="tabular-nums">{countMap[sev]}</span> {meta.label}
                  </p>
                </div>
                <span className="text-[11px] text-gray-500 uppercase tracking-wider font-semibold">
                  {isOpen ? "Hide" : "Expand"}
                </span>
              </button>
              {isOpen && (
                <div className="divide-y divide-white/5 bg-black/20">
                  {rows.slice(0, 5).map((a) => (
                    <div key={a.id} className="flex items-start gap-3 px-5 py-3">
                      <span className={cn("h-1.5 w-1.5 rounded-full mt-2 shrink-0", meta.dot)} />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-white truncate">{a.title}</p>
                        <p className="text-[11px] text-gray-500 truncate">{a.entityLabel} · {a.city} · {a.timeAgo}</p>
                      </div>
                      {a.actionHref && (
                        <Link
                          href={a.actionHref}
                          className="shrink-0 px-2.5 py-1 text-[11px] font-semibold rounded-md bg-brand-500/15 border border-brand-500/30 text-brand-200 hover:bg-brand-500/25"
                        >
                          View case
                        </Link>
                      )}
                    </div>
                  ))}
                  {rows.length > 5 && (
                    <Link
                      href={`/nbfc/batteries?severity=${sev}`}
                      className="block px-5 py-2.5 text-[11px] font-semibold text-brand-300 hover:text-brand-200 text-center"
                    >
                      View all {countMap[sev]} {meta.label.toLowerCase()} alerts →
                    </Link>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
