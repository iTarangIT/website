import { cn } from "@/lib/utils";

interface Props {
  score: number;
  size?: number;
  hidden?: boolean;
}

export default function IntentScoreRing({ score, size = 44, hidden = false }: Props) {
  const strokeWidth = 4;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const pct = hidden ? 0 : Math.min(100, Math.max(0, score));
  const dash = (pct / 100) * circumference;
  const color = hidden ? "#4b5563" : score >= 80 ? "#10b981" : score >= 60 ? "#38bdf8" : "#fbbf24";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <span
        className={cn(
          "absolute inset-0 flex items-center justify-center text-[11px] font-bold tabular-nums",
          hidden ? "text-gray-500" : "text-white",
        )}
      >
        {hidden ? "?" : score}
      </span>
    </div>
  );
}
