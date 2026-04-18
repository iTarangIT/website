import { dpdBuckets } from "@/data/portal/nbfc-extra-kpis";

export default function DPDBucketBar() {
  const max = Math.max(...dpdBuckets.map((b) => b.count));
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-5">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-gray-200">DPD Distribution</h4>
        <span className="text-[10px] uppercase tracking-wider text-gray-500">Days past due</span>
      </div>
      <div className="space-y-3">
        {dpdBuckets.map((bucket) => (
          <div key={bucket.label} className="flex items-center gap-3">
            <span className="text-xs text-gray-400 w-32 shrink-0">{bucket.label}</span>
            <div className="flex-1 h-5 rounded-full bg-white/5 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${(bucket.count / max) * 100}%`, backgroundColor: bucket.color }}
              />
            </div>
            <span className="text-xs font-medium text-gray-300 w-20 text-right tabular-nums">
              {bucket.count} · ₹{bucket.outstandingLakhs}L
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
