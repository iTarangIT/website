import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: number;
  median: number;
  topQuartile: number;
  unit?: string;
  higherIsBetter: boolean;
  format?: (n: number) => string;
}

export default function BenchmarkBar({
  label,
  value,
  median,
  topQuartile,
  higherIsBetter,
  format = (n) => String(n),
}: Props) {
  const max = Math.max(value, median, topQuartile, 1) * 1.1;

  const pct = (n: number) => `${Math.min(100, (n / max) * 100)}%`;

  // Performance color vs median
  const isGood = higherIsBetter ? value >= median : value <= median;
  const isGreat = higherIsBetter ? value >= topQuartile : value <= topQuartile;
  const barColor = isGreat ? "bg-accent-green" : isGood ? "bg-brand-400" : "bg-red-400";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-400">{label}</span>
        <span className={cn("font-bold tabular-nums", isGreat ? "text-accent-green" : isGood ? "text-brand-300" : "text-red-400")}>
          {format(value)}
        </span>
      </div>
      <div className="relative h-6 rounded-md bg-white/5 overflow-visible">
        {/* Driver bar */}
        <div
          className={cn("absolute inset-y-0 left-0 rounded-md transition-all duration-500", barColor)}
          style={{ width: pct(value) }}
        />
        {/* Median marker */}
        <div
          className="absolute inset-y-0 w-px bg-gray-400"
          style={{ left: pct(median) }}
          title={`Area median: ${format(median)}`}
        >
          <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[9px] text-gray-400 whitespace-nowrap">
            med
          </span>
        </div>
        {/* Top quartile marker */}
        <div
          className="absolute inset-y-0 w-px bg-accent-green/70"
          style={{ left: pct(topQuartile) }}
          title={`Top quartile: ${format(topQuartile)}`}
        >
          <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[9px] text-accent-green whitespace-nowrap">
            top 25%
          </span>
        </div>
      </div>
      <div className="flex items-center justify-between text-[10px] text-gray-500 pt-3">
        <span>Area median {format(median)}</span>
        <span>Top 25% {format(topQuartile)}</span>
      </div>
    </div>
  );
}
