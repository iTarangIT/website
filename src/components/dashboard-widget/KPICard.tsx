"use client";

import { cn } from "@/lib/utils";
import { type LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KPICardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  color?: string;
}

const trendConfig = {
  up: { Icon: TrendingUp, className: "text-accent-green" },
  down: { Icon: TrendingDown, className: "text-accent-pink" },
  neutral: { Icon: Minus, className: "text-gray-400" },
};

export default function KPICard({ label, value, icon: Icon, trend, color }: KPICardProps) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-4 flex flex-col gap-2 hover:bg-white/10 transition-colors">
      <div className="flex items-center justify-between">
        <div
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg",
            color || "bg-brand-500/20"
          )}
        >
          <Icon className="h-4 w-4 text-brand-300" />
        </div>
        {trend && (
          <span className={cn("flex items-center gap-0.5", trendConfig[trend].className)}>
            {(() => {
              const TrendIcon = trendConfig[trend].Icon;
              return <TrendIcon className="h-3.5 w-3.5" />;
            })()}
          </span>
        )}
      </div>
      <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
      <p className="text-xs text-gray-400 leading-tight">{label}</p>
    </div>
  );
}
