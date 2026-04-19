"use client";

import { cn } from "@/lib/utils";
import { Loader2, Sparkles, CheckCircle2, AlertCircle, XCircle, ChevronRight } from "lucide-react";
import type { IntentScore } from "@/lib/lead-store";

interface Props {
  status: "idle" | "scoring" | "done" | "error";
  score?: IntentScore | null;
  error?: string | null;
  onRetry?: () => void;
}

const ACTION_STYLES: Record<IntentScore["recommendedAction"], { chip: string; label: string; icon: typeof CheckCircle2 }> = {
  qualify: { chip: "bg-accent-green/20 border-accent-green/40 text-accent-green", label: "Hand to sales team", icon: CheckCircle2 },
  nurture: { chip: "bg-accent-amber/20 border-accent-amber/40 text-accent-amber", label: "Nurture — re-dial", icon: AlertCircle },
  disqualify: { chip: "bg-red-500/20 border-red-500/40 text-red-300", label: "Disqualify", icon: XCircle },
};

const DIMENSION_LABELS: Record<keyof IntentScore["dimensions"], string> = {
  intent: "Intent",
  productKnowledge: "Product knowledge",
  customerRequirement: "Customer requirement",
  budgetReadiness: "Budget readiness",
  timelineClarity: "Timeline",
};

function scoreColor(n: number): string {
  if (n >= 80) return "text-accent-green";
  if (n >= 60) return "text-brand-200";
  if (n >= 40) return "text-accent-amber";
  return "text-red-300";
}

function barBg(n: number): string {
  if (n >= 80) return "bg-accent-green";
  if (n >= 60) return "bg-brand-400";
  if (n >= 40) return "bg-accent-amber";
  return "bg-red-400";
}

export default function IntentScorePanel({ status, score, error, onRetry }: Props) {
  if (status === "idle") return null;

  if (status === "scoring") {
    return (
      <section className="rounded-lg bg-brand-500/10 border border-brand-500/30 p-4 flex items-center gap-3">
        <Loader2 className="h-4 w-4 animate-spin text-brand-200" />
        <div>
          <p className="text-xs font-semibold text-white">Scoring this lead…</p>
          <p className="text-[10px] text-brand-200 mt-0.5">
            Running transcript + call history through the intent model.
          </p>
        </div>
      </section>
    );
  }

  if (status === "error") {
    return (
      <section role="alert" className="rounded-lg bg-red-500/10 border border-red-500/30 p-3 space-y-2">
        <p className="text-xs font-semibold text-red-200">Intent scoring failed</p>
        <p className="text-[11px] text-red-200/80">{error ?? "Unknown error"}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold rounded-md bg-red-500/20 border border-red-500/30 text-red-200 hover:bg-red-500/30"
          >
            Retry scoring
          </button>
        )}
      </section>
    );
  }

  if (!score) return null;
  const action = ACTION_STYLES[score.recommendedAction];
  const ActionIcon = action.icon;

  return (
    <section className="rounded-lg bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-accent-amber" />
          <p className="text-xs font-bold uppercase tracking-wider text-gray-300">Intent score</p>
        </div>
        <span
          className={cn("inline-flex items-center gap-1.5 px-2 py-1 rounded-full border text-[10px] font-bold uppercase tracking-wider", action.chip)}
        >
          <ActionIcon className="h-3 w-3" />
          {action.label}
          <ChevronRight className="h-2.5 w-2.5 opacity-60" />
        </span>
      </div>

      <div className="p-4 space-y-4">
        <div className="flex items-baseline gap-3">
          <p className={cn("text-4xl font-bold tabular-nums", scoreColor(score.overall))}>{score.overall}</p>
          <p className="text-xs text-gray-500">overall · 0–100</p>
          {score.modelUsed && (
            <p className="ml-auto text-[10px] text-gray-600 font-mono">{score.modelUsed}</p>
          )}
        </div>

        <div className="space-y-2">
          {(Object.keys(DIMENSION_LABELS) as (keyof IntentScore["dimensions"])[]).map((k) => {
            const v = score.dimensions[k];
            return (
              <div key={k} className="flex items-center gap-3 text-[11px]">
                <span className="text-gray-400 w-36 shrink-0">{DIMENSION_LABELS[k]}</span>
                <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className={cn("h-full rounded-full transition-all duration-500", barBg(v))} style={{ width: `${v}%` }} />
                </div>
                <span className={cn("tabular-nums font-semibold w-8 text-right", scoreColor(v))}>{v}</span>
              </div>
            );
          })}
        </div>

        <div className="rounded-md bg-black/30 border border-white/5 p-3 text-[11px] text-gray-300 leading-relaxed italic">
          {score.rationale}
        </div>
      </div>
    </section>
  );
}
