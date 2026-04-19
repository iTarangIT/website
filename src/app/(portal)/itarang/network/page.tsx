"use client";

import { PhoneCall, UserPlus, IndianRupee, Activity, Play, FileText } from "lucide-react";
import KPIHeroCard from "@/components/portal/shared/KPIHeroCard";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";
import NarrativeTile from "@/components/portal/shared/NarrativeTile";
import AICallerSection from "@/components/portal/itarang/ai-caller/AICallerSection";
import {
  networkKPIs,
  regionalDialerPerformance,
  regionalFunnels,
  recentCallRecordings,
  cpaBreakdown,
} from "@/data/portal/network-metrics";
import { cn } from "@/lib/utils";

const OUTCOME_STYLES = {
  hot: "bg-accent-green/15 text-accent-green border-accent-green/30",
  warm: "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  cold: "bg-brand-500/15 text-brand-200 border-brand-500/30",
  "do-not-call": "bg-red-500/15 text-red-300 border-red-500/30",
};

export default function PartnerNetworkPage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Partner Network Growth</h1>
          <p className="text-sm text-gray-400 mt-1">
            AI dialer performance · conversion by region · cost-per-acquisition
          </p>
        </div>
        <DataFreshnessBadge />
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPIHeroCard label="Leads acquired · 30d" value={networkKPIs.leadsAcquired30d.toLocaleString("en-IN")} icon={UserPlus} delta="+12.4%" deltaDirection="up" deltaLabel="MoM" />
        <KPIHeroCard label="AI pickup rate" value={`${networkKPIs.aiPickupRatePct}%`} icon={PhoneCall} sparklineData={[41, 43, 44, 45, 46, 47, 48]} />
        <KPIHeroCard label="Cost per acquisition" value={`₹${networkKPIs.costPerAcquisitionRupees}`} icon={IndianRupee} delta="-18%" deltaDirection="down" positiveIsDown deltaLabel="vs industry ₹420" />
        <KPIHeroCard label="Dialer uptime" value={`${networkKPIs.dialerUptimePct}%`} icon={Activity} />
      </div>

      <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/10">
          <h4 className="text-sm font-semibold text-gray-200">AI dialer performance by region</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">Pickup rate × call duration × conversion</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-[11px]">
            <caption className="sr-only">AI dialer key metrics segmented by region.</caption>
            <thead className="bg-black/30 text-gray-500">
              <tr>
                <th scope="col" aria-sort="none" className="text-left px-4 py-2 font-semibold">Region</th>
                <th scope="col" aria-sort="descending" className="text-right px-3 py-2 font-semibold">Pickup rate</th>
                <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">Avg duration</th>
                <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">Conversion</th>
                <th scope="col" aria-sort="none" className="text-right px-4 py-2 font-semibold">CPA</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {regionalDialerPerformance.map((r) => (
                <tr key={r.region} className="hover:bg-white/5">
                  <td className="px-4 py-2 text-white font-medium">{r.region}</td>
                  <td className={cn("px-3 py-2 tabular-nums text-right font-semibold", r.pickupRatePct > 50 ? "text-accent-green" : r.pickupRatePct > 45 ? "text-accent-amber" : "text-red-300")}>
                    {r.pickupRatePct}%
                  </td>
                  <td className="px-3 py-2 text-gray-300 tabular-nums text-right">
                    {Math.floor(r.avgCallDurationSec / 60)}:{String(r.avgCallDurationSec % 60).padStart(2, "0")}
                  </td>
                  <td className="px-3 py-2 text-gray-300 tabular-nums text-right">{r.conversionPct}%</td>
                  <td className="px-4 py-2 text-gray-200 tabular-nums text-right">₹{r.cpa}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 rounded-xl bg-white/5 border border-white/10">
          <div className="px-5 py-4 border-b border-white/10">
            <h4 className="text-sm font-semibold text-gray-200">Conversion funnel · by region</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">Stacked funnels for top 3 regions</p>
          </div>
          <div className="p-5 space-y-5">
            {regionalFunnels.map((f) => {
              const max = f.cold;
              return (
                <div key={f.region}>
                  <p className="text-xs font-semibold text-white mb-2">{f.region}</p>
                  <div className="space-y-1">
                    {[
                      { label: "Cold", value: f.cold, color: "bg-brand-500/50" },
                      { label: "Warm", value: f.warm, color: "bg-accent-amber/60" },
                      { label: "Hot", value: f.hot, color: "bg-accent-green/60" },
                      { label: "Converted", value: f.converted, color: "bg-accent-green" },
                    ].map((row) => (
                      <div key={row.label} className="flex items-center gap-3 text-[11px]">
                        <span className="text-gray-500 w-20 shrink-0">{row.label}</span>
                        <div className="flex-1 h-4 rounded bg-white/5 overflow-hidden">
                          <div className={cn("h-full", row.color)} style={{ width: `${(row.value / max) * 100}%` }} />
                        </div>
                        <span className="text-gray-300 tabular-nums w-14 text-right">{row.value.toLocaleString("en-IN")}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <section className="rounded-xl bg-white/5 border border-white/10">
          <div className="px-5 py-4 border-b border-white/10">
            <h4 className="text-sm font-semibold text-gray-200">CPA breakdown</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">Estimated cost per qualified lead</p>
          </div>
          <dl className="px-5 py-4 space-y-2 text-xs">
            <CPARow label="AI dialer cost per lead" value={`₹${cpaBreakdown.dialerCostPerLeadRupees}`} />
            <CPARow label="Manual follow-up" value={`₹${cpaBreakdown.manualFollowupCostRupees}`} />
            <CPARow label="Telemetry setup (amortized)" value={`₹${cpaBreakdown.telemetrySetupAmortizedRupees}`} />
            <CPARow label="Total CPA" value={`₹${cpaBreakdown.totalCpa}`} accent />
            <CPARow label="Industry average" value={`₹${cpaBreakdown.industryAverageCpa}`} muted />
          </dl>
          <p className="px-5 py-3 text-[10px] text-accent-green border-t border-white/10 bg-accent-green/5">
            {Math.round((1 - cpaBreakdown.totalCpa / cpaBreakdown.industryAverageCpa) * 100)}% below industry average — AI dialer + telemetry-qualified leads drive the delta.
          </p>
        </section>
      </div>

      <section className="rounded-xl bg-white/5 border border-white/10">
        <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-semibold text-gray-200">Recent AI calls</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">Recordings · demo placeholders</p>
          </div>
          <span className="text-[10px] text-gray-500 flex items-center gap-1">
            <FileText className="h-3 w-3" /> Full transcripts available in production
          </span>
        </div>
        <ul className="divide-y divide-white/5">
          {recentCallRecordings.map((c) => (
            <li key={c.id} className="flex items-start gap-3 px-5 py-3">
              <button
                type="button"
                aria-label={`Play call recording with ${c.leadName}`}
                className="shrink-0 h-9 w-9 rounded-full bg-brand-500/20 border border-brand-500/40 text-brand-200 hover:bg-brand-500/30 flex items-center justify-center"
              >
                <Play className="h-3.5 w-3.5" />
              </button>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-semibold text-white">{c.leadName}</p>
                  <span className="text-[10px] text-gray-500">{c.businessType} · {c.city}</span>
                </div>
                <p className="text-[11px] text-gray-400 italic mt-1 line-clamp-2">{c.transcriptSnippet}</p>
              </div>
              <div className="shrink-0 text-right text-[10px]">
                <span className={cn("inline-block px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider", OUTCOME_STYLES[c.outcome])}>
                  {c.outcome}
                </span>
                <p className="text-gray-500 mt-1">
                  {Math.floor(c.durationSec / 60)}:{String(c.durationSec % 60).padStart(2, "0")} · {c.timeAgo}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <NarrativeTile
        title="Network signal of the week"
        bullets={[
          "AI pickup rate in Varanasi (39.7%) is ~14 pp below Delhi — low pickup days cluster on Sundays. Shift scheduling weight to Mon–Wed.",
          "Conversion of hot leads to converted dropped to 27% in Kolkata — sales capacity issue, not lead quality. Queue expansion recommended.",
          "CPA of ₹180 is 57% below the ₹420 industry average; the delta is driven by telemetry pre-qualification.",
        ]}
      />

      <AICallerSection />

      <RegulatoryFooter />
    </div>
  );
}

function CPARow({ label, value, accent, muted }: { label: string; value: string; accent?: boolean; muted?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 pb-1.5">
      <dt className={cn("text-gray-400", muted && "italic")}>{label}</dt>
      <dd className={cn("font-bold tabular-nums", accent ? "text-accent-green" : muted ? "text-gray-500" : "text-white")}>{value}</dd>
    </div>
  );
}
