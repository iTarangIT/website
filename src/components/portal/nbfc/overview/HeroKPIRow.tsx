"use client";

import Link from "next/link";
import { Wallet, AlertTriangle, TrendingDown, Recycle } from "lucide-react";
import KPIHeroCard from "@/components/portal/shared/KPIHeroCard";
import { portfolioKPIs, methodologyNotes } from "@/data/portal/portfolio";

export default function HeroKPIRow() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <Link href="/nbfc/batteries" className="block">
        <KPIHeroCard
          label="Active Loans"
          value={portfolioKPIs.activeLoans.toLocaleString("en-IN")}
          delta={`+${portfolioKPIs.activeLoansDeltaPct}%`}
          deltaDirection="up"
          deltaLabel="QoQ"
          icon={Wallet}
          sparklineData={[4120, 4285, 4398, 4502, 4610, 4720, 4856]}
        />
      </Link>
      <Link href="/nbfc/batteries?filter=at-risk" className="block">
        <KPIHeroCard
          label="At-Risk Accounts"
          value={`${portfolioKPIs.atRiskAccounts.toLocaleString("en-IN")} / ${portfolioKPIs.atRiskPct}%`}
          delta={`${portfolioKPIs.atRiskDeltaPct}%`}
          deltaDirection="down"
          positiveIsDown
          deltaLabel="MoM"
          icon={AlertTriangle}
          sparklineData={[1290, 1255, 1218, 1190, 1162, 1140, 1124]}
        />
      </Link>
      <Link href="/nbfc/risk" className="block">
        <KPIHeroCard
          label="Delinquency Rate"
          value={`${portfolioKPIs.delinquencyRatePct}%`}
          delta={`${portfolioKPIs.delinquencyDeltaPctMoM}%`}
          deltaDirection="down"
          positiveIsDown
          deltaLabel={`MoM · baseline ${portfolioKPIs.delinquencyBaselinePct}%`}
          icon={TrendingDown}
          sparklineData={[12.0, 11.4, 10.8, 10.3, 9.8, 9.5, 9.2]}
          methodology={methodologyNotes.delinquency}
        />
      </Link>
      <Link href="/nbfc/recovery" className="block">
        <KPIHeroCard
          label="Recovery In Motion"
          value={`₹${portfolioKPIs.recoveryInMotionLakhs} L / ${portfolioKPIs.recoveryPct}%`}
          delta={`+${portfolioKPIs.recoveryPct - 50}%`}
          deltaDirection="up"
          deltaLabel="vs baseline 50%"
          icon={Recycle}
          sparklineData={[48, 52, 56, 60, 63, 65, 67]}
          methodology={methodologyNotes.recoveryRate}
        />
      </Link>
    </div>
  );
}
