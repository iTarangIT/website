"use client";

import { AlertOctagon, AlertTriangle, Info, MapPin, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { alertCounts } from "@/data/portal/alerts";
import { allBatteryRows } from "@/data/portal/loans";
import type { SeverityFilter } from "./BatteryRiskTable";

interface TileMeta {
  id: SeverityFilter;
  label: string;
  color: string;
  bg: string;
  icon: typeof AlertOctagon;
}

const TILES: TileMeta[] = [
  { id: "critical", label: "Critical", color: "text-red-300", bg: "bg-red-500/10 border-red-500/30", icon: AlertOctagon },
  { id: "warning", label: "Warning", color: "text-accent-amber", bg: "bg-accent-amber/10 border-accent-amber/30", icon: AlertTriangle },
  { id: "info", label: "Info", color: "text-brand-200", bg: "bg-brand-500/10 border-brand-500/30", icon: Info },
  { id: "geo-variation", label: "Geo variation", color: "text-red-300", bg: "bg-red-500/10 border-red-500/30", icon: MapPin },
];

interface Props {
  severity: SeverityFilter;
  onSelect: (s: SeverityFilter) => void;
}

export default function RealTimeAlertPanel({ severity, onSelect }: Props) {
  const geoCount = allBatteryRows.filter((r) => r.geoShiftFlag).length;

  const countOf = (id: SeverityFilter) => {
    switch (id) {
      case "critical":
        return alertCounts.critical;
      case "warning":
        return alertCounts.warning;
      case "info":
        return alertCounts.info;
      case "geo-variation":
        return geoCount;
      default:
        return 0;
    }
  };

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
          <p className="text-[11px] text-gray-500 mt-0.5">Live from telemetry · click a tile to filter the table below</p>
        </div>
        {severity !== "all" && (
          <button
            type="button"
            onClick={() => onSelect("all")}
            className="inline-flex items-center gap-1 text-[11px] text-gray-400 hover:text-white px-2 py-1 rounded-md bg-white/5 border border-white/10"
          >
            <X className="h-3 w-3" />
            Clear filter
          </button>
        )}
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {TILES.map((t) => {
          const Icon = t.icon;
          const active = severity === t.id;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => onSelect(active ? "all" : t.id)}
              aria-pressed={active}
              className={cn(
                "text-left rounded-lg border p-3 transition-all",
                t.bg,
                active ? "ring-2 ring-brand-400 scale-[1.02]" : "hover:brightness-110",
              )}
            >
              <div className="flex items-center gap-2 mb-2">
                <Icon className={cn("h-3.5 w-3.5", t.color)} />
                <p className={cn("text-[10px] uppercase tracking-wider font-bold", t.color)}>{t.label}</p>
              </div>
              <p className="text-2xl font-bold text-white tabular-nums">{countOf(t.id)}</p>
              <p className="text-[10px] text-gray-500 mt-1">
                {active ? "Showing these only — click to clear" : "Click to filter"}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
