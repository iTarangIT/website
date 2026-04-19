"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  MoreVertical,
  Filter,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  MapPin,
  X,
} from "lucide-react";
import { allBatteryRows, type BatteryRow } from "@/data/portal/loans";
import ScoreBadge from "@/components/portal/shared/ScoreBadge";
import { useTableSort } from "@/components/portal/shared/useTableSort";

const TREND_ICON = {
  up: TrendingUp,
  down: TrendingDown,
  steady: Minus,
};

const RISK_ORDER: Record<BatteryRow["riskLevel"], number> = {
  low: 0,
  medium: 1,
  high: 2,
  "very-high": 3,
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

export type SignalFilter = "all" | "low-usage" | "irregular-charging" | "idle-2d" | "geo-shift";
export type SeverityFilter = "all" | "critical" | "warning" | "info" | "geo-variation";

export const SIGNAL_OPTIONS: { id: SignalFilter; label: string }[] = [
  { id: "all", label: "All signals" },
  { id: "low-usage", label: "Low usage (<40 km/d)" },
  { id: "irregular-charging", label: "Irregular charging" },
  { id: "idle-2d", label: "Idle 2+ days" },
  { id: "geo-shift", label: "Geo variation" },
];

function matchesSignal(row: BatteryRow, signal: SignalFilter): boolean {
  switch (signal) {
    case "all":
      return true;
    case "low-usage":
      return row.dailyKm30d < 40;
    case "irregular-charging":
      return row.imbalanceEvents7d >= 1 && row.offlineHours7d > 2;
    case "idle-2d":
      return row.idleDays7d >= 2;
    case "geo-shift":
      return row.geoShiftFlag;
  }
}

function matchesSeverity(row: BatteryRow, severity: SeverityFilter): boolean {
  switch (severity) {
    case "all":
      return true;
    case "critical":
      return row.riskLevel === "very-high";
    case "warning":
      return row.riskLevel === "high" || row.riskLevel === "medium";
    case "info":
      return row.riskLevel === "low";
    case "geo-variation":
      return row.geoShiftFlag;
  }
}

type SortKey =
  | "batteryId"
  | "customer"
  | "dealer"
  | "sohPct"
  | "dailyKm30d"
  | "overdueDays"
  | "cds"
  | "pci"
  | "riskLevel"
  | "geo";

interface Props {
  onRowClick: (row: BatteryRow) => void;
  onBadgeClick?: (row: BatteryRow, type: "cds" | "pci") => void;
  signal: SignalFilter;
  severity: SeverityFilter;
  onClearSignal: () => void;
  onClearSeverity: () => void;
}

export default function BatteryRiskTable({
  onRowClick,
  onBadgeClick,
  signal,
  severity,
  onClearSignal,
  onClearSeverity,
}: Props) {
  const [emiFilter, setEmiFilter] = useState<"all" | BatteryRow["emiStatus"]>("all");
  const [city, setCity] = useState<string>("all");
  const [query, setQuery] = useState("");

  const cities = useMemo(() => {
    const s = new Set<string>();
    for (const r of allBatteryRows) s.add(r.city);
    return Array.from(s).sort();
  }, []);

  const sort = useTableSort<BatteryRow, SortKey>({
    initialKey: "overdueDays",
    initialDir: "desc",
    getValue: (r, k) => {
      switch (k) {
        case "batteryId":
          return r.batteryId;
        case "customer":
          return r.customer;
        case "dealer":
          return r.dealer;
        case "sohPct":
          return r.sohPct;
        case "dailyKm30d":
          return r.dailyKm30d;
        case "overdueDays":
          return r.overdueDays;
        case "cds":
          return r.cds;
        case "pci":
          return r.pci;
        case "riskLevel":
          return RISK_ORDER[r.riskLevel];
        case "geo":
          return r.geoShiftFlag ? 1 : 0;
      }
    },
  });

  const filtered = useMemo(
    () =>
      allBatteryRows.filter((r) => {
        if (!matchesSeverity(r, severity)) return false;
        if (!matchesSignal(r, signal)) return false;
        if (emiFilter !== "all" && r.emiStatus !== emiFilter) return false;
        if (city !== "all" && r.city !== city) return false;
        if (query && !`${r.batteryId} ${r.customer} ${r.dealer} ${r.imei}`.toLowerCase().includes(query.toLowerCase()))
          return false;
        return true;
      }),
    [signal, severity, emiFilter, city, query],
  );

  const rows = useMemo(() => sort.sortRows(filtered), [filtered, sort]);

  const activeSignal = SIGNAL_OPTIONS.find((s) => s.id === signal);

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Battery risk master table</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">
            {rows.length} of {allBatteryRows.length} batteries · click any row to open case workspace · click headers to sort
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px]">
          <Filter className="h-3 w-3 text-gray-500" />
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

      {(signal !== "all" || severity !== "all") && (
        <div className="flex items-center gap-2 px-5 py-2.5 border-b border-white/10 bg-brand-500/5">
          <span className="text-[10px] uppercase tracking-wider font-bold text-brand-200">Active filter</span>
          {signal !== "all" && (
            <Chip label={`Signal · ${activeSignal?.label}`} onClear={onClearSignal} />
          )}
          {severity !== "all" && (
            <Chip label={`Severity · ${severity.replace("-", " ")}`} onClear={onClearSeverity} />
          )}
        </div>
      )}

      <div className="overflow-x-auto max-h-[720px]">
        <table className="w-full text-[11px]">
          <caption className="sr-only">
            All financed batteries with risk signals. Click a row to open the case workspace.
            Click a column header to sort the table.
          </caption>
          <thead className="bg-black/40 text-gray-500 sticky top-0 z-10">
            <tr>
              <SortableTh aria-sort={sort.ariaSortFor("batteryId")} onClick={() => sort.onHeaderClick("batteryId")} active={sort.sortKey === "batteryId"} dir={sort.sortDir}>
                Battery
              </SortableTh>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold hidden xl:table-cell">IMEI</th>
              <SortableTh aria-sort={sort.ariaSortFor("customer")} onClick={() => sort.onHeaderClick("customer")} active={sort.sortKey === "customer"} dir={sort.sortDir}>
                Customer
              </SortableTh>
              <SortableTh hiddenUnder="lg" aria-sort={sort.ariaSortFor("dealer")} onClick={() => sort.onHeaderClick("dealer")} active={sort.sortKey === "dealer"} dir={sort.sortDir}>
                Dealer
              </SortableTh>
              <SortableTh aria-sort={sort.ariaSortFor("sohPct")} onClick={() => sort.onHeaderClick("sohPct")} active={sort.sortKey === "sohPct"} dir={sort.sortDir}>
                SOH
              </SortableTh>
              <SortableTh align="right" hiddenUnder="md" aria-sort={sort.ariaSortFor("dailyKm30d")} onClick={() => sort.onHeaderClick("dailyKm30d")} active={sort.sortKey === "dailyKm30d"} dir={sort.sortDir}>
                KM/d 30d
              </SortableTh>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">EMI</th>
              <SortableTh align="right" aria-sort={sort.ariaSortFor("overdueDays")} onClick={() => sort.onHeaderClick("overdueDays")} active={sort.sortKey === "overdueDays"} dir={sort.sortDir}>
                DPD
              </SortableTh>
              <SortableTh aria-sort={sort.ariaSortFor("cds")} onClick={() => sort.onHeaderClick("cds")} active={sort.sortKey === "cds"} dir={sort.sortDir}>
                CDS
              </SortableTh>
              <SortableTh aria-sort={sort.ariaSortFor("pci")} onClick={() => sort.onHeaderClick("pci")} active={sort.sortKey === "pci"} dir={sort.sortDir}>
                PCI
              </SortableTh>
              <SortableTh aria-sort={sort.ariaSortFor("riskLevel")} onClick={() => sort.onHeaderClick("riskLevel")} active={sort.sortKey === "riskLevel"} dir={sort.sortDir}>
                Risk
              </SortableTh>
              <SortableTh aria-sort={sort.ariaSortFor("geo")} onClick={() => sort.onHeaderClick("geo")} active={sort.sortKey === "geo"} dir={sort.sortDir}>
                Geo
              </SortableTh>
              <th scope="col" className="text-right px-4 py-2.5 font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((r) => {
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
                    {r.rejectedAction && <FlagChip label="Immobilization rejected" variant="danger" />}
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
                  <td className="px-3 py-2">
                    <GeoChip flagged={r.geoShiftFlag} />
                  </td>
                  <td className="px-4 py-2 text-right">
                    <MoreVertical className="h-3.5 w-3.5 text-gray-500 inline-block" aria-hidden />
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={13} className="px-4 py-10 text-center text-gray-500">
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

function SortableTh({
  children,
  active,
  dir,
  onClick,
  align = "left",
  hiddenUnder,
  ...rest
}: React.ThHTMLAttributes<HTMLTableCellElement> & {
  active: boolean;
  dir: "asc" | "desc" | "none";
  onClick: () => void;
  align?: "left" | "right";
  hiddenUnder?: "lg" | "md";
}) {
  const Icon =
    !active || dir === "none"
      ? ChevronsUpDown
      : dir === "asc"
      ? ChevronUp
      : ChevronDown;

  return (
    <th
      scope="col"
      {...rest}
      className={cn(
        "font-semibold py-2.5",
        align === "right" ? "text-right px-3" : "text-left px-3",
        hiddenUnder === "lg" && "hidden lg:table-cell",
        hiddenUnder === "md" && "hidden md:table-cell",
      )}
    >
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "inline-flex items-center gap-1 text-[11px] uppercase tracking-wider hover:text-white focus:outline-none focus:ring-1 focus:ring-brand-400 rounded-sm px-0.5",
          active ? "text-brand-200" : "text-gray-500",
          align === "right" && "flex-row-reverse",
        )}
      >
        {children}
        <Icon className="h-3 w-3" />
      </button>
    </th>
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

function GeoChip({ flagged }: { flagged: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full border text-[10px] font-semibold",
        flagged ? "bg-red-500/15 text-red-300 border-red-500/30" : "bg-accent-green/10 text-accent-green border-accent-green/30",
      )}
      title={flagged ? ">100 km from onboarding — flagged" : "Within onboarding radius"}
    >
      <MapPin className="h-2.5 w-2.5" />
      {flagged ? "Variation" : "OK"}
    </span>
  );
}

function Chip({ label, onClear }: { label: string; onClear: () => void }) {
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-brand-500/20 border border-brand-500/40 text-brand-100 text-[10px] font-semibold">
      {label}
      <button
        type="button"
        onClick={onClear}
        aria-label={`Clear ${label}`}
        className="hover:text-white"
      >
        <X className="h-2.5 w-2.5" />
      </button>
    </span>
  );
}
