"use client";

import { useState } from "react";
import { FileText, XCircle } from "lucide-react";
import { appendAuditEntry } from "@/lib/audit-store";

interface Props {
  consentDate?: string;
  loanId?: string;
  purpose?: string;
}

export default function PurposeStrip({
  consentDate = "2024-08-14",
  loanId = "LN-2024-08932",
  purpose = "loan risk assessment per your consent",
}: Props) {
  const [withdrawn, setWithdrawn] = useState(false);

  const withdraw = () => {
    appendAuditEntry({
      actionType: "consent-withdraw",
      actionLabel: "Telemetry consent withdrawn (preview)",
      entity: loanId,
      reasonCode: "Borrower request via grievance channel",
      requestedBy: "Priya Sharma (on behalf of borrower)",
      approvedBy: null,
      status: "completed",
      details: "Telemetry purposes paused for this loan. Risk monitoring falls back to EMI signal only.",
    });
    setWithdrawn(true);
    setTimeout(() => setWithdrawn(false), 2500);
  };

  return (
    <div
      className="rounded-lg bg-black/30 border border-white/10 px-3 py-2.5 flex items-start gap-2 text-[11px] text-gray-400 leading-relaxed"
      role="status"
      aria-live="polite"
    >
      <FileText className="h-3.5 w-3.5 text-brand-300 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <span className="text-gray-300">Why we use this data:</span>{" "}
        {purpose} dated <span className="font-mono text-gray-300">{consentDate}</span>.
      </div>
      {withdrawn ? (
        <span className="inline-flex items-center gap-1 text-[10px] text-accent-green">
          <XCircle className="h-3 w-3" />
          Consent withdraw logged
        </span>
      ) : (
        <button
          type="button"
          onClick={withdraw}
          className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-300 hover:text-brand-200"
        >
          Withdraw consent →
        </button>
      )}
    </div>
  );
}
