"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ShieldCheck, Key, ArrowRight } from "lucide-react";
import { appendAuditEntry } from "@/lib/audit-store";
import type { AuditActionType } from "@/data/portal/audit-log";

interface Props {
  open: boolean;
  onClose: () => void;
  title: string;
  description: string;
  impact: string;                 // "affects 1,124 accounts"
  approverLabel: string;          // "Risk Head approval required"
  beforeLabel?: string;
  beforeValue?: string;
  afterLabel?: string;
  afterValue?: string;
  auditType: AuditActionType;
  actionLabel: string;
  entityLabel: string;
  reasonCode?: string;
  requireMFA?: boolean;
  onConfirmed?: () => void;
}

export default function DualApprovalModal({
  open,
  onClose,
  title,
  description,
  impact,
  approverLabel,
  beforeLabel,
  beforeValue,
  afterLabel,
  afterValue,
  auditType,
  actionLabel,
  entityLabel,
  reasonCode,
  requireMFA = true,
  onConfirmed,
}: Props) {
  const [mfaCode, setMfaCode] = useState("");
  const [step, setStep] = useState<"review" | "mfa" | "done">("review");

  const submit = () => {
    appendAuditEntry({
      actionType: auditType,
      actionLabel,
      entity: entityLabel,
      reasonCode: reasonCode ?? "Admin action",
      requestedBy: "Rohit Jain (Platform Admin)",
      approvedBy: "Meera Khanna (Ops Head)",
      status: "completed",
      beforeValue,
      afterValue,
      details: impact,
    });
    setStep("done");
    onConfirmed?.();
    setTimeout(() => {
      setMfaCode("");
      setStep("review");
      onClose();
    }, 1800);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && step !== "done" && onClose()}>
      <DialogContent className="sm:max-w-[540px] bg-gray-950 text-white border border-white/10">
        <DialogHeader>
          <DialogTitle className="text-lg text-white flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-brand-300" />
            {title}
          </DialogTitle>
          <DialogDescription className="text-gray-400 text-xs">{description}</DialogDescription>
        </DialogHeader>

        {step === "review" && (
          <div className="space-y-4 pt-2">
            <div className="rounded-lg bg-brand-500/10 border border-brand-500/30 px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wider text-brand-200 mb-1">Impact</p>
              <p className="text-sm text-white">{impact}</p>
            </div>

            {beforeValue && afterValue && (
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-black/30 border border-white/10 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{beforeLabel ?? "Before"}</p>
                  <p className="text-lg font-bold tabular-nums text-gray-300">{beforeValue}</p>
                </div>
                <div className="rounded-lg bg-accent-green/10 border border-accent-green/30 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-accent-green mb-1">{afterLabel ?? "After"}</p>
                  <p className="text-lg font-bold tabular-nums text-accent-green">{afterValue}</p>
                </div>
              </div>
            )}

            <div className="rounded-lg bg-accent-amber/10 border border-accent-amber/30 px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wider text-accent-amber mb-1">Governance</p>
              <p className="text-sm text-white">{approverLabel}</p>
            </div>

            <div className="flex items-center justify-end gap-2 pt-1">
              <button onClick={onClose} className="px-3 py-2 text-xs font-medium rounded-md text-gray-300 hover:bg-white/5">
                Cancel
              </button>
              <button
                onClick={() => setStep(requireMFA ? "mfa" : "done")}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600"
              >
                Proceed
                <ArrowRight className="h-3 w-3" />
              </button>
            </div>
          </div>
        )}

        {step === "mfa" && (
          <div className="space-y-4 pt-2">
            <div className="flex items-center gap-2 text-gray-300">
              <Key className="h-4 w-4 text-brand-300" />
              <p className="text-sm">Enter the 6-digit code from your authenticator</p>
            </div>
            <input
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
              placeholder="••••••"
              autoFocus
              inputMode="numeric"
              className="w-full bg-black/40 border border-white/10 text-white text-center text-2xl tracking-[0.5em] rounded-lg px-3 py-3 focus:outline-none focus:ring-2 focus:ring-brand-400"
            />
            <p className="text-[11px] text-gray-500 text-center">Demo: any 6 digits accepted</p>
            <div className="flex items-center justify-end gap-2">
              <button onClick={() => setStep("review")} className="px-3 py-2 text-xs font-medium rounded-md text-gray-300 hover:bg-white/5">
                Back
              </button>
              <button
                onClick={submit}
                disabled={mfaCode.length !== 6}
                className="px-3 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Verify & apply
              </button>
            </div>
          </div>
        )}

        {step === "done" && (
          <div className="py-6 flex flex-col items-center gap-3 text-center">
            <div className="h-10 w-10 rounded-full bg-accent-green/20 border border-accent-green/40 flex items-center justify-center">
              <ShieldCheck className="h-5 w-5 text-accent-green" />
            </div>
            <p className="text-sm font-semibold text-white">Applied · audit entry logged</p>
            <p className="text-[11px] text-gray-500">Change propagates within 2 minutes</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
