"use client";

// Public Loan Calculator — port of the CRM dealer-portal calculator with the
// same Card 1 (inputs) / Card 2 (scheme cards) UI. Differences from the CRM:
// - Per-search WhatsApp OTP: clicking "Calculate schemes" opens
//   <CalculatorVerifyModal>. Each verification is single-use — it mints a fresh
//   signed cookie for exactly one calculation, so EVERY search needs a new OTP.
//   Changing any input clears the last result so stale numbers never linger.
// - Calls the public /api/calculator/* routes (cookie-gated + rate-limited).
// - No WhatsApp results delivery.

import { useEffect, useState } from "react";
import {
  Loader2,
  Calculator,
  Phone,
  Mail,
  MessageCircle,
  AlertCircle,
  ShieldCheck,
} from "lucide-react";
import { maskPhone } from "@/lib/otp";
import { SchemeCardView } from "@/components/products/calculator/SchemeCardView";
import CalculatorVerifyModal, {
  type VerifiedLead,
} from "@/components/products/calculator/CalculatorVerifyModal";
import type { CalcResponse, ConfigMeta } from "@/components/products/calculator/types";

// Remembered only to PREFILL the modal's name/phone for convenience — it never
// grants access; a fresh OTP is still required for every calculation.
const PREFILL_KEY = "itarang_calculator_prefill";

interface FormState {
  city: string;
  modelId: string;
  tenure: string;
  expectedEmi: string;
  upfrontAbility: string;
}

const EMPTY: FormState = {
  city: "",
  modelId: "",
  tenure: "",
  expectedEmi: "",
  upfrontAbility: "",
};

function readPrefill(): { name: string; phone: string } {
  try {
    const stored = JSON.parse(localStorage.getItem(PREFILL_KEY) || "null");
    if (stored && typeof stored.name === "string" && typeof stored.phone === "string") {
      return { name: stored.name, phone: stored.phone };
    }
  } catch {
    // corrupt/unavailable storage → no prefill
  }
  return { name: "", phone: "" };
}

export default function LoanCalculator() {
  const [meta, setMeta] = useState<ConfigMeta | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [result, setResult] = useState<CalcResponse | null>(null);
  const [lastVerified, setLastVerified] = useState<VerifiedLead | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [prefill, setPrefill] = useState<{ name: string; phone: string }>({ name: "", phone: "" });

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/calculator/config");
        const data = await res.json();
        if (data.success) setMeta(data.data as ConfigMeta);
        else setMetaError(data.error?.message ?? "Failed to load calculator config.");
      } catch {
        setMetaError("Failed to load calculator config.");
      }
    })();
  }, []);

  useEffect(() => {
    setPrefill(readPrefill());
  }, []);

  // Changing any input invalidates the shown result — the next "Calculate
  // schemes" must re-verify with a fresh OTP.
  const set = (k: keyof FormState, v: string) =>
    setForm((f) => {
      setResult(null);
      setError(null);
      return { ...f, [k]: v };
    });

  // Step 1 — the "Calculate schemes" button. Validate, then require a fresh OTP.
  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.modelId || !form.tenure) {
      setError("Please select a battery model and tenure.");
      return;
    }
    setResult(null);
    setModalOpen(true);
  }

  // Step 2 — the modal verified a fresh OTP (single-use cookie is now set).
  // Run exactly one calculation with the verified {name, phone}.
  async function handleVerified(lead: VerifiedLead) {
    setModalOpen(false);
    setLastVerified(lead);
    try {
      localStorage.setItem(PREFILL_KEY, JSON.stringify(lead));
    } catch {
      // storage unavailable — prefill is best-effort only
    }
    setPrefill(lead);
    await runCalculate(lead);
  }

  async function runCalculate(lead: VerifiedLead) {
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/calculator/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customerName: lead.name,
          phone: lead.phone,
          city: form.city || null,
          modelId: Number(form.modelId),
          tenure: Number(form.tenure),
          expectedEmi: form.expectedEmi ? Number(form.expectedEmi) : undefined,
          upfrontAbility: form.upfrontAbility ? Number(form.upfrontAbility) : undefined,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setResult(data.data as CalcResponse);
      } else if (data.error?.code === "verification_required") {
        // Single-use cookie already consumed/expired — ask for a fresh OTP.
        setError("Your verification expired. Please verify again to calculate.");
      } else {
        setError(data.error?.message ?? "Calculation failed.");
      }
    } catch {
      setError("Calculation failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="font-sans">
      {metaError && (
        <div className="mb-6 flex items-center gap-2 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4" /> {metaError}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[380px_1fr]">
        {/* Card 1 — inputs */}
        <form onSubmit={onSubmit} className="h-fit rounded-2xl border border-gray-200 bg-white p-6 shadow-sm ring-1 ring-gray-900/[0.02] lg:sticky lg:top-24">
          <h2 className="mb-4 text-xs font-bold uppercase tracking-widest text-brand-500">Your details</h2>

          {/* Per-search verification notice */}
          <div className="mb-3 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5">
            <ShieldCheck className="h-4 w-4 shrink-0 text-emerald-600" />
            {result && lastVerified ? (
              <p className="text-xs font-semibold text-emerald-800">
                Verified for this search: {lastVerified.name} · {maskPhone(lastVerified.phone)}
              </p>
            ) : (
              <p className="text-xs font-medium text-emerald-800">
                You&apos;ll verify your number on WhatsApp for each search.
              </p>
            )}
          </div>

          <div className="space-y-3">
            <Field label="City">
              <select className={inputCls} value={form.city} onChange={(e) => set("city", e.target.value)}>
                <option value="">Any (Pan-India NBFCs only)</option>
                {meta?.cities.map((c) => (
                  <option key={c.normalized} value={c.normalized}>
                    {c.display}
                    {c.stateCode ? `, ${c.stateCode}` : ""}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Battery model" required>
              <select className={inputCls} value={form.modelId} onChange={(e) => set("modelId", e.target.value)}>
                <option value="">Select model…</option>
                {meta?.models.map((m) => (
                  <option key={m.id} value={m.id}>{m.displayName}</option>
                ))}
              </select>
            </Field>
            <Field label="Tenure" required>
              <select className={inputCls} value={form.tenure} onChange={(e) => set("tenure", e.target.value)}>
                <option value="">Select tenure…</option>
                {meta?.tenures.map((t) => (
                  <option key={t} value={t}>{t} months</option>
                ))}
              </select>
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label={`Expected EMI${meta?.filters.expectedEmiRequired ? " *" : ""}`}>
                <input className={inputCls} type="number" min={0} value={form.expectedEmi} onChange={(e) => set("expectedEmi", e.target.value)} placeholder="₹/month" />
              </Field>
              <Field label={`Upfront ability${meta?.filters.upfrontRequired ? " *" : ""}`}>
                <input className={inputCls} type="number" min={0} value={form.upfrontAbility} onChange={(e) => set("upfrontAbility", e.target.value)} placeholder="₹ total" />
              </Field>
            </div>
          </div>

          {error && (
            <p className="mt-3 flex items-center gap-1.5 text-xs text-red-600">
              <AlertCircle className="h-3.5 w-3.5" /> {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || !meta}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-brand-600 px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-brand-500/30 transition-all duration-200 hover:from-brand-600 hover:to-brand-700 hover:shadow-xl hover:shadow-brand-500/30 active:scale-[0.99] disabled:opacity-50 disabled:shadow-none"
          >
            {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
            {submitting ? "Calculating…" : "Verify & calculate schemes"}
          </button>
        </form>

        {/* Card 2 — results */}
        <div>
          {!result && (
            <div className="flex h-full min-h-[300px] items-center justify-center rounded-2xl border border-dashed border-gray-300 bg-white/50 text-sm text-gray-400">
              Scheme results will appear here.
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {result.waResults === "sent" && (
                <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2.5 text-sm text-emerald-800">
                  <MessageCircle className="h-4 w-4 shrink-0" />
                  {lastVerified
                    ? `These schemes have been sent to your WhatsApp (${maskPhone(lastVerified.phone)}).`
                    : "These schemes have been sent to your WhatsApp."}
                </div>
              )}
              {result.waResults === "failed" && (
                <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm text-amber-800">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  We couldn&apos;t send these to your WhatsApp right now — they&apos;re shown below.
                </div>
              )}
              <Results result={result} />
            </div>
          )}
        </div>
      </div>

      <CalculatorVerifyModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onVerified={handleVerified}
        initialName={prefill.name}
        initialPhone={prefill.phone.replace(/^\+?91/, "")}
      />
    </div>
  );
}

function Results({ result }: { result: CalcResponse }) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
        <p className="text-sm text-gray-500">
          Model <span className="font-semibold text-gray-900">{result.model.displayName}</span> ·{" "}
          {result.qualified.length} qualified, {result.stretch.length} next-best
        </p>
      </div>

      {result.qualified.length > 0 && (
        <section>
          <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-gray-500">Qualified schemes</h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {result.qualified.map((c) => (
              <SchemeCardView key={`${c.nbfc}-${c.schemeCode}`} card={c} />
            ))}
          </div>
        </section>
      )}

      {result.stretch.length > 0 && (
        <section>
          <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-gray-500">
            {result.outcome === "stretch_only" ? "Closest to qualify" : "Next best (stretch to qualify)"}
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {result.stretch.map((c) => (
              <SchemeCardView key={`${c.nbfc}-${c.schemeCode}`} card={c} />
            ))}
          </div>
        </section>
      )}

      {result.outcome === "none" && (
        <div className="rounded-2xl border border-gray-200 bg-white px-5 py-6 text-center text-sm text-gray-500">
          No schemes qualify or are close for these filters. Please reach out to your
          nearest iTarang dealer — we may still be able to help.
        </div>
      )}

      {/* Footer — disclaimer + contact (admin-editable, from calc_settings) */}
      <footer className="rounded-2xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
        <p className="text-xs text-gray-500">{result.footer.disclaimer}</p>
        <div className="mt-3 flex flex-wrap gap-4 text-xs font-medium text-gray-700">
          <a href={`tel:${result.footer.phone}`} className="flex items-center gap-1.5 hover:text-gray-900">
            <Phone className="h-3.5 w-3.5" /> {result.footer.phone}
          </a>
          <a href={`mailto:${result.footer.email}`} className="flex items-center gap-1.5 hover:text-gray-900">
            <Mail className="h-3.5 w-3.5" /> {result.footer.email}
          </a>
          <a
            href={`https://wa.me/${result.footer.whatsapp.replace(/[^0-9]/g, "")}`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 hover:text-gray-900"
          >
            <MessageCircle className="h-3.5 w-3.5" /> {result.footer.whatsapp}
          </a>
        </div>
      </footer>
    </div>
  );
}

const inputCls =
  "w-full rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-brand-400 focus:bg-white focus:ring-2 focus:ring-brand-100";

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-gray-600">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </span>
      {children}
    </label>
  );
}
