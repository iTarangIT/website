import { cn } from "@/lib/utils";

export default function ScoreBadge({
  value,
  size = "md",
  className,
}: {
  value: number;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const bucket =
    value >= 80
      ? "bg-green-100 text-green-700 border-green-200"
      : value >= 60
      ? "bg-amber-100 text-amber-700 border-amber-200"
      : "bg-red-100 text-red-700 border-red-200";

  const sizes = {
    sm: "text-[11px] px-2 py-0.5",
    md: "text-xs px-2.5 py-1",
    lg: "text-sm px-3 py-1.5",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-semibold border",
        bucket,
        sizes[size],
        className
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {value}
      <span className="opacity-60">/100</span>
    </span>
  );
}
