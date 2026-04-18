"use client";

import { TrendingUp, TrendingDown, Minus, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: string;
  delta?: string;
  deltaDirection?: "up" | "down" | "neutral";
  deltaLabel?: string;
  icon?: LucideIcon;
  sparklineData?: number[];
  positiveIsDown?: boolean;
  onClick?: () => void;
  methodology?: string;
}

export default function KPIHeroCard({
  label,
  value,
  delta,
  deltaDirection = "neutral",
  deltaLabel,
  icon: Icon,
  sparklineData,
  positiveIsDown = false,
  onClick,
  methodology,
}: Props) {
  const Trend = deltaDirection === "up" ? TrendingUp : deltaDirection === "down" ? TrendingDown : Minus;
  const isGood =
    deltaDirection === "neutral"
      ? true
      : positiveIsDown
      ? deltaDirection === "down"
      : deltaDirection === "up";
  const deltaColor = deltaDirection === "neutral" ? "text-gray-400" : isGood ? "text-accent-green" : "text-red-400";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "text-left w-full rounded-xl bg-white/5 border border-white/10 p-5 transition-all",
        onClick && "hover:bg-white/10 hover:border-white/20 cursor-pointer",
      )}
      title={methodology}
    >
      <div className="flex items-center justify-between mb-2">
        <p className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold">{label}</p>
        {Icon && <Icon className="h-3.5 w-3.5 text-gray-500" />}
      </div>
      <p className="text-3xl font-bold text-white tracking-tight tabular-nums">{value}</p>
      {(delta || sparklineData) && (
        <div className="flex items-center justify-between gap-3 mt-3">
          {delta && (
            <span className={cn("inline-flex items-center gap-1 text-xs font-semibold", deltaColor)}>
              <Trend className="h-3 w-3" />
              {delta}
              {deltaLabel && <span className="text-gray-500 font-normal ml-1">{deltaLabel}</span>}
            </span>
          )}
          {sparklineData && <Sparkline data={sparklineData} positive={isGood} />}
        </div>
      )}
    </button>
  );
}

function Sparkline({ data, positive }: { data: number[]; positive: boolean }) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * 80;
      const y = 20 - ((v - min) / range) * 20;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={80} height={20} className="shrink-0" aria-hidden>
      <polyline
        points={pts}
        fill="none"
        stroke={positive ? "#10b981" : "#ef4444"}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
