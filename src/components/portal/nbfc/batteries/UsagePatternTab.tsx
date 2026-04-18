"use client";

import { type BatteryRow } from "@/data/portal/loans";
import { type Driver } from "@/data/portal/drivers";
import { MapPin, PauseCircle } from "lucide-react";

interface Props {
  row: BatteryRow;
  driver?: Driver;
}

function dailyKmSeries(avg: number, drop: boolean): number[] {
  const out: number[] = [];
  for (let i = 0; i < 30; i++) {
    const base = drop
      ? Math.max(0, avg * (1 - Math.min(0.6, i / 60)) + (Math.sin(i * 1.3) * 4 - 2))
      : avg + Math.sin(i * 1.1) * 5 - 2;
    out.push(Math.max(0, base));
  }
  return out;
}

export default function UsagePatternTab({ row, driver }: Props) {
  const drop = (driver?.risk.usageDropPct ?? 0) > 0.2;
  const series = dailyKmSeries(row.dailyKm30d, drop);
  const max = Math.max(...series, 1);

  return (
    <div className="space-y-4">
      <section className="rounded-lg bg-black/20 border border-white/10 p-5">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-gray-300">Daily KM · 30-day pattern</p>
          <p className="text-[10px] text-gray-500">Latest 7d avg {driver?.avgDailyKm7d ?? row.dailyKm30d} km</p>
        </div>
        <svg viewBox="0 0 300 90" className="w-full h-24" preserveAspectRatio="none">
          <defs>
            <linearGradient id="kmGrad" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
            </linearGradient>
          </defs>
          {(() => {
            const pts = series.map((v, i) => {
              const x = (i / (series.length - 1)) * 300;
              const y = 90 - (v / max) * 76 - 4;
              return [x, y] as const;
            });
            const line = pts.map(([x, y]) => `${x},${y.toFixed(1)}`).join(" ");
            const area = `0,90 ${line} 300,90`;
            return (
              <>
                <polyline points={area} fill="url(#kmGrad)" stroke="none" />
                <polyline
                  points={line}
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </>
            );
          })()}
        </svg>
        <p className="sr-only">
          Daily kilometres over 30 days, averaging around {row.dailyKm30d} km per day, {drop ? "with a declining trend" : "roughly steady"}.
        </p>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div className="rounded-lg bg-black/20 border border-white/10 p-3">
          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 flex items-center gap-1">
            <MapPin className="h-2.5 w-2.5" />
            Geo-shift
          </p>
          <p className="text-sm font-bold text-white">{driver?.risk.geoShiftFlag ? "Flagged · >100 km from onboarding" : "Within onboarding radius"}</p>
        </div>
        <div className="rounded-lg bg-black/20 border border-white/10 p-3">
          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 flex items-center gap-1">
            <PauseCircle className="h-2.5 w-2.5" />
            Idle days (7d)
          </p>
          <p className="text-sm font-bold text-white tabular-nums">{driver?.risk.idleDays7d ?? 0}</p>
        </div>
        <div className="rounded-lg bg-black/20 border border-white/10 p-3">
          <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">Offline hrs (7d)</p>
          <p className="text-sm font-bold text-white tabular-nums">{driver?.offlineHours7d.toFixed(1) ?? 0}</p>
        </div>
      </div>
    </div>
  );
}
