import { portfolioDistribution } from "@/data/portal/loans";

const SEGMENTS = [
  { key: "low", label: "Low", ...portfolioDistribution.low, color: "#10b981" },
  { key: "medium", label: "Medium", ...portfolioDistribution.medium, color: "#5b7bff" },
  { key: "high", label: "High", ...portfolioDistribution.high, color: "#fbbf24" },
  { key: "veryHigh", label: "Very High", ...portfolioDistribution.veryHigh, color: "#ef4444" },
];

export default function RiskDistributionDonut() {
  const total = SEGMENTS.reduce((a, b) => a + b.count, 0);
  const r = 44;
  const circumference = 2 * Math.PI * r;

  const segments = SEGMENTS.map((s, i) => {
    const start = SEGMENTS.slice(0, i).reduce((a, x) => a + x.count, 0);
    return { ...s, startPct: (start / total) * 100 };
  });

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 p-5">
      <h4 className="text-sm font-semibold text-gray-200 mb-3">Portfolio risk distribution</h4>
      <div className="flex items-center gap-5">
        <svg width="120" height="120" viewBox="0 0 120 120" className="shrink-0 -rotate-90">
          {segments.map((s) => {
            const dash = (s.pct / 100) * circumference;
            const gap = circumference - dash;
            const offset = (-s.startPct / 100) * circumference;
            return (
              <circle
                key={s.key}
                cx="60"
                cy="60"
                r={r}
                fill="none"
                stroke={s.color}
                strokeWidth="14"
                strokeDasharray={`${dash} ${gap}`}
                strokeDashoffset={offset}
              />
            );
          })}
          <text x="60" y="62" textAnchor="middle" dominantBaseline="middle" transform="rotate(90 60 60)" fill="white" fontSize="16" fontWeight="700">
            {total.toLocaleString("en-IN")}
          </text>
        </svg>
        <div className="flex-1 space-y-2 min-w-0">
          {segments.map((s) => (
            <div key={s.key} className="flex items-center gap-3 text-xs">
              <span className="h-2 w-2 rounded-full shrink-0" style={{ backgroundColor: s.color }} />
              <span className="text-gray-300 flex-1 truncate">{s.label}</span>
              <span className="text-white font-semibold tabular-nums">{s.pct}%</span>
              <span className="text-gray-500 tabular-nums w-16 text-right">{s.count.toLocaleString("en-IN")}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="text-[10px] text-gray-500 mt-4 border-t border-white/10 pt-2">
        Computed nightly from CDS bands. Each band&apos;s ceiling is controlled by Risk Rule Engine (admin).
      </p>
    </section>
  );
}
