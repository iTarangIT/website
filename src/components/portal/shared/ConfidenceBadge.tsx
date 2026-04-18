import { cn } from "@/lib/utils";

interface Props {
  level: "low" | "medium" | "high";
  title?: string;
}

const STYLES = {
  low: "bg-red-500/15 text-red-300 border-red-500/30",
  medium: "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  high: "bg-accent-green/15 text-accent-green border-accent-green/30",
};

export default function ConfidenceBadge({ level, title }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border capitalize",
        STYLES[level],
      )}
      title={title ?? `Confidence: ${level}`}
    >
      Confidence · {level}
    </span>
  );
}
