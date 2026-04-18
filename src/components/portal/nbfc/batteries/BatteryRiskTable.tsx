"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown, Minus, MoreVertical, Filter } from "lucide-react";
import { allBatteryRows, type BatteryRow } from "@/data/portal/loans";
import ScoreBadge from "@/components/portal/shared/ScoreBadge";

const TREND_ICON = {
  up: TrendingUp,
  down: TrendingDown,
  steady: Minus,
};

const RISK_STYLES: Record<BatteryRow["riskLevel"], string> = {
  low: "bg-accent-green/20 text-accent-green border-accent-green/40",
  medium: "bg-brand-500/20 text-brand-200 border-brand-500/40",
  high: "bg-accent-amber/20 text-accent-amber border-accent-amber/40",
  "very-high": "bg-red-500/20 text-red-300 border-red-500/40",
};

const EMI_STATUS_LABEL: Record<BatteryRow["emiStatus"], { label: string; cls: string }> = {
  current: { label: "Current", cls: "text-accent-green" },
  "overdue-1-7": { label: "1–7d overdue", cls: "text-accent-amber" },
  "overdue-8-30": { label: "8–30d overdue", cls: "text-accent-amber" },
  "overdue-30+": { label: "30d+ overdue", cls: "text-red-300" },
  skipped: { label: "Skipped", cls: "text-red-300" },
};

interface Props {
  onRowClick: (row: BatteryRow) => void;
  onBadgeClick?: (row: BatteryRow, type: "cds" | "pci") => void;
  initialRiskFilter?: "all" | BatteryRow["riskLevel"];
}

export default function BatteryRiskTable({ onRowClick, onBadgeClick, initialRiskFilter = "all" }: Props) {
  const [risk, setRisk] = useState<"all" | BatteryRow["riskLevel"]>(initialRiskFilter);
  const [emiFilter, setEmiFilter] = useState<"all" | BatteryRow["emiStatus"]>("all");
  const [city, setCity] = useState<string>("all");
  const [query, setQuery] = useState("");

  const cities = useMemo(() => {
    const s = new Set<string>();
    for (const r of allBatteryRows) s.add(r.city);
    return Array.from(s).sort();
  }, []);

  const filtered = useMemo(
    () =>
      allBatteryRows.filter((r) => {
        if (risk !== "all" && r.riskLevel !== risk) return false;
        if (emiFilter !== "all" && r.emiStatus !== emiFilter) return false;
        if (city !== "all" && r.city !== city) return false;
        if (query && !`${r.batteryId} ${r.customer} ${r.dealer} ${r.imei}`.toLowerCase().includes(query.toLowerCase())) return false;
        return true;
      }),
    [risk, emiFilter, city, query],
  );

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Battery risk master table</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">
            {filtered.length} of {allBatteryRows.length} batteries · click any row to open case workspace
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <Filter className="h-3 w-3 text-gray-500" />
          <select
            value={risk}
            onChange={(e) => setRisk(e.target.value as "all" | BatteryRow["riskLevel"])}
            className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none"
          >
            <option value="all" className="bg-gray-950">Risk · All</option>
            <option value="low" className="bg-gray-950">Low</option>
            <option value="medium" className="bg-gray-950">Medium</option>
            <option value="high" className="bg-gray-950">High</option>
            <option value="very-high" className="bg-gray-950">Very High</option>
          </select>
          <select
            value={emiFilter}
            onChange={(e) => setEmiFilter(e.target.value as "all" | BatteryRow["emiStatus"])}
            className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none"
          >
            <option value="all" className="bg-gray-950">EMI · All</option>
            <option value="current" className="bg-gray-950">Current</option>
            <option value="overdue-1-7" className="bg-gray-950">1–7 days</option>
            <option value="overdue-8-30" className="bg-gray-950">8–30 days</option>
            <option value="overdue-30+" className="bg-gray-950">30+ days</option>
          </select>
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none"
          >
            <option value="all" className="bg-gray-950">City · All</option>
            {cities.map((c) => (
              <option key={c} value={c} className="bg-gray-950">{c}</option>
            ))}
          </select>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Battery / IMEI / name"
            className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-brand-400 w-44"
          />
        </div>
      </div>

      <div className="overflow-x-auto max-h-[720px]">
        <table className="w-full text-[11px]">
          <caption className="sr-only">All financed batteries with risk signals. Click a row to open the case workspace.</caption>
          <thead className="bg-black/40 text-gray-500 sticky top-0 z-10">
            <tr>
              <th scope="col" className="text-left px-4 py-2.5 font-semibold">Battery</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold hidden xl:table-cell">IMEI</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Customer</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold hidden lg:table-cell">Dealer</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">SOH</th>
              <th scope="col" className="text-right px-3 py-2.5 font-semibold hidden md:table-cell">KM/d 30d</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">EMI</th>
              <th scope="col" className="text-right px-3 py-2.5 font-semibold">DPD</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">CDS</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">PCI</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Risk</th>
              <th scope="col" className="text-right px-4 py-2.5 font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.map((r) => {
              const Trend = TREND_ICON[r.sohTrend];
              const emi = EMI_STATUS_LABEL[r.emiStatus];
              return (
                <tr
                  key={r.batteryId}
                  onClick={() => onRowClick(r)}
                  className="hover:bg-white/5 cursor-pointer"
                >
                  <td className="px-4 py-2 font-mono text-white">
                    {r.batteryId}
                    {r.isInsufficientHistory && <FlagChip label="Insufficient data" />}
                    {r.isRecentlyRestructured && <FlagChip label="Restructured" />}
                    {r.isForceMajeure && <FlagChip label="Force majeure" />}
                    {r.immobilized && <FlagChip label="Immobilized" variant="danger" />}
                  </td>
                  <td className="px-3 py-2 text-gray-400 font-mono hidden xl:table-cell">{r.imei}</td>
                  <td className="px-3 py-2 text-gray-200">{r.customer}</td>
                  <td className="px-3 py-2 text-gray-400 hidden lg:table-cell">{r.dealer}</td>
                  <td className="px-3 py-2 text-gray-200 tabular-nums">
                    <span className="inline-flex items-center gap-1">
                      {r.sohPct}%
                      <Trend
                        className={cn(
                          "h-3 w-3",
                          r.sohTrend === "down" ? "text-red-400" : r.sohTrend === "up" ? "text-accent-green" : "text-gray-500",
                        )}
                      />
                    </span>
                  </td>
                  <td className="px-3 py-2 text-gray-300 tabular-nums text-right hidden md:table-cell">{r.dailyKm30d}</td>
                  <td className={cn("px-3 py-2", emi.cls)}>{emi.label}</td>
                  <td className="px-3 py-2 text-gray-200 tabular-nums text-right">{r.overdueDays || "—"}</td>
                  <td
                    className="px-3 py-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      onBadgeClick?.(r, "cds");
                    }}
                  >
                    {r.isInsufficientHistory ? (
                      <span className="text-[10px] text-gray-500">Insufficient</span>
                    ) : (
                      <ScoreBadge type="cds" value={r.cds} onClick={onBadgeClick ? () => onBadgeClick(r, "cds") : undefined} />
                    )}
                  </td>
                  <td
                    className="px-3 py-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      onBadgeClick?.(r, "pci");
                    }}
                  >
                    <ScoreBadge type="pci" value={r.pci} onClick={onBadgeClick ? () => onBadgeClick(r, "pci") : undefined} />
                  </td>
                  <td className="px-3 py-2">
                    <span className={cn("inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", RISK_STYLES[r.riskLevel])}>
                      {r.riskLevel.replace("-", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <MoreVertical className="h-3.5 w-3.5 text-gray-500 inline-block" aria-hidden />
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={12} className="px-4 py-10 text-center text-gray-500">
                  No batteries match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FlagChip({ label, variant = "default" }: { label: string; variant?: "default" | "danger" }) {
  return (
    <span
      className={cn(
        "ml-2 inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider",
        variant === "danger" ? "bg-red-500/20 text-red-300" : "bg-white/10 text-gray-300",
      )}
    >
      {label}
    </span>
  );
}
