import { Clock } from "lucide-react";

interface Props {
  label?: string;
  timestamp?: string;
  stale?: boolean;
}

export default function DataFreshnessBadge({
  label = "Last updated",
  timestamp = "Today, 6:00 AM IST",
  stale = false,
}: Props) {
  return (
    <span
      className={
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border " +
        (stale
          ? "bg-accent-amber/10 border-accent-amber/30 text-accent-amber"
          : "bg-white/5 border-white/10 text-gray-400")
      }
      title={stale ? "Data may be stale" : label}
    >
      <Clock className="h-2.5 w-2.5" />
      {label}: {timestamp}
    </span>
  );
}
