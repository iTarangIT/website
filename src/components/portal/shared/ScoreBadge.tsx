"use client";

import { cn } from "@/lib/utils";

export type ScoreType = "cds" | "pci" | "intent";

interface Props {
  type: ScoreType;
  value: number;
  onClick?: () => void;
  size?: "sm" | "md";
}

function bandFor(type: ScoreType, value: number): "low" | "medium" | "high" | "very-high" {
  if (type === "pci") {
    // Higher is better — reliable payer
    if (value >= 0.85) return "low";
    if (value >= 0.65) return "medium";
    if (value >= 0.4) return "high";
    return "very-high";
  }
  // CDS / Intent — higher is worse for CDS, for intent we invert
  if (type === "intent") {
    if (value >= 80) return "low";
    if (value >= 50) return "medium";
    if (value >= 30) return "high";
    return "very-high";
  }
  // CDS
  if (value <= 20) return "low";
  if (value <= 40) return "medium";
  if (value <= 60) return "high";
  return "very-high";
}

const COLORS = {
  low: "bg-accent-green/20 text-accent-green border-accent-green/40",
  medium: "bg-brand-500/20 text-brand-200 border-brand-500/40",
  high: "bg-accent-amber/20 text-accent-amber border-accent-amber/40",
  "very-high": "bg-red-500/20 text-red-300 border-red-500/40",
};

const PREFIX: Record<ScoreType, string> = { cds: "CDS", pci: "PCI", intent: "Intent" };

export default function ScoreBadge({ type, value, onClick, size = "sm" }: Props) {
  const band = bandFor(type, value);
  const display = type === "pci" ? value.toFixed(2) : String(Math.round(value));
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!onClick}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-bold tabular-nums transition-opacity",
        size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        COLORS[band],
        onClick ? "hover:opacity-80 cursor-pointer" : "cursor-default",
      )}
      title={onClick ? "Click to see how this score is calculated" : PREFIX[type]}
    >
      {PREFIX[type]} · {display}
    </button>
  );
}
