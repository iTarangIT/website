"use client";

import { Lightbulb } from "lucide-react";
import InsightCards from "@/components/portal/nbfc/risk/InsightCards";
import CohortTable from "@/components/portal/nbfc/risk/CohortTable";
import RiskDistributionDonut from "@/components/portal/nbfc/risk/RiskDistributionDonut";
import HeroPersonasSection from "@/components/portal/nbfc/risk/HeroPersonasSection";
import { preDisbursementRecs } from "@/data/portal/insights";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import ConfidenceBadge from "@/components/portal/shared/ConfidenceBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";

export default function RiskIntelligencePage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Risk Intelligence</h1>
          <p className="text-sm text-gray-400 mt-1">
            Act 2 · pattern-level insights for pre-disbursement underwriting (no raw borrower data exposed)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceBadge level="medium" title="Rule-based insights · periodic sample validation" />
          <DataFreshnessBadge />
        </div>
      </header>

      <section>
        <h4 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-3 pb-1 border-b border-white/10 flex items-center gap-2">
          <Lightbulb className="h-3.5 w-3.5" />
          AI-generated insights
        </h4>
        <InsightCards />
      </section>

      <HeroPersonasSection />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <CohortTable />
        </div>
        <RiskDistributionDonut />
      </div>

      <section className="rounded-xl bg-white/5 border border-white/10">
        <div className="px-5 py-4 border-b border-white/10">
          <h4 className="text-sm font-semibold text-gray-200">Pre-disbursement recommendations</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">Evidence-backed underwriting tweaks · not auto-applied</p>
        </div>
        <ul className="divide-y divide-white/5">
          {preDisbursementRecs.map((r) => (
            <li key={r.id} className="px-5 py-4 grid md:grid-cols-5 gap-3 text-xs">
              <div className="md:col-span-2">
                <p className="text-gray-400 text-[10px] uppercase tracking-wider font-semibold">Segment</p>
                <p className="text-white font-semibold mt-0.5">{r.segment}</p>
              </div>
              <div className="md:col-span-2">
                <p className="text-gray-400 text-[10px] uppercase tracking-wider font-semibold">Recommendation</p>
                <p className="text-gray-200 mt-0.5">{r.recommendation}</p>
              </div>
              <div>
                <p className="text-gray-400 text-[10px] uppercase tracking-wider font-semibold">Evidence</p>
                <p className="text-gray-400 italic mt-0.5 leading-relaxed">{r.evidence}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <p className="text-[10px] text-gray-500 leading-relaxed">
        Why we use this data: portfolio-level risk modelling per NBFC underwriting purpose. No individual borrower PII shown on this page.
      </p>

      <RegulatoryFooter />
    </div>
  );
}
