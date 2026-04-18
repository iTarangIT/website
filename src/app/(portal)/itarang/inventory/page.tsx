"use client";

import { useMemo, useState } from "react";
import { Package, Warehouse as WarehouseIcon, X } from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";
import KPIHeroCard from "@/components/portal/shared/KPIHeroCard";
import {
  inventoryUnits,
  inventorySummary,
  type InventoryStatus,
  type InventoryUnit,
  type Warehouse,
  type AgeBand,
} from "@/data/portal/inventory";

const STATUS_STYLES: Record<InventoryStatus, string> = {
  Received: "bg-brand-500/15 text-brand-200 border-brand-500/30",
  "Under Inspection": "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  Refurbished: "bg-accent-green/15 text-accent-green border-accent-green/30",
  "Ready for Auction": "bg-accent-green/25 text-white border-accent-green/50",
  Scrapped: "bg-red-500/15 text-red-300 border-red-500/30",
};

const STATUSES: InventoryStatus[] = ["Received", "Under Inspection", "Refurbished", "Ready for Auction", "Scrapped"];
const WAREHOUSES: Warehouse[] = ["Delhi · Khair", "Kolkata · Howrah", "Lucknow · Amausi"];
const AGE_BANDS: AgeBand[] = ["0-6 mo", "6-12 mo", "12-18 mo", "18-24 mo", "24+ mo"];

export default function InventoryPage() {
  const [status, setStatus] = useState<"all" | InventoryStatus>("all");
  const [warehouse, setWarehouse] = useState<"all" | Warehouse>("all");
  const [age, setAge] = useState<"all" | AgeBand>("all");
  const [detail, setDetail] = useState<InventoryUnit | null>(null);

  const rows = useMemo(
    () =>
      inventoryUnits.filter((u) => {
        if (status !== "all" && u.status !== status) return false;
        if (warehouse !== "all" && u.warehouse !== warehouse) return false;
        if (age !== "all" && u.ageBand !== age) return false;
        return true;
      }),
    [status, warehouse, age],
  );

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Inventory Management</h1>
          <p className="text-sm text-gray-400 mt-1">Recovered battery inventory · 3 warehouses · click any row for unit detail</p>
        </div>
        <DataFreshnessBadge />
      </header>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {STATUSES.map((s) => (
          <KPIHeroCard
            key={s}
            label={s}
            value={String(inventorySummary.byStatus[s])}
            icon={Package}
            onClick={() => setStatus(s === status ? "all" : s)}
          />
        ))}
      </div>

      <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
        <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-white/10 flex-wrap">
          <div>
            <h4 className="text-sm font-semibold text-gray-200">Inventory units</h4>
            <p className="text-[11px] text-gray-500 mt-0.5">
              {rows.length} of {inventoryUnits.length} units · total est. recovery {formatCurrency(inventorySummary.totalRecoveryValue)}
            </p>
          </div>
          <div className="flex items-center gap-2 text-[11px]">
            <select value={warehouse} onChange={(e) => setWarehouse(e.target.value as "all" | Warehouse)} className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none">
              <option value="all" className="bg-gray-950">Warehouse · All</option>
              {WAREHOUSES.map((w) => (
                <option key={w} value={w} className="bg-gray-950">{w}</option>
              ))}
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value as "all" | InventoryStatus)} className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none">
              <option value="all" className="bg-gray-950">Status · All</option>
              {STATUSES.map((s) => (
                <option key={s} value={s} className="bg-gray-950">{s}</option>
              ))}
            </select>
            <select value={age} onChange={(e) => setAge(e.target.value as "all" | AgeBand)} className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none">
              <option value="all" className="bg-gray-950">Age · All</option>
              {AGE_BANDS.map((a) => (
                <option key={a} value={a} className="bg-gray-950">{a}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="overflow-x-auto max-h-[560px]">
          <table className="w-full text-[11px]">
            <caption className="sr-only">All recovered inventory units, filterable by warehouse, status and age band.</caption>
            <thead className="bg-black/40 text-gray-500 sticky top-0 z-10">
              <tr>
                <th scope="col" aria-sort="none" className="text-left px-4 py-2 font-semibold">Unit ID</th>
                <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Battery</th>
                <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Model</th>
                <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Warehouse</th>
                <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Status</th>
                <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Age</th>
                <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">SOH</th>
                <th scope="col" aria-sort="none" className="text-right px-4 py-2 font-semibold">Recovery</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {rows.map((u) => (
                <tr key={u.id} onClick={() => setDetail(u)} className="hover:bg-white/5 cursor-pointer">
                  <td className="px-4 py-2 font-mono text-white">{u.id}</td>
                  <td className="px-3 py-2 font-mono text-gray-300">{u.serial}</td>
                  <td className="px-3 py-2 text-gray-300">{u.model}</td>
                  <td className="px-3 py-2 text-gray-400">
                    <span className="inline-flex items-center gap-1">
                      <WarehouseIcon className="h-3 w-3" />
                      {u.warehouse}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", STATUS_STYLES[u.status])}>
                      {u.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-gray-300">{u.ageBand}</td>
                  <td className={cn("px-3 py-2 tabular-nums text-right font-semibold", u.sohPct > 85 ? "text-accent-green" : u.sohPct > 70 ? "text-accent-amber" : "text-red-300")}>
                    {u.sohPct}%
                  </td>
                  <td className="px-4 py-2 text-white tabular-nums text-right">{formatCurrency(u.estRecoveryValue)}</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-10 text-center text-gray-500">No units match these filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {detail && <UnitDetailDrawer unit={detail} onClose={() => setDetail(null)} />}

      <RegulatoryFooter />
    </div>
  );
}

function UnitDetailDrawer({ unit, onClose }: { unit: InventoryUnit; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60" onClick={onClose}>
      <div
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="unit-detail-title"
        className="h-full w-full sm:max-w-md bg-gray-950 border-l border-white/10 shadow-2xl overflow-y-auto"
      >
        <header className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-black/30 sticky top-0">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">Inventory unit</p>
            <h2 id="unit-detail-title" className="text-base font-semibold text-white font-mono">{unit.id}</h2>
          </div>
          <button onClick={onClose} aria-label="Close" className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5">
            <X className="h-4 w-4" />
          </button>
        </header>
        <div className="p-5 space-y-4 text-xs">
          <Row label="Battery serial" value={unit.serial} mono />
          <Row label="Model" value={unit.model} />
          <Row label="Warehouse" value={unit.warehouse} />
          <Row label="Status" value={unit.status} />
          <Row label="Age" value={unit.ageBand} />
          <Row label="Received" value={unit.receivedOn} />
          <Row label="SOH" value={`${unit.sohPct}%`} accent />
          <Row label="Estimated recovery" value={formatCurrency(unit.estRecoveryValue)} accent />
          {unit.note && (
            <div className="rounded-lg bg-accent-amber/10 border border-accent-amber/30 px-3 py-2 text-[11px] text-accent-amber">
              {unit.note}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, mono, accent }: { label: string; value: string; mono?: boolean; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 pb-2">
      <span className="text-gray-400">{label}</span>
      <span className={cn("text-right", mono && "font-mono", accent ? "text-white font-bold" : "text-gray-200")}>{value}</span>
    </div>
  );
}
