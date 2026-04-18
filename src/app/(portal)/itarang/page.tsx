import Link from "next/link";
import { ArrowRight, Phone, Clock, Factory } from "lucide-react";
import ControlTowerKpiGrid from "@/components/portal/itarang/ControlTowerKpiGrid";
import AlertFeed from "@/components/portal/itarang/AlertFeed";
import Badge from "@/components/ui/Badge";
import { oemAnomalyRates, slaBreachQueue } from "@/data/portal/itarang-mock";
import { cn } from "@/lib/utils";

export default function ITarangDashboardPage() {
  const maxOem = Math.max(...oemAnomalyRates.map((r) => r.anomalyRatePct));

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-7">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Control Tower</h1>
          <p className="text-sm text-gray-400 mt-1">Enterprise visibility across telemetry, finance & service.</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="accent">
            <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-pink-400 animate-pulse" />
            Internal
          </Badge>
        </div>
      </div>

      <ControlTowerKpiGrid />

      {/* Leads CTA */}
      <Link
        href="/itarang/leads"
        className="group flex items-center justify-between gap-4 rounded-xl bg-gradient-to-r from-brand-500/20 via-brand-500/10 to-brand-500/5 border border-brand-500/30 px-5 py-4 hover:from-brand-500/30 hover:border-brand-500/50 transition-all"
      >
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-brand-500/30 border border-brand-500/40 flex items-center justify-center">
            <Phone className="h-4 w-4 text-brand-200" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Leads — AI dialer pipeline</p>
            <p className="text-xs text-gray-400">Scrape · AI-qualify · Hand off to sales. 12 active leads.</p>
          </div>
        </div>
        <ArrowRight className="h-5 w-5 text-brand-200 group-hover:translate-x-1 transition-transform" />
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AlertFeed />
        </div>

        <section className="rounded-xl bg-white/5 border border-white/10">
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
            <div>
              <h4 className="text-sm font-semibold text-gray-200">OEM anomaly rates</h4>
              <p className="text-xs text-gray-500 mt-0.5">30-day rolling</p>
            </div>
            <Factory className="h-4 w-4 text-gray-500" />
          </div>
          <div className="px-5 py-4 space-y-4">
            {oemAnomalyRates.map((row) => (
              <div key={row.oem} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-white">{row.oem}</p>
                    <p className="text-[11px] text-gray-500">{row.modelMix} · {row.deployed} units</p>
                  </div>
                  <span className={cn(
                    "font-bold tabular-nums",
                    row.anomalyRatePct > 4 ? "text-red-400" : row.anomalyRatePct > 2.5 ? "text-accent-amber" : "text-accent-green",
                  )}>
                    {row.anomalyRatePct}%
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      row.anomalyRatePct > 4 ? "bg-red-400" : row.anomalyRatePct > 2.5 ? "bg-accent-amber" : "bg-accent-green",
                    )}
                    style={{ width: `${(row.anomalyRatePct / maxOem) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* SLA breach queue */}
      <section className="rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div>
            <h4 className="text-sm font-semibold text-gray-200">SLA breach-imminent</h4>
            <p className="text-xs text-gray-500 mt-0.5">Service tickets close to SLA limit</p>
          </div>
          <Clock className="h-4 w-4 text-gray-500" />
        </div>
        <div className="divide-y divide-white/5">
          {slaBreachQueue.map((t) => (
            <div key={t.id} className="flex items-center justify-between gap-3 px-5 py-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-white truncate">{t.id} · {t.customer}</p>
                <p className="text-[11px] text-gray-500 truncate">{t.issue} · {t.city}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-bold tracking-wider",
                  t.severity === "Critical" ? "bg-red-500/20 text-red-400 border-red-500/30" : "bg-accent-amber/20 text-accent-amber border-accent-amber/30",
                )}>
                  {t.severity.toUpperCase()}
                </span>
                <span className={cn(
                  "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold tabular-nums",
                  t.slaRemainingMinutes < 120 ? "bg-red-500/20 text-red-400" : "bg-accent-amber/20 text-accent-amber",
                )}>
                  <Clock className="h-2.5 w-2.5" />
                  {t.slaRemainingMinutes < 60 ? `${t.slaRemainingMinutes}m` : `${(t.slaRemainingMinutes / 60).toFixed(1)}h`}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
