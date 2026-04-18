"use client";

import { narrativeHeader, whatChangedThisWeek, recentActions } from "@/data/portal/portfolio";
import HeroKPIRow from "@/components/portal/nbfc/overview/HeroKPIRow";
import ThreeActStrip from "@/components/portal/nbfc/overview/ThreeActStrip";
import PriorityQueue from "@/components/portal/nbfc/overview/PriorityQueue";
import RegionalRiskChart from "@/components/portal/nbfc/overview/RegionalRiskChart";
import NarrativeTile from "@/components/portal/shared/NarrativeTile";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import { useExecutiveMode } from "@/components/portal/shared/ExecutiveSummaryToggle";
import Link from "next/link";

export default function NBFCOverviewPage() {
  const { executiveMode } = useExecutiveMode();

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-7">
      {/* Narrative header */}
      <header className="space-y-2">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <h1 className="text-2xl font-semibold text-white tracking-tight">Portfolio Command Centre</h1>
          <DataFreshnessBadge />
        </div>
        <p className="text-lg text-gray-300 leading-relaxed max-w-3xl">{narrativeHeader}</p>
      </header>

      <HeroKPIRow />

      <ThreeActStrip />

      {!executiveMode && <PriorityQueue />}

      <NarrativeTile title="What changed this week" bullets={whatChangedThisWeek} />

      {!executiveMode && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2">
            <RegionalRiskChart />
          </div>

          <section className="rounded-xl bg-white/5 border border-white/10">
            <div className="px-5 py-4 border-b border-white/10">
              <h4 className="text-sm font-semibold text-gray-200">Recently completed actions</h4>
              <p className="text-[11px] text-gray-500 mt-0.5">Transparency strip · clickable</p>
            </div>
            <ul className="divide-y divide-white/5">
              {[
                { label: "Re-mobilizations", value: recentActions.reMobilizations, href: "/nbfc/audit?type=remobilization" },
                { label: "Field visits", value: recentActions.fieldVisits, href: "/nbfc/audit?type=field-visit" },
                { label: "Restructuring reviews", value: recentActions.restructuringReviews, href: "/nbfc/audit?type=restructuring-review" },
              ].map((row) => (
                <li key={row.label}>
                  <Link
                    href={row.href}
                    className="flex items-center justify-between px-5 py-3 text-sm hover:bg-white/5 transition-colors"
                  >
                    <span className="text-gray-300">{row.label}</span>
                    <span className="text-white font-semibold tabular-nums">{row.value}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}

      {executiveMode && (
        <section className="rounded-xl bg-white/5 border border-white/10 p-5">
          <h4 className="text-sm font-semibold text-gray-200 mb-3">Outcome summary</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Outcome label="Delinquency" from="12.0%" to="9.2%" delta="-2.8 pp" positive />
            <Outcome label="Collection efficiency" from="79%" to="91.4%" delta="+12.4 pp" positive />
            <Outcome label="Recovery rate" from="50%" to="64.2%" delta="+14.2 pp" positive />
          </div>
          <p className="text-[10px] text-gray-500 mt-4 border-t border-white/10 pt-3">
            Every outcome is measured over last 90 days against industry or pre-telemetry baseline. Hover any KPI card for methodology.
          </p>
        </section>
      )}

      <p className="text-[10px] text-gray-500 border-t border-white/10 pt-4">
        This view complies with RBI Digital Lending Directions 2025 and the Fair Practices Code.
      </p>
    </div>
  );
}

function Outcome({ label, from, to, delta, positive }: { label: string; from: string; to: string; delta: string; positive: boolean }) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-4">
      <p className="text-[11px] uppercase tracking-wider text-gray-500 mb-2">{label}</p>
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-xs text-gray-500 line-through tabular-nums">{from}</span>
        <span className="text-lg font-bold text-white tabular-nums">{to}</span>
      </div>
      <p className={"text-xs font-semibold " + (positive ? "text-accent-green" : "text-red-400")}>{delta}</p>
    </div>
  );
}
