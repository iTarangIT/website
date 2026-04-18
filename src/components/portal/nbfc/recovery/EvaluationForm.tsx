"use client";

import { useMemo, useState } from "react";
import { ChevronRight, ChevronLeft, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

type Step = 1 | 2 | 3;

export default function EvaluationForm() {
  const [step, setStep] = useState<Step>(1);

  // Step 1
  const [sohPct, setSohPct] = useState<string>("78");
  const [physical, setPhysical] = useState<"Good" | "Fair" | "Poor">("Fair");
  const [manufacture, setManufacture] = useState("2024-03");
  const [iot, setIot] = useState<"Online" | "Intermittent" | "Offline">("Online");
  const [bms, setBms] = useState<"Healthy" | "Warning" | "Fault">("Healthy");
  const [charger, setCharger] = useState<"Standard" | "Fast">("Standard");
  const [model, setModel] = useState("48V 100AH");

  // Step 2
  const [refurbType, setRefurbType] = useState<"Minor Repair" | "Cell Replacement" | "Scrap">("Minor Repair");
  const [refurbCost, setRefurbCost] = useState<string>("3200");
  const [actions, setActions] = useState<Record<string, boolean>>({
    terminalCleaning: true,
    softwareRecalibration: true,
    warrantyReset: false,
  });

  // Step 3
  const [outcome, setOutcome] = useState<"approve" | "scrap" | "hold" | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const originalValue = useMemo(() => {
    if (model.startsWith("48V")) return 45000;
    if (model.startsWith("60V")) return 58000;
    if (model.startsWith("72V")) return 75000;
    return 50000;
  }, [model]);

  const suggestedBasePrice = useMemo(() => {
    const sohNum = parseFloat(sohPct) || 0;
    const factor = sohNum > 80 ? 0.65 : sohNum > 70 ? 0.6 : 0.5;
    const refurbNum = parseFloat(refurbCost) || 0;
    return Math.max(0, Math.round(originalValue * factor - refurbNum));
  }, [sohPct, refurbCost, originalValue]);

  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <div className="px-5 py-4 border-b border-white/10">
        <h4 className="text-sm font-semibold text-gray-200">Battery evaluation</h4>
        <p className="text-[11px] text-gray-500 mt-0.5">Step {step} of 3 · multi-step form with accessibility labels</p>
      </div>

      <div className="px-5 py-5 space-y-4">
        {/* Stepper */}
        <ol className="flex items-center gap-2 text-[11px]">
          {([1, 2, 3] as Step[]).map((s) => (
            <li
              key={s}
              className={cn(
                "flex items-center gap-2",
                step === s ? "text-white font-bold" : step > s ? "text-accent-green" : "text-gray-500",
              )}
            >
              <span
                className={cn(
                  "h-5 w-5 rounded-full border flex items-center justify-center text-[10px]",
                  step === s ? "border-brand-400 bg-brand-500/30" : step > s ? "border-accent-green bg-accent-green/20" : "border-white/10",
                )}
              >
                {step > s ? <CheckCircle2 className="h-3 w-3" /> : s}
              </span>
              {s === 1 ? "Technical" : s === 2 ? "Refurbishment" : "Pricing"}
              {s < 3 && <ChevronRight className="h-3 w-3 text-gray-600" />}
            </li>
          ))}
        </ol>

        {submitted ? (
          <div className="py-6 text-center space-y-2">
            <div className="h-10 w-10 rounded-full bg-accent-green/20 border border-accent-green/40 flex items-center justify-center mx-auto">
              <CheckCircle2 className="h-5 w-5 text-accent-green" />
            </div>
            <p className="text-sm font-semibold text-white">Evaluation recorded</p>
            <p className="text-[11px] text-gray-500">Audit entry logged · lot queued for next step</p>
          </div>
        ) : step === 1 ? (
          <form className="grid md:grid-cols-2 gap-4 text-xs">
            <Field label="SOH %" required>
              <input value={sohPct} onChange={(e) => setSohPct(e.target.value)} inputMode="numeric" className={inputCls} required />
            </Field>
            <Field label="Physical condition" required>
              <select value={physical} onChange={(e) => setPhysical(e.target.value as "Good" | "Fair" | "Poor")} className={inputCls}>
                <option className="bg-gray-950">Good</option>
                <option className="bg-gray-950">Fair</option>
                <option className="bg-gray-950">Poor</option>
              </select>
            </Field>
            <Field label="Manufacturing month" required>
              <input value={manufacture} onChange={(e) => setManufacture(e.target.value)} placeholder="YYYY-MM" className={inputCls} required />
            </Field>
            <Field label="IoT status" required>
              <select value={iot} onChange={(e) => setIot(e.target.value as "Online" | "Intermittent" | "Offline")} className={inputCls}>
                <option className="bg-gray-950">Online</option>
                <option className="bg-gray-950">Intermittent</option>
                <option className="bg-gray-950">Offline</option>
              </select>
            </Field>
            <Field label="BMS health" required>
              <select value={bms} onChange={(e) => setBms(e.target.value as "Healthy" | "Warning" | "Fault")} className={inputCls}>
                <option className="bg-gray-950">Healthy</option>
                <option className="bg-gray-950">Warning</option>
                <option className="bg-gray-950">Fault</option>
              </select>
            </Field>
            <Field label="Charger type">
              <select value={charger} onChange={(e) => setCharger(e.target.value as "Standard" | "Fast")} className={inputCls}>
                <option className="bg-gray-950">Standard</option>
                <option className="bg-gray-950">Fast</option>
              </select>
            </Field>
            <Field label="Model">
              <input value={model} onChange={(e) => setModel(e.target.value)} className={inputCls} />
            </Field>
          </form>
        ) : step === 2 ? (
          <form className="space-y-4 text-xs">
            <Field label="Refurbishment type" required>
              <select value={refurbType} onChange={(e) => setRefurbType(e.target.value as "Minor Repair" | "Cell Replacement" | "Scrap")} className={inputCls}>
                <option className="bg-gray-950">Minor Repair</option>
                <option className="bg-gray-950">Cell Replacement</option>
                <option className="bg-gray-950">Scrap</option>
              </select>
            </Field>
            <Field label="Estimated cost (₹)" required>
              <input value={refurbCost} onChange={(e) => setRefurbCost(e.target.value)} inputMode="numeric" className={inputCls} required />
            </Field>
            <div>
              <p className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2">Actions checklist</p>
              <div className="space-y-1.5">
                {[
                  ["terminalCleaning", "Terminal cleaning"],
                  ["softwareRecalibration", "Software recalibration"],
                  ["warrantyReset", "Warranty reset"],
                ].map(([key, label]) => (
                  <label key={key} className="flex items-center gap-2 text-xs text-gray-200">
                    <input
                      type="checkbox"
                      checked={!!actions[key]}
                      onChange={() => setActions((prev) => ({ ...prev, [key]: !prev[key] }))}
                      className="h-3.5 w-3.5 rounded border-gray-600 bg-black/30"
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
          </form>
        ) : (
          <div className="text-xs space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <Readout label="Original value" value={inr(originalValue)} />
              <Readout label="Refurb cost" value={inr(parseFloat(refurbCost) || 0)} />
              <Readout label="Suggested base price" value={inr(suggestedBasePrice)} accent />
            </div>
            <p className="text-[11px] text-gray-500 leading-relaxed">
              Formula: <span className="text-gray-300 font-mono">base = original × SOH-band factor − refurb cost</span>. Override by
              routing the lot through the Auction Control Centre.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <OutcomeBtn selected={outcome === "approve"} onClick={() => setOutcome("approve")} label="Approve for auction" />
              <OutcomeBtn selected={outcome === "scrap"} onClick={() => setOutcome("scrap")} label="Send to scrap" variant="danger" />
              <OutcomeBtn selected={outcome === "hold"} onClick={() => setOutcome("hold")} label="Hold" variant="neutral" />
            </div>
          </div>
        )}

        {/* Navigation */}
        {!submitted && (
          <div className="flex items-center justify-between pt-3 border-t border-white/10">
            <button
              onClick={() => setStep((s) => (s === 1 ? 1 : ((s - 1) as Step)))}
              disabled={step === 1}
              className="inline-flex items-center gap-1 px-3 py-2 text-xs text-gray-300 rounded-md hover:bg-white/5 disabled:opacity-40"
            >
              <ChevronLeft className="h-3 w-3" /> Back
            </button>
            {step < 3 ? (
              <button
                onClick={() => setStep((s) => Math.min(3, s + 1) as Step)}
                className="inline-flex items-center gap-1 px-3 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600"
              >
                Next <ChevronRight className="h-3 w-3" />
              </button>
            ) : (
              <button
                onClick={() => setSubmitted(true)}
                disabled={!outcome}
                className="px-3 py-2 text-xs font-semibold rounded-md bg-accent-green text-white hover:bg-accent-green/90 disabled:opacity-40"
              >
                Submit evaluation
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

const inputCls =
  "w-full bg-white/5 border border-white/10 text-white text-xs rounded-md px-2.5 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400";

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-1">
        {label}
        {required && <span className="text-red-400 ml-0.5">*</span>}
      </span>
      {children}
    </label>
  );
}

function Readout({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className={"text-lg font-bold tabular-nums mt-1 " + (accent ? "text-accent-green" : "text-white")}>{value}</p>
    </div>
  );
}

function OutcomeBtn({
  label,
  selected,
  onClick,
  variant = "default",
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
  variant?: "default" | "danger" | "neutral";
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 text-[11px] font-semibold rounded-md border",
        selected
          ? variant === "danger"
            ? "bg-red-500/20 border-red-500/40 text-red-300"
            : variant === "neutral"
            ? "bg-white/10 border-white/20 text-white"
            : "bg-accent-green/20 border-accent-green/40 text-accent-green"
          : "bg-white/5 border-white/10 text-gray-300 hover:bg-white/10",
      )}
    >
      {label}
    </button>
  );
}

function inr(n: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
}
