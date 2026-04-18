import { cn } from "@/lib/utils";
import { buybackRequests, buybackPricingRules, type BuybackStatus } from "@/data/portal/buybacks";

const STATUS_STYLES: Record<BuybackStatus, string> = {
  "pending-evaluation": "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  "offer-made": "bg-brand-500/15 text-brand-200 border-brand-500/30",
  accepted: "bg-accent-green/15 text-accent-green border-accent-green/30",
  rejected: "bg-red-500/15 text-red-300 border-red-500/30",
};

function inr(n: number | null) {
  if (n === null) return "—";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
}

export default function BuybackRequests() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Buyback requests</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">5 customer requests · tooltip on offer shows pricing rules</p>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <caption className="sr-only">Customer buyback requests with current status and offer.</caption>
          <thead className="bg-black/30 text-gray-500">
            <tr>
              <th scope="col" className="text-left px-4 py-2 font-semibold">Customer</th>
              <th scope="col" className="text-left px-3 py-2 font-semibold">Battery</th>
              <th scope="col" className="text-right px-3 py-2 font-semibold">SOH</th>
              <th scope="col" className="text-left px-3 py-2 font-semibold">Requested</th>
              <th scope="col" className="text-left px-3 py-2 font-semibold">Evaluation</th>
              <th
                scope="col"
                className="text-right px-3 py-2 font-semibold"
                title={`${buybackPricingRules.highSoh.note} · ${buybackPricingRules.midSoh.note} · ${buybackPricingRules.lowSoh.note}`}
              >
                Offer
              </th>
              <th scope="col" className="text-left px-4 py-2 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {buybackRequests.map((r) => (
              <tr key={r.id} className="hover:bg-white/5">
                <td className="px-4 py-2 text-white">{r.customer}</td>
                <td className="px-3 py-2 font-mono text-gray-300">{r.batteryId}</td>
                <td className="px-3 py-2 text-gray-200 tabular-nums text-right">{r.sohPct}%</td>
                <td className="px-3 py-2 text-gray-400">{r.requestDate}</td>
                <td className="px-3 py-2 text-gray-300 capitalize">{r.evaluationStatus.replace("-", " ")}</td>
                <td className="px-3 py-2 text-right font-semibold tabular-nums text-white">{inr(r.offer)}</td>
                <td className="px-4 py-2">
                  <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", STATUS_STYLES[r.status])}>
                    {r.status.replace("-", " ")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
