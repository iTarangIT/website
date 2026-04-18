"use client";

import { User, Battery as BatteryIcon, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Driver, RiskBand } from "@/data/portal/drivers";

interface Props {
  driver: Driver;
  onClick: () => void;
}

const BAND_STYLES: Record<RiskBand, { chip: string; accent: string; label: string }> = {
  low: { chip: "bg-accent-green/20 text-accent-green border-accent-green/30", accent: "text-accent-green", label: "LOW" },
  medium: { chip: "bg-accent-amber/20 text-accent-amber border-accent-amber/30", accent: "text-accent-amber", label: "MED" },
  high: { chip: "bg-red-500/20 text-red-400 border-red-500/30", accent: "text-red-400", label: "HIGH" },
};

export default function AssetCard({ driver, onClick }: Props) {
  const style = BAND_STYLES[driver.risk.riskBand];

  return (
    <button
      onClick={onClick}
      className="text-left rounded-xl bg-white/5 border border-white/10 p-4 hover:bg-white/10 hover:border-white/20 transition-all group flex flex-col gap-3"
    >
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center shrink-0">
          <User className="h-4 w-4 text-brand-300" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-white truncate">{driver.name}</p>
          <p className="text-[11px] text-gray-500 truncate">{driver.batterySerial} · {driver.batteryModelLabel}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded-full border text-[10px] font-bold tracking-wider",
          style.chip,
        )}>
          {style.label}
        </span>
        <span className="text-xs text-gray-400">
          CDS <span className={cn("font-bold tabular-nums", style.accent)}>{driver.risk.cdsScore}</span>
        </span>
      </div>

      <div className="flex items-center justify-between text-[11px] text-gray-500 pt-2 border-t border-white/5">
        <span className="flex items-center gap-1 min-w-0">
          <MapPin className="h-3 w-3 shrink-0" />
          <span className="truncate">{driver.city}</span>
        </span>
        <span>{driver.monthsDeployed} mo</span>
        <span className="flex items-center gap-1">
          <BatteryIcon className="h-3 w-3" />
          {driver.sohPct}%
        </span>
      </div>
    </button>
  );
}
