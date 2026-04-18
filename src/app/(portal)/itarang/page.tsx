"use client";

import Link from "next/link";
import { Network, Activity, Wifi, Bell, ArrowRight } from "lucide-react";
import { ecosystemKPIs, nbfcPartners } from "@/data/portal/ecosystem";
import KPIHeroCard from "@/components/portal/shared/KPIHeroCard";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";

export default function ITarangEcosystemPage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Ecosystem Overview</h1>
          <p className="text-sm text-gray-400 mt-1">Cross-NBFC platform oversight · iTarang Platform Admin</p>
        </div>
        <DataFreshnessBadge />
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPIHeroCard label="Connected NBFCs" value={String(ecosystemKPIs.connectedNBFCs)} icon={Network} />
        <KPIHeroCard label="Total portfolio" value={`₹${ecosystemKPIs.totalPortfolioCr} Cr`} icon={Activity} />
        <KPIHeroCard label="Batteries under mgmt" value={ecosystemKPIs.totalBatteries.toLocaleString("en-IN")} />
        <KPIHeroCard label="Platform uptime" value={`${ecosystemKPIs.platformUptimePct}%`} icon={Wifi} />
      </div>

      <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/10">
          <h4 className="text-sm font-semibold text-gray-200">Cross-NBFC comparison</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">Key metrics per partner</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <caption className="sr-only">Performance comparison across partner NBFCs.</caption>
            <thead className="bg-black/30 text-gray-500">
              <tr>
                <th scope="col" className="text-left px-4 py-2 font-semibold">NBFC</th>
                <th scope="col" className="text-right px-3 py-2 font-semibold">Portfolio (₹ Cr)</th>
                <th scope="col" className="text-right px-3 py-2 font-semibold">Active loans</th>
                <th scope="col" className="text-right px-3 py-2 font-semibold">Delinquency</th>
                <th scope="col" className="text-right px-3 py-2 font-semibold">Recovery rate</th>
                <th scope="col" className="text-right px-3 py-2 font-semibold">Avg CDS</th>
                <th scope="col" className="text-right px-4 py-2 font-semibold">Online share</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {nbfcPartners.map((n) => (
                <tr key={n.id} className="hover:bg-white/5">
                  <td className="px-4 py-2 text-white font-medium">{n.name}</td>
                  <td className="px-3 py-2 text-gray-300 tabular-nums text-right">{n.portfolioCr}</td>
                  <td className="px-3 py-2 text-gray-300 tabular-nums text-right">{n.activeLoans.toLocaleString("en-IN")}</td>
                  <td className={"px-3 py-2 tabular-nums text-right font-semibold " + (n.delinquencyRatePct > 10 ? "text-red-300" : n.delinquencyRatePct > 9 ? "text-accent-amber" : "text-accent-green")}>
                    {n.delinquencyRatePct}%
                  </td>
                  <td className="px-3 py-2 text-accent-green tabular-nums text-right font-semibold">{n.recoveryRatePct}%</td>
                  <td className="px-3 py-2 text-gray-300 tabular-nums text-right">{n.avgCds}</td>
                  <td className="px-4 py-2 text-gray-300 tabular-nums text-right">{n.onlineSharePct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <PlatformTile label="API latency" value={`${ecosystemKPIs.apiLatencyMs}ms`} good={ecosystemKPIs.apiLatencyMs < 200} />
        <PlatformTile label="IoT connectivity" value={`${ecosystemKPIs.iotConnectivityPct}%`} good={ecosystemKPIs.iotConnectivityPct > 90} />
        <PlatformTile label="Alert volume 24h" value={ecosystemKPIs.alertVolume24h.toLocaleString("en-IN")} good={ecosystemKPIs.alertVolume24h < 5000} icon={Bell} />
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/itarang/auction"
          className="group rounded-xl bg-gradient-to-r from-brand-500/20 via-brand-500/10 to-brand-500/5 border border-brand-500/30 px-5 py-4 flex items-center justify-between hover:border-brand-500/50 transition-colors"
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-brand-200">Admin Power</p>
            <p className="text-sm text-white font-semibold mt-1">Auction Control Centre</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Extend/reduce time · set reserve · approve winners</p>
          </div>
          <ArrowRight className="h-5 w-5 text-brand-200 group-hover:translate-x-0.5 transition-transform" />
        </Link>
        <Link
          href="/itarang/risk-engine"
          className="group rounded-xl bg-gradient-to-r from-accent-amber/20 via-accent-amber/10 to-accent-amber/5 border border-accent-amber/30 px-5 py-4 flex items-center justify-between hover:border-accent-amber/50 transition-colors"
        >
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-accent-amber">Admin Power</p>
            <p className="text-sm text-white font-semibold mt-1">Risk Rule Engine</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Tune CDS/PCI/usage thresholds · dual approval + MFA</p>
          </div>
          <ArrowRight className="h-5 w-5 text-accent-amber group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </div>

      <RegulatoryFooter />
    </div>
  );
}

function PlatformTile({
  label,
  value,
  good,
  icon: Icon,
}: {
  label: string;
  value: string;
  good: boolean;
  icon?: typeof Bell;
}) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-[11px] uppercase tracking-wider text-gray-500 font-semibold">{label}</p>
        {Icon && <Icon className="h-3 w-3 text-gray-500" />}
      </div>
      <p className={"text-2xl font-bold tabular-nums " + (good ? "text-accent-green" : "text-accent-amber")}>{value}</p>
    </div>
  );
}
