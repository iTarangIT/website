"use client";

import Link from "next/link";
import { AlertOctagon, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { alertCounts, priorityQueue, type AlertSeverity } from "@/data/portal/alerts";

const META: Record<AlertSeverity, { label: string; color: string; bg: string; icon: typeof AlertOctagon }> = {
  critical: { label: "Critical", color: "text-red-300", bg: "bg-red-500/10 border-red-500/30", icon: AlertOctagon },
  warning: { label: "Warning", color: "text-accent-amber", bg: "bg-accent-amber/10 border-accent-amber/30", icon: AlertTriangle },
  info: { label: "Info", color: "text-brand-200", bg: "bg-brand-500/10 border-brand-500/30", icon: Info },
};

export default function RealTimeAlertPanel() {
  return (
    <section
      className="rounded-xl bg-white/5 border border-white/10 p-4"
      role="status"
      aria-live="polite"
      aria-label="Real-time alert panel"
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Real-time alerts</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">Live from telemetry · click a tile to filter the table</p>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {(["critical", "warning", "info"] as AlertSeverity[]).map((sev) => {
          const m = META[sev];
          const Icon = m.icon;
          const latest = priorityQueue.filter((a) => a.severity === sev).slice(0, 1)[0];
          const href =
            sev === "critical"
              ? "/nbfc/batteries?severity=critical"
              : sev === "warning"
              ? "/nbfc/batteries?severity=warning"
              : "/nbfc/batteries";
          return (
            <Link
              key={sev}
              href={href}
              className={cn(
                "rounded-lg border p-3 hover:brightness-110 transition-all group",
                m.bg,
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <Icon className={cn("h-3.5 w-3.5", m.color)} />
                <p className={cn("text-[10px] uppercase tracking-wider font-bold", m.color)}>{m.label}</p>
              </div>
              <p className="text-2xl font-bold text-white tabular-nums">{alertCounts[sev]}</p>
              {latest && (
                <p className="text-[10px] text-gray-500 mt-1 truncate">Latest: {latest.title}</p>
              )}
            </Link>
          );
        })}
      </div>
    </section>
  );
}
