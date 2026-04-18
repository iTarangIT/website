"use client";

import { cn } from "@/lib/utils";
import type { RiskBand } from "@/data/portal/drivers";

interface BucketSummary {
  band: RiskBand;
  count: number;
  totalOutstanding: number;
  totalDrivers: number;
}

interface Props {
  buckets: BucketSummary[];
  selected: RiskBand | "all";
  onSelect: (b: RiskBand | "all") => void;
}

const BUCKET_META: Record<RiskBand, { label: string; sub: string; color: string; bg: string; border: string; dot: string }> = {
  low: {
    label: "Low NPA Risk",
    sub: "Score 0–39",
    color: "text-accent-green",
    bg: "bg-accent-green/10",
    border: "border-accent-green/30",
    dot: "bg-accent-green",
  },
  medium: {
    label: "Medium NPA Risk",
    sub: "Score 40–69",
    color: "text-accent-amber",
    bg: "bg-accent-amber/10",
    border: "border-accent-amber/30",
    dot: "bg-accent-amber",
  },
  high: {
    label: "High NPA Risk",
    sub: "Score 70–100",
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    dot: "bg-red-500",
  },
};

function formatLakhs(n: number) {
  return `₹${(n / 100000).toFixed(2)} L`;
}

export default function RiskBucketsHeader({ buckets, selected, onSelect }: Props) {
  const totalDrivers = buckets[0]?.totalDrivers ?? 1;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {buckets.map((b) => {
        const meta = BUCKET_META[b.band];
        const isActive = selected === b.band;
        const pct = totalDrivers ? Math.round((b.count / totalDrivers) * 100) : 0;
        return (
          <button
            key={b.band}
            onClick={() => onSelect(isActive ? "all" : b.band)}
            className={cn(
              "text-left rounded-2xl border p-5 transition-all group",
              meta.bg,
              isActive ? `${meta.border} ring-2 ring-offset-0` : "border-white/10 hover:border-white/20",
              isActive && (b.band === "low" ? "ring-accent-green/40" : b.band === "medium" ? "ring-accent-amber/40" : "ring-red-500/40"),
            )}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gray-300">
                <span className={cn("h-2 w-2 rounded-full", meta.dot)} />
                {meta.label}
              </span>
              <span className="text-[10px] text-gray-500 font-mono">{meta.sub}</span>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-4xl font-bold text-white tabular-nums">{b.count}</p>
              <p className={cn("text-sm font-medium", meta.color)}>{pct}% of portfolio</p>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Outstanding: <span className="text-white font-semibold">{formatLakhs(b.totalOutstanding)}</span>
            </p>
            {isActive && (
              <p className="text-[10px] uppercase tracking-wider text-brand-300 font-semibold mt-3">
                ● Filter active
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}
