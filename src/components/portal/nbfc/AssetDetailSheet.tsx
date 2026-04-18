"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Phone,
  User,
  Calendar,
  Zap,
  Thermometer,
  Route,
  Battery,
  AlertTriangle,
  TrendingDown,
  Lock,
  Send,
  ShieldAlert,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Driver } from "@/data/portal/drivers";
import { getBenchmark } from "@/data/portal/area-benchmarks";
import BenchmarkBar from "./BenchmarkBar";
import { formatCurrency } from "@/lib/utils";

interface Props {
  driver: Driver | null;
  onClose: () => void;
}

export default function AssetDetailSheet({ driver, onClose }: Props) {
  const [toast, setToast] = useState<string | null>(null);

  if (!driver) return null;
  const bench = getBenchmark(driver.city);

  const band = driver.risk.riskBand;
  const bandColor = band === "low" ? "text-accent-green" : band === "medium" ? "text-accent-amber" : "text-red-400";
  const bandBg = band === "low" ? "bg-accent-green/15 border-accent-green/30" : band === "medium" ? "bg-accent-amber/15 border-accent-amber/30" : "bg-red-500/15 border-red-500/30";

  const action = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <Sheet open={!!driver} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl bg-gray-950 text-white border-l border-white/10 overflow-y-auto p-0"
      >
        <SheetHeader className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur border-b border-white/10 px-6 py-4 space-y-0">
          <SheetTitle className="text-white">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center">
                <User className="h-4 w-4 text-brand-300" />
              </div>
              <div className="min-w-0">
                <p className="text-base font-semibold text-white truncate">{driver.name}</p>
                <p className="text-xs text-gray-400 font-normal truncate">
                  {driver.batterySerial} · {driver.batteryModelLabel}
                </p>
              </div>
              <span className={cn("ml-auto shrink-0 text-[10px] uppercase tracking-wider font-bold px-2 py-1 rounded-full border", bandBg, bandColor)}>
                {band} risk
              </span>
            </div>
          </SheetTitle>
        </SheetHeader>

        <div className="px-6 py-6 space-y-7">
          {/* Driver + loan */}
          <section>
            <SectionTitle>Driver & Loan</SectionTitle>
            <div className="grid grid-cols-2 gap-x-5 gap-y-3 text-xs">
              <InfoRow icon={Phone} label="Phone" value={driver.phone} />
              <InfoRow icon={Calendar} label="Onboarded" value={driver.onboardingDate} />
              <InfoRow label="Dealer" value={driver.dealerName} />
              <InfoRow label="City" value={driver.city} />
              <InfoRow label="Principal" value={formatCurrency(driver.loan.principal)} />
              <InfoRow label="EMI" value={formatCurrency(driver.loan.emi)} />
              <InfoRow label="Outstanding" value={formatCurrency(driver.loan.outstanding)} emphasis />
              <InfoRow label="Next due" value={driver.loan.nextDueDate} />
              <InfoRow label="DPD" value={String(driver.loan.dpd)} emphasis={driver.loan.dpd > 0} />
              <InfoRow label="Tenure" value={`${driver.loan.tenureMonths} months`} />
            </div>
          </section>

          {/* Battery performance */}
          <section>
            <SectionTitle>Battery Performance</SectionTitle>
            <div className="grid grid-cols-2 gap-3">
              <StatTile icon={Route} label="Cumulative KM" value={driver.cumulativeKm.toLocaleString("en-IN")} />
              <StatTile icon={Route} label="Avg Daily KM (7d)" value={`${driver.avgDailyKm7d}`} sub={`30d: ${driver.avgDailyKm30d}`} />
              <StatTile icon={Battery} label="SOH" value={`${driver.sohPct}%`} sub={`Δ30d: ${driver.sohDelta30d >= 0 ? "+" : ""}${driver.sohDelta30d}`} />
              <StatTile icon={Calendar} label="Deployed" value={`${driver.monthsDeployed} mo`} />
              <StatTile icon={Zap} label="Charge Cycles" value={String(driver.chargeCycles)} />
              <StatTile icon={Thermometer} label="Temp stress (7d)" value={`${driver.tempStressMinutes7d} min`} />
            </div>
          </section>

          {/* Risk signals */}
          <section>
            <SectionTitle>Risk Signals</SectionTitle>
            <div className="space-y-2">
              <SignalRow label="Usage drop vs prev 7d" value={`${Math.round(driver.risk.usageDropPct * 100)}%`} warn={driver.risk.usageDropPct > 0.3} />
              <SignalRow label="Idle days (7d)" value={String(driver.risk.idleDays7d)} warn={driver.risk.idleDays7d >= 2} />
              <SignalRow label="Geo-shift flag" value={driver.risk.geoShiftFlag ? "Yes" : "No"} warn={driver.risk.geoShiftFlag} />
              <SignalRow label="Tamper / offline events (30d)" value={String(driver.risk.tamperEvents30d + Math.round(driver.offlineHours7d / 24))} warn={driver.risk.tamperEvents30d > 0} />
              <SignalRow label="Cell imbalance (7d)" value={String(driver.imbalanceEvents7d)} warn={driver.imbalanceEvents7d >= 2} />
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="rounded-lg bg-black/20 border border-white/10 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-gray-500">Chronic Default Score</p>
                  <p className={cn("text-2xl font-bold tabular-nums mt-1", bandColor)}>{driver.risk.cdsScore}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">0 = safe · 100 = very high</p>
                </div>
                <div className="rounded-lg bg-black/20 border border-white/10 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-gray-500">Payment Consistency</p>
                  <p className="text-2xl font-bold tabular-nums mt-1 text-white">{driver.risk.pci.toFixed(2)}</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">1.0 = reliable payer</p>
                </div>
              </div>
            </div>
          </section>

          {/* Area benchmarks */}
          {bench && (
            <section>
              <SectionTitle>
                Area Benchmark
                <span className="ml-2 text-[10px] font-normal text-gray-500 uppercase tracking-wider">
                  vs other drivers in {driver.city}
                </span>
              </SectionTitle>
              <div className="space-y-5 pt-2">
                <BenchmarkBar
                  label="Daily KM"
                  value={driver.avgDailyKm7d}
                  median={bench.avgDailyKm.median}
                  topQuartile={bench.avgDailyKm.topQuartile}
                  higherIsBetter
                />
                <BenchmarkBar
                  label="SOH %"
                  value={driver.sohPct}
                  median={bench.sohPct.median}
                  topQuartile={bench.sohPct.topQuartile}
                  higherIsBetter
                  format={(n) => `${n}%`}
                />
                <BenchmarkBar
                  label="DPD"
                  value={driver.loan.dpd}
                  median={bench.dpd.median}
                  topQuartile={bench.dpd.topQuartile}
                  higherIsBetter={false}
                />
                <BenchmarkBar
                  label="CDS Score"
                  value={driver.risk.cdsScore}
                  median={bench.cdsScore.median}
                  topQuartile={bench.cdsScore.topQuartile}
                  higherIsBetter={false}
                />
              </div>
            </section>
          )}

          {/* Actions */}
          <section>
            <SectionTitle>Actions</SectionTitle>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <ActionButton icon={Send} label="Send reminder" onClick={() => action("Reminder SMS queued")} />
              <ActionButton icon={AlertTriangle} label="Escalate" onClick={() => action("Escalated to collections")} warning />
              <ActionButton icon={Lock} label="Request immobilize" onClick={() => action("Immobilization request created")} danger />
            </div>
          </section>
        </div>

        {toast && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 border border-white/10 text-white text-sm px-4 py-2 rounded-lg shadow-xl z-50 flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-accent-green" />
            {toast}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-3 pb-1 border-b border-white/10">
      {children}
    </h3>
  );
}

function InfoRow({
  icon: Icon,
  label,
  value,
  emphasis,
}: {
  icon?: typeof Phone;
  label: string;
  value: string;
  emphasis?: boolean;
}) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-white/5 pb-2">
      <span className="text-gray-400 flex items-center gap-1.5">
        {Icon && <Icon className="h-3 w-3" />}
        {label}
      </span>
      <span className={cn("text-right tabular-nums", emphasis ? "text-white font-semibold" : "text-gray-200")}>
        {value}
      </span>
    </div>
  );
}

function StatTile({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: typeof Phone;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-gray-500 mb-1">
        <Icon className="h-3 w-3" />
        {label}
      </div>
      <p className="text-lg font-bold text-white tabular-nums">{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function SignalRow({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="flex items-center justify-between text-xs py-1.5">
      <span className="text-gray-400">{label}</span>
      <span className={cn("font-semibold tabular-nums", warn ? "text-red-400" : "text-gray-200")}>
        {warn && <span className="inline-block h-1.5 w-1.5 rounded-full bg-red-400 mr-1.5 align-middle" />}
        {value}
      </span>
    </div>
  );
}

function ActionButton({
  icon: Icon,
  label,
  onClick,
  warning,
  danger,
}: {
  icon: typeof Send;
  label: string;
  onClick: () => void;
  warning?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center justify-center gap-2 px-3 py-2.5 text-xs font-semibold rounded-lg border transition-colors",
        danger
          ? "bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20"
          : warning
          ? "bg-accent-amber/10 border-accent-amber/30 text-accent-amber hover:bg-accent-amber/20"
          : "bg-brand-500/10 border-brand-500/30 text-brand-300 hover:bg-brand-500/20",
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </button>
  );
}

// Suppress unused import TS warning (Zap only referenced, TrendingDown unused but we import for potential reuse)
void TrendingDown;
