import { riskBandDistribution, portfolioHealth } from "@/data/portal/nbfc-extra-kpis";

export default function RiskBandDonut() {
  const total = riskBandDistribution.reduce((a, b) => a + b.count, 0);

  const segments = riskBandDistribution.map((r, i) => {
    const start = riskBandDistribution.slice(0, i).reduce((a, x) => a + x.count, 0);
    const end = start + r.count;
    return {
      ...r,
      startPct: (start / total) * 100,
      endPct: (end / total) * 100,
    };
  });

  const r = 32;
  const circumference = 2 * Math.PI * r;

  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-5">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-sm font-semibold text-gray-200">CDS Risk Bands</h4>
        <span className="text-[10px] uppercase tracking-wider text-gray-500">Chronic default score</span>
      </div>
      <div className="flex items-center gap-5">
        <svg width="96" height="96" viewBox="0 0 96 96" className="shrink-0 -rotate-90">
          {segments.map((s) => {
            const pct = (s.endPct - s.startPct) / 100;
            const dash = pct * circumference;
            const gap = circumference - dash;
            const offset = -s.startPct / 100 * circumference;
            return (
              <circle
                key={s.band}
                cx="48"
                cy="48"
                r={r}
                fill="none"
                stroke={s.color}
                strokeWidth="12"
                strokeDasharray={`${dash} ${gap}`}
                strokeDashoffset={offset}
              />
            );
          })}
          <text
            x="48"
            y="50"
            textAnchor="middle"
            dominantBaseline="middle"
            transform="rotate(90 48 48)"
            fill="white"
            fontSize="14"
            fontWeight="700"
          >
            {portfolioHealth.averageCdsScore}
          </text>
        </svg>
        <div className="flex-1 space-y-1.5 min-w-0">
          {segments.map((s) => (
            <div key={s.band} className="flex items-center gap-2 text-xs">
              <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
              <span className="text-gray-300 truncate">{s.band}</span>
              <span className="ml-auto font-medium text-gray-400 tabular-nums">{s.count}</span>
            </div>
          ))}
          <p className="text-[10px] text-gray-500 pt-1">Avg PCI: <span className="text-gray-300 font-medium">{portfolioHealth.avgPci}</span></p>
        </div>
      </div>
    </div>
  );
}
