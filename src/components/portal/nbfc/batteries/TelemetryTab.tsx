"use client";

import { type BatteryRow } from "@/data/portal/loans";
import { type Driver } from "@/data/portal/drivers";
import { Battery, Zap, Thermometer, Clock } from "lucide-react";

interface Props {
  row: BatteryRow;
  driver?: Driver;
}

// Deterministic synthetic 30-day SOH series based on current SOH + trend
function sohSeries(sohPct: number, trend: BatteryRow["sohTrend"]): number[] {
  const dir = trend === "down" ? -1 : trend === "up" ? 1 : 0;
  const amplitude = trend === "steady" ? 0.4 : 2.8;
  const out: number[] = [];
  for (let d = 29; d >= 0; d--) {
    const mix = (29 - d) / 29;
    const noise = Math.sin(d * 0.7 + sohPct * 0.1) * 0.3;
    out.push(sohPct - dir * amplitude * mix + noise);
  }
  return out;
}

export default function TelemetryTab({ row, driver }: Props) {
  const series = sohSeries(row.sohPct, row.sohTrend);
  const min = Math.min(...series);
  const max = Math.max(...series);
  const range = max - min || 1;

  return (
    <div className="space-y-4">
      <section className="rounded-lg bg-black/20 border border-white/10 p-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
            <Battery className="h-3.5 w-3.5" /> SOH · 30-day trend
          </p>
          <p className="text-[10px] text-gray-500">
            Range {min.toFixed(1)}% – {max.toFixed(1)}% · latest {row.sohPct}%
          </p>
        </div>
        <svg viewBox="0 0 300 90" className="w-full h-24" preserveAspectRatio="none">
          <defs>
            <linearGradient id="sohGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor={row.sohTrend === "down" ? "#ef4444" : "#10b981"} stopOpacity={0.35} />
              <stop offset="100%" stopColor={row.sohTrend === "down" ? "#ef4444" : "#10b981"} stopOpacity={0} />
            </linearGradient>
          </defs>
          {(() => {
            const pts = series.map((v, i) => {
              const x = (i / (series.length - 1)) * 300;
              const y = 90 - ((v - min) / range) * 76 - 4;
              return [x, y] as const;
            });
            const line = pts.map(([x, y]) => `${x},${y.toFixed(1)}`).join(" ");
            const area = `0,90 ${line} 300,90`;
            return (
              <>
                <polyline points={area} fill="url(#sohGrad)" stroke="none" />
                <polyline
                  points={line}
                  fill="none"
                  stroke={row.sohTrend === "down" ? "#ef4444" : "#10b981"}
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </>
            );
          })()}
        </svg>
        <p className="sr-only">
          State-of-Health over 30 days: ranges from {min.toFixed(1)} to {max.toFixed(1)} percent, ending at {row.sohPct} percent.
        </p>
      </section>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <Tile icon={Zap} label="SOC" value={`${40 + Math.round(Math.abs(Math.sin(row.sohPct * 0.3) * 50))}%`} />
        <Tile icon={Battery} label="Charge cycles" value={String(driver?.chargeCycles ?? "—")} />
        <Tile icon={Thermometer} label="Temp stress 7d" value={`${driver?.tempStressMinutes7d ?? 0} min`} />
        <Tile icon={Clock} label="Last seen" value={row.immobilized ? "Immobilized · 2 hrs ago" : "4 min ago"} />
      </div>

      <div className="rounded-lg bg-black/20 border border-white/10 p-4 text-xs">
        <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-2">Warranty</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-gray-300">
          <div>Status: <span className="text-white">Active</span></div>
          <div>Expires: <span className="text-white">{row.customer === "Mohan Sharma" ? "2027-02-14" : "2027-08-22"}</span></div>
          <div>Cycles remaining: <span className="text-white">~{2000 - (driver?.chargeCycles ?? 300)}</span></div>
        </div>
      </div>
    </div>
  );
}

function Tile({ icon: Icon, label, value }: { icon: typeof Battery; label: string; value: string }) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 flex items-center gap-1">
        <Icon className="h-2.5 w-2.5" />
        {label}
      </p>
      <p className="text-sm font-bold text-white tabular-nums">{value}</p>
    </div>
  );
}
