import { Battery, Wallet, Clock, ShieldCheck, TrendingDown, Repeat2 } from "lucide-react";
import { kpis } from "@/lib/nbfc-mock-data";
import { formatNumber } from "@/lib/utils";
import NPAComparisonBar from "./NPAComparisonBar";

type KPICardProps = {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: React.ReactNode;
  caption?: string;
  tone?: "default" | "success";
  children?: React.ReactNode;
};

function KPICard({ icon: Icon, label, value, caption, tone = "default", children }: KPICardProps) {
  return (
    <div className="rounded-2xl bg-white border border-gray-100 shadow-sm p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-gray-400">
          {label}
        </span>
        <span
          className={
            tone === "success"
              ? "inline-flex h-8 w-8 items-center justify-center rounded-lg bg-green-50 text-accent-green"
              : "inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600"
          }
        >
          <Icon className="h-4 w-4" />
        </span>
      </div>

      {children ?? (
        <>
          <p className="text-2xl font-semibold text-gray-900 tracking-tight">{value}</p>
          {caption && <p className="text-xs text-gray-500">{caption}</p>}
        </>
      )}
    </div>
  );
}

export default function KPIGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
      <KPICard
        icon={Battery}
        label="Total Batteries Financed"
        value={formatNumber(kpis.batteriesFinanced)}
        caption="Across India — live telemetry"
      />
      <KPICard
        icon={Wallet}
        label="Active Loans"
        value={formatNumber(kpis.activeLoans)}
        caption="Currently on-book"
      />
      <KPICard
        icon={TrendingDown}
        label="Portfolio AUM"
        value={kpis.portfolioAumLabel}
        caption="Assets under management"
      />
      <KPICard icon={ShieldCheck} label="NPA %" value="" tone="success">
        <div className="flex items-baseline gap-2">
          <p className="text-2xl font-semibold text-accent-green tracking-tight">
            {kpis.npa.itarang.toFixed(1)}%
          </p>
          <span className="text-xs text-gray-400">
            vs {kpis.npa.industry.toFixed(1)}% industry
          </span>
        </div>
        <NPAComparisonBar itarang={kpis.npa.itarang} industry={kpis.npa.industry} />
      </KPICard>
      <KPICard
        icon={Clock}
        label="Avg. Lead → Disbursement"
        value={kpis.leadToDisbursement.value}
        caption={kpis.leadToDisbursement.comparison}
        tone="success"
      />
      <KPICard
        icon={Repeat2}
        label="Recovery Rate on Defaults"
        value={kpis.recoveryRate.value}
        caption={kpis.recoveryRate.comparison}
        tone="success"
      />
    </div>
  );
}
