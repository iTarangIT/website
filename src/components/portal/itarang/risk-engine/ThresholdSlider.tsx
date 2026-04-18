"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import DualApprovalModal from "@/components/portal/shared/DualApprovalModal";
import type { Threshold } from "@/data/portal/risk-thresholds";

interface Props {
  threshold: Threshold;
}

export default function ThresholdSlider({ threshold }: Props) {
  const [value, setValue] = useState(threshold.currentValue);
  const [pendingValue, setPendingValue] = useState<number | null>(null);

  const dirty = value !== threshold.currentValue;

  const apply = () => {
    setPendingValue(value);
  };

  const confirmed = () => {
    // Value has been "committed" server-side in the mock.
    setPendingValue(null);
  };

  return (
    <article className="rounded-xl bg-white/5 border border-white/10 p-5 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{threshold.label}</p>
          <p className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">{threshold.description}</p>
        </div>
        <span className="text-[10px] text-gray-500 shrink-0">{threshold.affectsAccounts.toLocaleString("en-IN")} accounts</span>
      </div>

      <div className="flex items-center gap-3">
        <input
          type="range"
          min={threshold.min}
          max={threshold.max}
          step={threshold.step}
          value={value}
          onChange={(e) => setValue(parseFloat(e.target.value))}
          className="flex-1 accent-brand-500"
        />
        <div className="w-24 shrink-0 text-right">
          <p className="text-[10px] uppercase tracking-wider text-gray-500">Current</p>
          <p className={cn("text-lg font-bold tabular-nums", dirty ? "text-accent-amber" : "text-white")}>
            {value.toFixed(threshold.step < 1 ? 2 : 0)}
            {threshold.unit && <span className="text-[10px] text-gray-400 ml-1">{threshold.unit}</span>}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] text-gray-500">
          Range {threshold.min}–{threshold.max}{threshold.unit ? ` ${threshold.unit}` : ""}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setValue(threshold.currentValue)}
            disabled={!dirty}
            className="px-2.5 py-1 text-[11px] font-medium rounded-md text-gray-300 hover:bg-white/5 disabled:opacity-40"
          >
            Reset
          </button>
          <button
            onClick={apply}
            disabled={!dirty}
            className="px-2.5 py-1 text-[11px] font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40"
          >
            Apply change
          </button>
        </div>
      </div>

      {pendingValue !== null && (
        <DualApprovalModal
          open={pendingValue !== null}
          onClose={() => setPendingValue(null)}
          onConfirmed={confirmed}
          title={`Change threshold · ${threshold.label}`}
          description="Propagates to the risk engine on next nightly evaluation."
          impact={`This change affects ${threshold.affectsAccounts.toLocaleString("en-IN")} accounts.`}
          approverLabel="Risk Head approval required (MFA sim)"
          beforeLabel="Before"
          beforeValue={`${threshold.currentValue}${threshold.unit ? " " + threshold.unit : ""}`}
          afterLabel="After"
          afterValue={`${pendingValue}${threshold.unit ? " " + threshold.unit : ""}`}
          auditType="threshold-change"
          actionLabel={threshold.label}
          entityLabel="Risk Rule Engine"
          reasonCode="Calibration"
        />
      )}
    </article>
  );
}
