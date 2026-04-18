"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ShieldCheck, UserCheck2, Clock, ScrollText, ArrowLeft } from "lucide-react";
import BorrowerNoticePreview from "./BorrowerNoticePreview";
import { appendAuditEntry } from "@/lib/audit-store";

interface Approver {
  role: string;
  name: string;
  etaHours: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  action: {
    title: string;                // "You are about to request battery immobilization"
    label: string;                // "Request Immobilization"
    auditType: Parameters<typeof appendAuditEntry>[0]["actionType"];
    entityLabel: string;          // "BT-3567 · Mohan Sharma"
    entityId: string;             // IMEI or battery id
  };
  reasonCodes: string[];
  steps: string[];                // what will happen in plain language
  approvers: Approver[];          // dual approval required
  borrowerNotice?: {
    borrowerName: string;
    loanId: string;
    outstanding: number;
    actionLabel: string;
    reversibility: string;
  };
}

export default function ActionConfirmation({
  open,
  onClose,
  action,
  reasonCodes,
  steps,
  approvers,
  borrowerNotice,
}: Props) {
  const [reasonCode, setReasonCode] = useState(reasonCodes[0] ?? "");
  const [customReason, setCustomReason] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const resolvedReason = reasonCode === "Other (specify)" ? customReason : reasonCode;
  const canSubmit = !!resolvedReason.trim();

  const submit = () => {
    appendAuditEntry({
      actionType: action.auditType,
      actionLabel: action.label,
      entity: action.entityId,
      reasonCode: resolvedReason,
      requestedBy: "Priya Sharma (Risk Analyst)",
      approvedBy: approvers.length > 0 ? null : "N/A",
      status: approvers.length > 0 ? "pending-approval" : "completed",
      details:
        approvers.length > 0
          ? `Dual approval required: ${approvers.map((a) => a.role).join(" + ")}`
          : "Action executed without approval (informational)",
    });
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
    }, 2400);
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-[640px] bg-gray-950 text-white border border-white/10 p-0 overflow-hidden">
        <div className="px-6 py-5 border-b border-white/10">
          <DialogHeader>
            <DialogTitle className="text-lg text-white">{action.title}</DialogTitle>
            <DialogDescription className="text-gray-400 text-xs">
              {action.entityLabel} · Evidence → Decision → Action → Audit
            </DialogDescription>
          </DialogHeader>
        </div>

        <div className="px-6 py-5 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* What will happen */}
          <section>
            <SectionTitle>What will happen</SectionTitle>
            <ol className="space-y-2 text-sm text-gray-200">
              {steps.map((s, i) => (
                <li key={i} className="flex gap-2">
                  <span className="shrink-0 h-5 w-5 rounded-full bg-brand-500/30 border border-brand-500/50 flex items-center justify-center text-[10px] font-bold">
                    {i + 1}
                  </span>
                  <span className="leading-relaxed">{s}</span>
                </li>
              ))}
            </ol>
          </section>

          {/* Approvers */}
          {approvers.length > 0 && (
            <section className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-4 space-y-2.5">
              <div className="flex items-center gap-2 text-brand-200">
                <ShieldCheck className="h-4 w-4" />
                <p className="text-xs font-bold uppercase tracking-wider">Approvals required</p>
              </div>
              {approvers.map((a) => (
                <div key={a.role} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <UserCheck2 className="h-3.5 w-3.5 text-brand-300" />
                    <span className="text-gray-300">{a.role}</span>
                    <span className="text-white font-medium">· {a.name}</span>
                  </div>
                  <span className="text-gray-500 flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {a.etaHours}
                  </span>
                </div>
              ))}
            </section>
          )}

          {/* Reason code */}
          <section>
            <SectionTitle>
              Reason code
              <span className="ml-2 text-[10px] text-red-300 font-bold">(required)</span>
            </SectionTitle>
            <select
              value={reasonCode}
              onChange={(e) => setReasonCode(e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
            >
              {reasonCodes.map((r) => (
                <option key={r} value={r} className="bg-gray-950">
                  {r}
                </option>
              ))}
            </select>
            {reasonCode === "Other (specify)" && (
              <textarea
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                placeholder="Describe the reason in detail (will be logged verbatim to audit)"
                rows={2}
                className="mt-2 w-full bg-white/5 border border-white/10 text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-brand-400"
              />
            )}
          </section>

          {/* Borrower notice */}
          {borrowerNotice && <BorrowerNoticePreview {...borrowerNotice} />}

          {/* Audit trail preview */}
          <section className="rounded-lg border border-white/10 bg-black/20 p-4">
            <div className="flex items-center gap-2 text-gray-400">
              <ScrollText className="h-3.5 w-3.5" />
              <p className="text-[11px] font-bold uppercase tracking-wider">Audit trail preview</p>
            </div>
            <p className="text-[11px] text-gray-400 leading-relaxed mt-2">
              Will log: <span className="text-white">timestamp · {action.entityId} · {action.label} · {resolvedReason || "<pending>"} · requested by Priya Sharma · approver chain · borrower-notice record</span>
            </p>
          </section>

          <p className="text-[10px] text-gray-500 border-t border-white/10 pt-3">
            This action complies with RBI Digital Lending Directions 2025 and the Fair Practices Code.
          </p>
        </div>

        <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-white/10 bg-black/30">
          <button
            onClick={onClose}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-md text-gray-400 hover:text-white hover:bg-white/5"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Review evidence
          </button>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-md text-gray-300 hover:text-white hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              onClick={submit}
              disabled={!canSubmit || submitted}
              className="px-4 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {submitted ? "Submitted — routed to approvers" : "Submit for approval"}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-[10px] uppercase tracking-wider font-bold text-gray-500 mb-2 pb-1 border-b border-white/10">
      {children}
    </h3>
  );
}
