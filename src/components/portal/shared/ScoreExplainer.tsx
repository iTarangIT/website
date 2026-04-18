"use client";

import { useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Info, Flag } from "lucide-react";
import ConfidenceBadge from "./ConfidenceBadge";

export type ScoreType = "cds" | "pci" | "intent";

interface Props {
  open: boolean;
  onClose: () => void;
  type: ScoreType;
  value: number;
  entityLabel?: string;
  emiHistory?: { when: string; status: string; weight: number; recency: number; penalty: number; contribution: number }[];
  intentInputs?: {
    questionType: string;
    toneKeywords: string[];
    callbackRequested: boolean;
    budgetSignaled: boolean;
    timelineStated: string;
  };
  confidence: "low" | "medium" | "high";
}

const TITLE: Record<ScoreType, string> = {
  cds: "Chronic Default Score (CDS)",
  pci: "Payment Consistency Index (PCI)",
  intent: "Intent Score",
};

const FORMULAS: Record<ScoreType, string> = {
  cds: "CDS = Σ(EMI weight × recency multiplier) + consecutive-default penalty · normalized to 0–100",
  pci: "PCI = Σ(EMI score × age weight) / Σ(age weights) · range 0.0–1.0",
  intent:
    "Intent = w₁·question_type + w₂·tone_positive + w₃·callback + w₄·budget_signal + w₅·timeline · normalized 0–100 (model v0.2-demo)",
};

const LIMITS: Record<ScoreType, string[]> = {
  cds: [
    "Insufficient history: fewer than 3 EMIs observed — score unreliable",
    "Recent restructuring: flag dropped to 'Low' until 2 fresh EMIs observed",
    "Declared force majeure: score should be overridden manually",
  ],
  pci: [
    "Fewer than 3 EMIs → PCI shows 'Insufficient Data'",
    "Does not capture partial payments before settlement period",
    "Use alongside CDS — PCI alone cannot predict default",
  ],
  intent: [
    "Model v0.2-demo — requires sales team validation",
    "Low confidence on leads with < 60s conversation duration",
    "Tone keywords are language-dependent — Hindi/regional require newer model",
  ],
};

export default function ScoreExplainer({
  open,
  onClose,
  type,
  value,
  entityLabel,
  emiHistory,
  intentInputs,
  confidence,
}: Props) {
  const [overrideReason, setOverrideReason] = useState("");
  const [overrideDone, setOverrideDone] = useState(false);

  const submitOverride = () => {
    if (!overrideReason.trim()) return;
    // In a real system this would POST to an audit endpoint; here we just acknowledge.
    setOverrideDone(true);
    setTimeout(() => {
      setOverrideReason("");
      setOverrideDone(false);
      onClose();
    }, 1600);
  };

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-lg bg-gray-950 text-white border-l border-white/10 overflow-y-auto p-0"
      >
        <SheetHeader className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur border-b border-white/10 px-6 py-4">
          <SheetTitle className="text-white">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-base font-semibold">{TITLE[type]}</p>
                {entityLabel && <p className="text-xs text-gray-400 font-normal mt-0.5">{entityLabel}</p>}
              </div>
              <ConfidenceBadge level={confidence} />
            </div>
          </SheetTitle>
        </SheetHeader>

        <div className="px-6 py-6 space-y-6">
          <section>
            <div className="flex items-baseline gap-3">
              <p className="text-5xl font-bold tabular-nums text-white">
                {type === "pci" ? value.toFixed(2) : Math.round(value)}
              </p>
              <p className="text-xs text-gray-500">
                {type === "pci" ? "of 1.0" : "of 100"}
              </p>
            </div>
          </section>

          <section>
            <SectionTitle>Formula</SectionTitle>
            <p className="text-xs text-gray-300 bg-black/30 border border-white/10 rounded-lg px-3 py-2.5 font-mono leading-relaxed">
              {FORMULAS[type]}
            </p>
          </section>

          {emiHistory && emiHistory.length > 0 && (
            <section>
              <SectionTitle>Inputs — last 6 EMIs</SectionTitle>
              <div className="overflow-x-auto rounded-lg border border-white/10">
                <table className="w-full text-[11px]">
                  <thead className="bg-black/30 text-gray-500">
                    <tr>
                      <th className="text-left px-2 py-1.5">EMI</th>
                      <th className="text-left px-2 py-1.5">Status</th>
                      <th className="text-right px-2 py-1.5">Weight</th>
                      <th className="text-right px-2 py-1.5">Recency</th>
                      <th className="text-right px-2 py-1.5">Penalty</th>
                      <th className="text-right px-2 py-1.5">Contrib</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {emiHistory.map((row) => (
                      <tr key={row.when}>
                        <td className="px-2 py-1.5 text-gray-300">{row.when}</td>
                        <td className="px-2 py-1.5 text-gray-300">{row.status}</td>
                        <td className="px-2 py-1.5 text-right text-gray-300 tabular-nums">{row.weight}</td>
                        <td className="px-2 py-1.5 text-right text-gray-300 tabular-nums">{row.recency.toFixed(1)}×</td>
                        <td className="px-2 py-1.5 text-right text-gray-300 tabular-nums">{row.penalty}</td>
                        <td className="px-2 py-1.5 text-right text-white font-semibold tabular-nums">{row.contribution.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {intentInputs && (
            <section>
              <SectionTitle>Inputs</SectionTitle>
              <dl className="grid grid-cols-2 gap-3 text-xs">
                <dt className="text-gray-500">Question type</dt>
                <dd className="text-gray-200">{intentInputs.questionType}</dd>
                <dt className="text-gray-500">Tone keywords</dt>
                <dd className="text-gray-200">{intentInputs.toneKeywords.join(", ")}</dd>
                <dt className="text-gray-500">Callback requested</dt>
                <dd className="text-gray-200">{intentInputs.callbackRequested ? "Yes" : "No"}</dd>
                <dt className="text-gray-500">Budget signalled</dt>
                <dd className="text-gray-200">{intentInputs.budgetSignaled ? "Yes" : "No"}</dd>
                <dt className="text-gray-500">Timeline</dt>
                <dd className="text-gray-200">{intentInputs.timelineStated}</dd>
              </dl>
            </section>
          )}

          <section>
            <SectionTitle>When NOT to trust this score</SectionTitle>
            <ul className="text-xs text-gray-400 space-y-1.5">
              {LIMITS[type].map((l) => (
                <li key={l} className="flex gap-2">
                  <Info className="h-3 w-3 text-accent-amber shrink-0 mt-0.5" />
                  <span>{l}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-lg bg-black/30 border border-white/10 p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Flag className="h-3.5 w-3.5 text-accent-amber" />
              <p className="text-xs font-semibold text-white">Manual override</p>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed">
              Override does not change the computed score. Your reason is logged to the audit trail and used to downgrade the
              severity of follow-up actions for this entity.
            </p>
            <textarea
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="Required: documented reason (e.g. medical emergency, model misclassification)"
              rows={3}
              className="w-full text-xs bg-black/40 border border-white/10 text-white rounded-md px-2.5 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
              disabled={overrideDone}
            />
            <button
              onClick={submitOverride}
              disabled={!overrideReason.trim() || overrideDone}
              className="w-full px-3 py-2 text-xs font-semibold rounded-md bg-accent-amber/20 border border-accent-amber/30 text-accent-amber hover:bg-accent-amber/30 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {overrideDone ? "Override logged · audit updated" : "Submit override"}
            </button>
          </section>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2 pb-1 border-b border-white/10">
      {children}
    </h3>
  );
}
