import { cohortRows } from "@/data/portal/loans";
import { cn } from "@/lib/utils";

export default function CohortTable() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/10">
        <h4 className="text-sm font-semibold text-gray-200">Cohort comparison</h4>
        <p className="text-[11px] text-gray-500 mt-0.5">Region × vehicle type · default vs recovery</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <caption className="sr-only">Default rate and recovery rate by region and vehicle type segment.</caption>
          <thead className="bg-black/30 text-gray-500">
            <tr>
              <th scope="col" aria-sort="none" className="text-left px-4 py-2 font-semibold">Segment</th>
              <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">Accounts</th>
              <th scope="col" aria-sort="ascending" className="text-right px-3 py-2 font-semibold">Default rate</th>
              <th scope="col" aria-sort="none" className="text-right px-3 py-2 font-semibold">Recovery rate</th>
              <th scope="col" aria-sort="none" className="text-right px-4 py-2 font-semibold">Avg SOH</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {cohortRows.map((r) => (
              <tr key={r.segment} className="hover:bg-white/5">
                <td className="px-4 py-2 text-gray-200">{r.segment}</td>
                <td className="px-3 py-2 text-gray-300 tabular-nums text-right">{r.accounts.toLocaleString("en-IN")}</td>
                <td className={cn("px-3 py-2 tabular-nums text-right font-semibold", r.defaultRatePct > 12 ? "text-red-300" : r.defaultRatePct > 9 ? "text-accent-amber" : "text-accent-green")}>
                  {r.defaultRatePct}%
                </td>
                <td className={cn("px-3 py-2 tabular-nums text-right font-semibold", r.recoveryRatePct < 55 ? "text-red-300" : r.recoveryRatePct < 65 ? "text-accent-amber" : "text-accent-green")}>
                  {r.recoveryRatePct}%
                </td>
                <td className="px-4 py-2 text-gray-300 tabular-nums text-right">{r.avgSoh}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
