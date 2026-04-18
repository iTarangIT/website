"use client";

import { useMemo, useState, useSyncExternalStore } from "react";
import { cn } from "@/lib/utils";
import { getAuditEntries, subscribeToAudit } from "@/lib/audit-store";
import type { AuditEntry, AuditActionType, AuditStatus } from "@/data/portal/audit-log";
import { ScrollText, Filter, Download } from "lucide-react";

const STATUS_STYLES: Record<AuditStatus, string> = {
  completed: "bg-accent-green/15 text-accent-green border-accent-green/30",
  "pending-approval": "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  rejected: "bg-red-500/15 text-red-300 border-red-500/30",
};

const ACTION_CATEGORIES: { id: "all" | "borrower" | "admin"; label: string; match: (t: AuditActionType) => boolean }[] = [
  { id: "all", label: "All", match: () => true },
  {
    id: "borrower",
    label: "Borrower-impacting",
    match: (t) =>
      t.startsWith("immobilization") ||
      t === "remobilization" ||
      t === "restructuring-review" ||
      t === "payment-reminder" ||
      t === "field-visit" ||
      t === "score-override" ||
      t === "consent-withdraw",
  },
  {
    id: "admin",
    label: "Admin privileged",
    match: (t) =>
      t === "threshold-change" ||
      t.startsWith("auction-") ||
      t === "reserve-price-set" ||
      t === "winning-bid-approved" ||
      t === "data-export" ||
      t === "pii-access" ||
      t === "bid-placed",
  },
];

export default function AuditLogTable() {
  const entries = useSyncExternalStore(
    (cb) => subscribeToAudit(cb),
    () => getAuditEntries(),
    () => getAuditEntries(),
  );

  const [category, setCategory] = useState<"all" | "borrower" | "admin">("all");
  const [statusFilter, setStatusFilter] = useState<AuditStatus | "all">("all");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const catMatcher = ACTION_CATEGORIES.find((c) => c.id === category)!.match;
    return entries.filter((e: AuditEntry) => {
      if (!catMatcher(e.actionType)) return false;
      if (statusFilter !== "all" && e.status !== statusFilter) return false;
      if (query && !`${e.entity} ${e.actionLabel} ${e.requestedBy} ${e.reasonCode}`.toLowerCase().includes(query.toLowerCase()))
        return false;
      return true;
    });
  }, [entries, category, statusFilter, query]);

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
            <ScrollText className="h-4 w-4" />
            Audit log
          </h4>
          <p className="text-[11px] text-gray-500 mt-0.5">
            {filtered.length} of {entries.length} entries · immutable · RBI DL compliant
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-[11px]">
            <Filter className="h-3 w-3 text-gray-500" />
            {ACTION_CATEGORIES.map((c) => (
              <button
                key={c.id}
                onClick={() => setCategory(c.id)}
                className={cn(
                  "px-2 py-1 rounded-md transition-colors",
                  category === c.id ? "bg-brand-500 text-white" : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10",
                )}
              >
                {c.label}
              </button>
            ))}
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as AuditStatus | "all")}
            className="bg-white/5 border border-white/10 text-white text-[11px] rounded-md px-2 py-1 focus:outline-none"
          >
            <option value="all" className="bg-gray-950">All status</option>
            <option value="completed" className="bg-gray-950">Completed</option>
            <option value="pending-approval" className="bg-gray-950">Pending</option>
            <option value="rejected" className="bg-gray-950">Rejected</option>
          </select>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search entity, user…"
            className="bg-white/5 border border-white/10 text-white text-[11px] rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-brand-400 w-40"
          />
          <button
            disabled
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] text-gray-500 bg-white/5 border border-white/10 cursor-not-allowed"
            title="Available in production — requires MFA + purpose declaration"
          >
            <Download className="h-3 w-3" />
            Export
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <caption className="sr-only">All privileged actions across the platform.</caption>
          <thead className="bg-black/30 text-gray-500">
            <tr>
              <th scope="col" className="text-left px-4 py-2.5 font-semibold">Timestamp</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Entity</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Action</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Reason</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Requested by</th>
              <th scope="col" className="text-left px-3 py-2.5 font-semibold">Approved by</th>
              <th scope="col" className="text-left px-4 py-2.5 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {filtered.slice(0, 60).map((e) => (
              <tr key={e.id} className="hover:bg-white/5">
                <td className="px-4 py-2 text-gray-400 whitespace-nowrap font-mono">{e.timestamp}</td>
                <td className="px-3 py-2 text-gray-300 whitespace-nowrap font-mono">{e.entity}</td>
                <td className="px-3 py-2 text-gray-200">
                  <div>{e.actionLabel}</div>
                  {(e.beforeValue || e.afterValue) && (
                    <div className="text-[10px] text-gray-500 mt-0.5">
                      {e.beforeValue && <>was <span className="text-gray-300">{e.beforeValue}</span></>}
                      {e.beforeValue && e.afterValue && " → "}
                      {e.afterValue && <><span className="text-accent-green">{e.afterValue}</span></>}
                    </div>
                  )}
                </td>
                <td className="px-3 py-2 text-gray-400">{e.reasonCode}</td>
                <td className="px-3 py-2 text-gray-300 whitespace-nowrap">{e.requestedBy}</td>
                <td className="px-3 py-2 text-gray-400 whitespace-nowrap">{e.approvedBy ?? "—"}</td>
                <td className="px-4 py-2">
                  <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", STATUS_STYLES[e.status])}>
                    {e.status === "pending-approval" ? "Pending" : e.status}
                  </span>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">No audit entries match the current filter.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {filtered.length > 60 && (
        <div className="px-5 py-3 text-center text-[11px] text-gray-500 border-t border-white/10">
          Showing first 60 of {filtered.length} entries. Refine filters to narrow further.
        </div>
      )}
    </section>
  );
}
