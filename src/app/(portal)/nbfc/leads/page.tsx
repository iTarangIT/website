"use client";

import { PhoneCall, Flame, Target, TrendingUp } from "lucide-react";
import { useExecutiveMode } from "@/components/portal/shared/ExecutiveSummaryToggle";
import KPIHeroCard from "@/components/portal/shared/KPIHeroCard";
import LeadFunnel from "@/components/portal/nbfc/leads/LeadFunnel";
import LeadDistributionEngine from "@/components/portal/nbfc/leads/LeadDistributionEngine";
import LeadTable from "@/components/portal/nbfc/leads/LeadTable";
import CallScheduler from "@/components/portal/nbfc/leads/CallScheduler";
import NarrativeTile from "@/components/portal/shared/NarrativeTile";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import { leadKPIs } from "@/data/portal/leads";

export default function LeadIntelligencePage() {
  const { executiveMode } = useExecutiveMode();

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Lead Intelligence</h1>
          <p className="text-sm text-gray-400 mt-1">Act 1 · how your loan book is growing</p>
        </div>
        <DataFreshnessBadge />
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPIHeroCard label="Leads contacted today" value={leadKPIs.leadsContactedToday.toLocaleString("en-IN")} delta={`+${leadKPIs.leadsContactedDeltaPct}%`} deltaDirection="up" deltaLabel="vs yesterday" icon={PhoneCall} />
        <KPIHeroCard label="AI calls today" value={leadKPIs.aiCallsToday.toLocaleString("en-IN")} icon={PhoneCall} sparklineData={[820, 910, 1020, 1075, 1120, 1195, 1243]} />
        <KPIHeroCard label="Hot leads generated" value={String(leadKPIs.hotLeadsGenerated)} delta="+18" deltaDirection="up" deltaLabel="this week" icon={Flame} />
        <KPIHeroCard label="Conversion rate" value={`${leadKPIs.conversionRatePct}%`} delta="+0.3 pp" deltaDirection="up" deltaLabel="MoM" icon={Target} />
      </div>

      {!executiveMode && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2"><LeadFunnel /></div>
          <LeadDistributionEngine />
        </div>
      )}

      <NarrativeTile
        title="Lead signal of the week"
        bullets={[
          "Referral-sourced leads convert 2.1× better than paid — consider doubling referral incentives this quarter.",
          "AI dialer pickup rate in Kolkata rose from 38% to 51% after time-of-day optimization (10:30–12:30).",
          "Budget-signaling leads pay higher intent score even if tone is hesitant — do not down-weight tone alone.",
        ]}
      />

      {!executiveMode && <LeadTable />}

      {!executiveMode && <CallScheduler />}

      <p className="text-[10px] text-gray-500 border-t border-white/10 pt-4 flex items-center gap-2">
        <TrendingUp className="h-3 w-3" />
        Intent-Score model is v0.2-demo. All scores clickable for inputs + confidence. RBI DL fair-practice compliant.
      </p>
    </div>
  );
}
