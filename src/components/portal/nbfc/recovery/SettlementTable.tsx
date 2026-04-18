import { cn } from "@/lib/utils";
import { settledLots, revenueSummary, type SettledLot } from "@/data/portal/auction";

const STATUS_STYLES: Record<SettledLot["status"], string> = {
  delivered: "bg-accent-green/15 text-accent-green border-accent-green/30",
  "in-transit": "bg-brand-500/15 text-brand-200 border-brand-500/30",
  "payment-pending": "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  "in-progress": "bg-white/10 text-gray-300 border-white/20",
};

const LABEL: Record<SettledLot["status"], string> = {
  delivered: "✅ Delivered",
  "in-transit": "🚚 In transit",
  "payment-pending": "💰 Payment pending",
  "in-progress": "🔄 In progress",
};

function inr(n: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
}

export default function SettlementTable() {
  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/10 flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Post-auction settlement</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">5 most recent settled lots</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <Meta label="Total value" value={`₹${revenueSummary.totalAuctionValueLakhs} L`} />
          <Meta label="Recovery rate" value={`${revenueSummary.recoveryRatePct}%`} accent />
          <Meta label="Premium over base" value={`+${revenueSummary.avgPremiumOverBasePct}%`} accent />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <caption className="sr-only">Five most recent settled auction lots.</caption>
          <thead className="bg-black/30 text-gray-500">
            <tr>
              <th scope="col" className="text-left px-4 py-2 font-semibold">Lot ID</th>
              <th scope="col" className="text-left px-3 py-2 font-semibold">Assets</th>
              <th scope="col" className="text-right px-3 py-2 font-semibold">Base price</th>
              <th scope="col" className="text-right px-3 py-2 font-semibold">Final price</th>
              <th scope="col" className="text-left px-3 py-2 font-semibold">Winner</th>
              <th scope="col" className="text-left px-4 py-2 font-semibold">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {settledLots.map((l) => (
              <tr key={l.id} className="hover:bg-white/5">
                <td className="px-4 py-2 font-mono text-white">{l.id}</td>
                <td className="px-3 py-2 text-gray-300">{l.assets}</td>
                <td className="px-3 py-2 text-gray-400 tabular-nums text-right">{inr(l.basePrice)}</td>
                <td className="px-3 py-2 text-accent-green tabular-nums text-right font-semibold">{inr(l.finalPrice)}</td>
                <td className="px-3 py-2 text-gray-300">{l.winner}</td>
                <td className="px-4 py-2">
                  <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-semibold", STATUS_STYLES[l.status])}>
                    {LABEL[l.status]}
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

function Meta({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className={"font-bold tabular-nums " + (accent ? "text-accent-green" : "text-white")}>{value}</p>
    </div>
  );
}
