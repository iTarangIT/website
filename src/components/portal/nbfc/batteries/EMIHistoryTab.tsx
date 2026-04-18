"use client";

import { cn } from "@/lib/utils";
import { type BatteryRow } from "@/data/portal/loans";

type EMIStatus = "on-time" | "late-1-7" | "late-8-30" | "skipped";

interface EMIRow {
  month: string;
  dueDate: string;
  paidDate?: string;
  amount: number;
  status: EMIStatus;
  daysLate: number;
}

const STATUS_STYLES: Record<EMIStatus, string> = {
  "on-time": "bg-accent-green/15 text-accent-green border-accent-green/30",
  "late-1-7": "bg-brand-500/15 text-brand-200 border-brand-500/30",
  "late-8-30": "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  skipped: "bg-red-500/15 text-red-300 border-red-500/30",
};

function buildHistory(row: BatteryRow): EMIRow[] {
  // Construct 6 synthetic EMIs based on DPD + risk band
  const base = row.overdueDays;
  const shape: EMIStatus[] = base > 30
    ? ["skipped", "skipped", "late-8-30", "late-1-7", "late-1-7", "on-time"]
    : base > 7
    ? ["late-8-30", "late-1-7", "late-1-7", "on-time", "on-time", "on-time"]
    : base > 0
    ? ["late-1-7", "on-time", "on-time", "on-time", "on-time", "on-time"]
    : ["on-time", "on-time", "on-time", "on-time", "on-time", "on-time"];

  const months = ["Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"];
  const emi = Math.round(row.outstanding / 6 / 1000) * 1000 || 3250;

  return shape.map((st, i) => ({
    month: months[i],
    dueDate: `${i + 1} ${months[i].split(" ")[0]}`,
    paidDate: st === "skipped" ? undefined : `${i + 1 + (st === "late-8-30" ? 14 : st === "late-1-7" ? 4 : 0)} ${months[i].split(" ")[0]}`,
    amount: emi,
    status: st,
    daysLate: st === "skipped" ? row.overdueDays : st === "late-8-30" ? 14 : st === "late-1-7" ? 4 : 0,
  }));
}

export default function EMIHistoryTab({ row }: { row: BatteryRow }) {
  const history = buildHistory(row);
  return (
    <div className="rounded-lg border border-white/10 overflow-hidden">
      <table className="w-full text-[11px]">
        <caption className="sr-only">Last six EMIs for this loan.</caption>
        <thead className="bg-black/30 text-gray-500">
          <tr>
            <th scope="col" className="text-left px-3 py-2 font-semibold">EMI</th>
            <th scope="col" className="text-left px-3 py-2 font-semibold">Due</th>
            <th scope="col" className="text-left px-3 py-2 font-semibold">Paid</th>
            <th scope="col" className="text-right px-3 py-2 font-semibold">Amount</th>
            <th scope="col" className="text-right px-3 py-2 font-semibold">Days late</th>
            <th scope="col" className="text-left px-3 py-2 font-semibold">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {history.map((r) => (
            <tr key={r.month} className="hover:bg-white/5">
              <td className="px-3 py-2 text-white font-medium">{r.month}</td>
              <td className="px-3 py-2 text-gray-400">{r.dueDate}</td>
              <td className="px-3 py-2 text-gray-300">{r.paidDate ?? "—"}</td>
              <td className="px-3 py-2 text-gray-200 tabular-nums text-right">
                {new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(r.amount)}
              </td>
              <td className="px-3 py-2 text-gray-200 tabular-nums text-right">{r.daysLate || "—"}</td>
              <td className="px-3 py-2">
                <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", STATUS_STYLES[r.status])}>
                  {r.status.replace("-", " ")}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="px-3 py-2 text-[10px] text-gray-500 border-t border-white/5">
        Feeds directly into visible CDS calculation. Click CDS badge above to see per-row contribution.
      </p>
    </div>
  );
}
