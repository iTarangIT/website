"use client";

import { fleetMockData } from "@/data/fleet-mock";
import KPICard from "./KPICard";
import Badge from "@/components/ui/Badge";
import {
  Battery,
  HeartPulse,
  Route,
  Zap,
  ArrowUpCircle,
  RefreshCw,
  MapPin,
} from "lucide-react";

const kpis = [
  {
    label: "Total Batteries",
    value: String(fleetMockData.totalBatteriesMonitored),
    icon: Battery,
    trend: "up" as const,
  },
  {
    label: "Fleet SOH",
    value: `${fleetMockData.fleetAvgSOH}%`,
    icon: HeartPulse,
    trend: "up" as const,
  },
  {
    label: "Avg Daily Km",
    value: String(fleetMockData.avgDailyKm),
    icon: Route,
    trend: "neutral" as const,
  },
  {
    label: "Charge Cycles",
    value: String(fleetMockData.avgChargeCycles),
    icon: Zap,
    trend: "up" as const,
  },
  {
    label: "Fleet Uptime",
    value: `${fleetMockData.fleetUptimePercent}%`,
    icon: ArrowUpCircle,
    trend: "up" as const,
  },
];

export default function FleetDashboardWidget() {
  const maxSOHCount = Math.max(...fleetMockData.sohDistribution.map((d) => d.count));

  return (
    <section className="py-16 md:py-24 bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-gray-950 shadow-2xl overflow-hidden border border-gray-800">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-white">
                Live Fleet Intelligence
              </h3>
              <Badge className="bg-accent-green/20 text-accent-green border border-accent-green/30 animate-pulse">
                <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-accent-green" />
                LIVE
              </Badge>
            </div>
            <button
              className="text-gray-500 hover:text-gray-300 transition-colors"
              aria-label="Refresh data"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>

          {/* KPI Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 p-6">
            {kpis.map((kpi) => (
              <KPICard key={kpi.label} {...kpi} />
            ))}
          </div>

          {/* Bottom row: SOH Distribution + Active Cities */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 px-6 pb-6">
            {/* SOH Distribution */}
            <div className="rounded-xl bg-white/5 border border-white/10 p-5">
              <h4 className="text-sm font-semibold text-gray-300 mb-4">
                SOH Distribution
              </h4>
              <div className="space-y-3">
                {fleetMockData.sohDistribution.map((bucket) => (
                  <div key={bucket.range} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-16 shrink-0 text-right">
                      {bucket.range}
                    </span>
                    <div className="flex-1 h-5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${(bucket.count / maxSOHCount) * 100}%`,
                          backgroundColor: bucket.color,
                        }}
                      />
                    </div>
                    <span className="text-xs font-medium text-gray-300 w-8 text-right">
                      {bucket.count}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Active Cities */}
            <div className="rounded-xl bg-white/5 border border-white/10 p-5">
              <h4 className="text-sm font-semibold text-gray-300 mb-4">
                Active Cities
              </h4>
              <ul className="space-y-3">
                {fleetMockData.activeCities.map((city) => (
                  <li
                    key={city.name}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <MapPin className="h-3.5 w-3.5 text-brand-400" />
                      <span className="text-sm text-gray-300">{city.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-white">
                      {city.count}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-3 border-t border-gray-800 bg-gray-950/50">
            <p className="text-xs text-gray-500 flex items-center gap-1.5">
              <RefreshCw className="h-3 w-3" />
              Last updated 5 min ago
            </p>
            <p className="text-xs text-gray-600">
              iTarang Fleet Dashboard v1.0
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
