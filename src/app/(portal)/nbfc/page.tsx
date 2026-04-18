import Link from "next/link";
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  IndianRupee,
  AlertCircle,
  Activity,
  MapPin,
  WifiOff,
  Lock,
} from "lucide-react";
import NBFCKpiGrid from "@/components/portal/nbfc/NBFCKpiGrid";
import DPDBucketBar from "@/components/portal/nbfc/DPDBucketBar";
import RiskBandDonut from "@/components/portal/nbfc/RiskBandDonut";
import Badge from "@/components/ui/Badge";
import {
  nbfcMonthlyFinancial,
  telemetryAlerts,
  highRiskPreview,
} from "@/data/portal/nbfc-extra-kpis";

export default function NBFCDashboardPage() {
  const m = nbfcMonthlyFinancial;

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">NBFC Portfolio Overview</h1>
          <p className="text-sm text-gray-400 mt-1">Live visibility across financed assets, risk signals and collections.</p>
        </div>
        <Badge variant="success" className="animate-pulse">
          <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-accent-green" />
          LIVE
        </Badge>
      </div>

      {/* Top 6 KPI cards */}
      <NBFCKpiGrid />

      {/* Portfolio health: DPD + Risk band donut */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DPDBucketBar />
        <RiskBandDonut />
      </section>

      {/* Financial rollup + telemetry alerts */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="rounded-xl bg-white/5 border border-white/10 p-5 space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-gray-200">Monthly Financial Rollup</h4>
            <span className="text-[10px] uppercase tracking-wider text-gray-500">April 2026</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <FinancialStat
              label="Disbursed this month"
              value={`₹${m.disbursedThisMonthLakhs} L`}
              delta={m.disbursedDeltaPct}
              icon={IndianRupee}
              positive={m.disbursedDeltaPct >= 0}
            />
            <FinancialStat
              label="Collected this month"
              value={`₹${m.collectedThisMonthLakhs} L`}
              delta={m.collectedDeltaPct}
              icon={Activity}
              positive={m.collectedDeltaPct >= 0}
            />
            <FinancialStat
              label="Overdue outstanding"
              value={`₹${m.overdueOutstandingLakhs} L`}
              delta={m.overdueDeltaPct}
              icon={AlertCircle}
              positive={m.overdueDeltaPct < 0}
            />
          </div>
        </div>

        <div className="rounded-xl bg-white/5 border border-white/10 p-5">
          <h4 className="text-sm font-semibold text-gray-200 mb-4">Telemetry-linked risk</h4>
          <ul className="space-y-3">
            <TelemetryAlertRow icon={Activity} label="Usage drop >50% (7d)" count={telemetryAlerts.usageDropCount} color="text-accent-yellow" />
            <TelemetryAlertRow icon={MapPin} label="Geo-shift (>100 km)" count={telemetryAlerts.geoShiftCount} color="text-accent-amber" />
            <TelemetryAlertRow icon={WifiOff} label="Offline > 48h" count={telemetryAlerts.offlineGt48hCount} color="text-red-400" />
            <TelemetryAlertRow icon={Lock} label="Immobilizations pending" count={telemetryAlerts.immobilizationPending} color="text-brand-300" />
          </ul>
        </div>
      </section>

      {/* High risk queue preview */}
      <section className="rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div>
            <h4 className="text-sm font-semibold text-gray-200">High-risk queue</h4>
            <p className="text-xs text-gray-500 mt-0.5">Top assets by chronic default score</p>
          </div>
          <Link
            href="/nbfc/assets?risk=high"
            className="text-xs font-semibold text-brand-300 hover:text-brand-200 flex items-center gap-1"
          >
            View all assets
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
        <div className="divide-y divide-white/5">
          {highRiskPreview.map((row) => (
            <div key={row.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm font-medium text-white">{row.name}</p>
                <p className="text-xs text-gray-500">{row.city}</p>
              </div>
              <div className="flex items-center gap-5 text-xs">
                <span className="text-gray-400">DPD <span className="text-white font-semibold tabular-nums ml-1">{row.dpd}</span></span>
                <span className="text-gray-400">CDS <span className="text-accent-amber font-semibold tabular-nums ml-1">{row.cds}</span></span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function FinancialStat({
  label,
  value,
  delta,
  icon: Icon,
  positive,
}: {
  label: string;
  value: string;
  delta: number;
  icon: typeof Activity;
  positive: boolean;
}) {
  const Trend = delta >= 0 ? TrendingUp : TrendingDown;
  return (
    <div className="rounded-lg bg-black/20 border border-white/5 p-4">
      <div className="flex items-center justify-between mb-3">
        <Icon className="h-4 w-4 text-brand-300" />
        <span className={`flex items-center gap-0.5 text-[11px] ${positive ? "text-accent-green" : "text-red-400"}`}>
          <Trend className="h-3 w-3" />
          {Math.abs(delta).toFixed(1)}%
        </span>
      </div>
      <p className="text-xl font-bold text-white tracking-tight">{value}</p>
      <p className="text-[11px] text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}

function TelemetryAlertRow({
  icon: Icon,
  label,
  count,
  color,
}: {
  icon: typeof Activity;
  label: string;
  count: number;
  color: string;
}) {
  return (
    <li className="flex items-center justify-between text-sm">
      <span className="flex items-center gap-2 text-gray-300">
        <Icon className={`h-3.5 w-3.5 ${color}`} />
        {label}
      </span>
      <span className="font-semibold text-white tabular-nums">{count}</span>
    </li>
  );
}
