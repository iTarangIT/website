"use client";

import { useMemo, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Phone,
  MapPin,
  AlertTriangle,
  X,
  User,
  Send,
  FileWarning,
  Lock,
  Wrench,
  BrainCircuit,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import type { BatteryRow } from "@/data/portal/loans";
import { portalDrivers } from "@/data/portal/drivers";
import ScoreBadge from "@/components/portal/shared/ScoreBadge";
import ScoreExplainer from "@/components/portal/shared/ScoreExplainer";
import ConfidenceBadge from "@/components/portal/shared/ConfidenceBadge";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import ActionConfirmation from "@/components/portal/shared/ActionConfirmation";
import TelemetryTab from "./TelemetryTab";
import EMIHistoryTab from "./EMIHistoryTab";
import UsagePatternTab from "./UsagePatternTab";
import ActionHistoryTab from "./ActionHistoryTab";

type TabId = "telemetry" | "emi" | "usage" | "history";
type ActionId = "reminder" | "field-visit" | "immobilize" | "restructure";

interface Props {
  row: BatteryRow | null;
  onClose: () => void;
}

const RISK_BANNER: Record<BatteryRow["riskLevel"], { label: string; cls: string }> = {
  low: { label: "LOW RISK — Monitor only", cls: "bg-accent-green/15 text-accent-green border-accent-green/30" },
  medium: { label: "MEDIUM RISK — Reminder cadence applied", cls: "bg-brand-500/15 text-brand-200 border-brand-500/30" },
  high: { label: "HIGH RISK — Recovery escalation eligible", cls: "bg-accent-amber/15 text-accent-amber border-accent-amber/30" },
  "very-high": { label: "VERY HIGH RISK — Immobilization Eligible", cls: "bg-red-500/15 text-red-300 border-red-500/30" },
};

export default function CaseWorkspace({ row, onClose }: Props) {
  const [tab, setTab] = useState<TabId>("telemetry");
  const [explainer, setExplainer] = useState<"cds" | "pci" | null>(null);
  const [selectedAction, setSelectedAction] = useState<ActionId | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const driver = useMemo(() => portalDrivers.find((d) => d.id === row?.driverId), [row]);

  if (!row) return null;

  const banner = RISK_BANNER[row.riskLevel];

  return (
    <>
      <Dialog open={!!row} onOpenChange={(o) => !o && onClose()}>
        <DialogContent className="max-w-[1100px] w-[96vw] h-[90vh] bg-gray-950 border border-white/10 p-0 overflow-hidden flex flex-col">
          <DialogTitle className="sr-only">Case workspace for {row.customer}</DialogTitle>
          {/* Header */}
          <header className="flex items-start justify-between gap-3 px-6 py-4 border-b border-white/10 bg-black/30">
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                <span>Case</span>
                <span className="font-mono text-white">{row.batteryId}</span>
                <span>·</span>
                <span className="text-white">{row.customer}</span>
                <span>·</span>
                <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{row.city}</span>
              </div>
              <span
                className={cn(
                  "inline-flex items-center gap-2 px-2.5 py-1 rounded-full border text-[11px] font-bold uppercase tracking-wider",
                  banner.cls,
                )}
              >
                {banner.label}
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5"
              aria-label="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </header>

          {/* Body */}
          <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
            {/* Account summary */}
            <section className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <Field label="Customer" value={row.customer} icon={User} />
              <Field label="Dealer" value={row.dealer} />
              <Field label="Loan ID" value={row.loanId} />
              <Field label="Outstanding" value={formatCurrency(row.outstanding)} emphasis />
              <Field label="Loan start" value={driver?.onboardingDate ?? "—"} />
              <Field label="Tenure" value={`${driver?.loan.tenureMonths ?? 18} months`} />
              <Field label="Phone" value={row.customer === "Mohan Sharma" ? "+91 94110 22337" : driver?.phone ?? "—"} icon={Phone} />
              <Field label="IMEI" value={row.imei} mono />
            </section>

            {/* Why flagged */}
            <section className="rounded-xl border-2 border-accent-amber/30 bg-accent-amber/5 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2 text-accent-amber">
                  <AlertTriangle className="h-4 w-4" />
                  <p className="text-xs font-bold uppercase tracking-wider">Why this account is flagged</p>
                </div>
                <div className="flex items-center gap-2">
                  <ConfidenceBadge level={row.isInsufficientHistory ? "low" : row.riskLevel === "very-high" ? "high" : "medium"} />
                  <DataFreshnessBadge />
                </div>
              </div>
              <WhyBullets row={row} />
              <div className="flex items-center gap-3">
                <ScoreBadge type="cds" value={row.cds} size="md" onClick={() => setExplainer("cds")} />
                <ScoreBadge type="pci" value={row.pci} size="md" onClick={() => setExplainer("pci")} />
                <span className="text-[11px] text-gray-500">(click any score to see formula, inputs & limits)</span>
              </div>
            </section>

            {/* Evidence tabs */}
            <section>
              <div className="flex items-center gap-1 text-xs border-b border-white/10 mb-3">
                {([
                  { id: "telemetry", label: "Telemetry" },
                  { id: "emi", label: "EMI History" },
                  { id: "usage", label: "Usage Pattern" },
                  { id: "history", label: "Action History" },
                ] as { id: TabId; label: string }[]).map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setTab(t.id)}
                    className={cn(
                      "px-3 py-2 font-semibold transition-colors border-b-2",
                      tab === t.id ? "border-brand-400 text-white" : "border-transparent text-gray-500 hover:text-gray-200",
                    )}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {tab === "telemetry" && <TelemetryTab row={row} driver={driver} />}
              {tab === "emi" && <EMIHistoryTab row={row} />}
              {tab === "usage" && <UsagePatternTab row={row} driver={driver} />}
              {tab === "history" && <ActionHistoryTab row={row} />}
            </section>

            {/* Why this matters */}
            <section className="rounded-xl bg-brand-500/5 border border-brand-500/20 p-4">
              <div className="flex items-center gap-2 text-brand-200 mb-2">
                <BrainCircuit className="h-4 w-4" />
                <p className="text-xs font-bold uppercase tracking-wider">Why this matters</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-xs">
                <InfoTile label="Default probability" value={defaultProbability(row)} accent />
                <InfoTile label="Evidence confidence" value={row.isInsufficientHistory ? "Low" : "Medium"} />
                <InfoTile label="Data freshness" value="Today, 6:00 AM IST" />
                <InfoTile label="Knowledge limits" value="Cannot detect force majeure · human review required" />
              </div>
            </section>

            {/* Recommended actions */}
            <section>
              <h4 className="text-xs uppercase tracking-wider font-bold text-gray-500 mb-3 pb-1 border-b border-white/10">
                Recommended actions
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <ActionRadio
                  id="reminder"
                  icon={Send}
                  label="Send payment reminder"
                  sub="Auto-notification · no approval required"
                  selected={selectedAction === "reminder"}
                  onSelect={() => setSelectedAction("reminder")}
                />
                <ActionRadio
                  id="field-visit"
                  icon={Wrench}
                  label="Request field visit"
                  sub="Assign agent · single approval"
                  selected={selectedAction === "field-visit"}
                  onSelect={() => setSelectedAction("field-visit")}
                />
                <ActionRadio
                  id="immobilize"
                  icon={Lock}
                  label="Request immobilization"
                  sub="Dual approval required · Risk Head + Ops"
                  selected={selectedAction === "immobilize"}
                  onSelect={() => setSelectedAction("immobilize")}
                  variant="danger"
                />
                <ActionRadio
                  id="restructure"
                  icon={FileWarning}
                  label="Review for loan restructuring"
                  sub="Dual approval required · compliance review"
                  selected={selectedAction === "restructure"}
                  onSelect={() => setSelectedAction("restructure")}
                />
              </div>
              <div className="mt-4 flex justify-end">
                <button
                  onClick={() => setConfirmOpen(true)}
                  disabled={!selectedAction}
                  className="px-4 py-2 text-xs font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Continue to action →
                </button>
              </div>
            </section>
          </div>
        </DialogContent>
      </Dialog>

      <ScoreExplainer
        open={explainer === "cds"}
        onClose={() => setExplainer(null)}
        type="cds"
        value={row.cds}
        entityLabel={`${row.batteryId} · ${row.customer}`}
        confidence={row.isInsufficientHistory ? "low" : "medium"}
        emiHistory={[
          { when: "EMI 6 (current)", status: row.overdueDays > 0 ? "Skipped" : "On time", weight: row.overdueDays > 0 ? 7 : 0, recency: 1.5, penalty: row.overdueDays > 30 ? 2 : 0, contribution: (row.overdueDays > 0 ? 7 : 0) * 1.5 + (row.overdueDays > 30 ? 2 : 0) },
          { when: "EMI 5", status: row.overdueDays > 15 ? "Skipped" : "Late", weight: row.overdueDays > 15 ? 7 : 3, recency: 1.5, penalty: row.overdueDays > 15 ? 2 : 0, contribution: (row.overdueDays > 15 ? 7 : 3) * 1.5 + (row.overdueDays > 15 ? 2 : 0) },
          { when: "EMI 4", status: "Late 8-30d", weight: 3, recency: 1.2, penalty: 0, contribution: 3.6 },
          { when: "EMI 3", status: "On time", weight: 0, recency: 1.2, penalty: 0, contribution: 0 },
          { when: "EMI 2", status: "Late 1-7d", weight: 1, recency: 1.0, penalty: 0, contribution: 1 },
          { when: "EMI 1", status: "On time", weight: 0, recency: 1.0, penalty: 0, contribution: 0 },
        ]}
      />

      <ScoreExplainer
        open={explainer === "pci"}
        onClose={() => setExplainer(null)}
        type="pci"
        value={row.pci}
        entityLabel={`${row.batteryId} · ${row.customer}`}
        confidence={row.isInsufficientHistory ? "low" : "medium"}
      />

      {selectedAction && (
        <ActionConfirmation
          open={confirmOpen}
          onClose={() => setConfirmOpen(false)}
          action={actionConfigFor(selectedAction, row).action}
          reasonCodes={actionConfigFor(selectedAction, row).reasonCodes}
          steps={actionConfigFor(selectedAction, row).steps}
          approvers={actionConfigFor(selectedAction, row).approvers}
          borrowerNotice={actionConfigFor(selectedAction, row).borrowerNotice}
        />
      )}
    </>
  );
}

function defaultProbability(row: BatteryRow): string {
  // Simple heuristic off CDS
  const pct = Math.min(95, Math.round(row.cds * 0.95));
  return `${pct}% (based on CDS ${row.cds})`;
}

function WhyBullets({ row }: { row: BatteryRow }) {
  const bullets: string[] = [];
  if (row.dailyKm30d < 30) bullets.push(`Daily usage dropped — current 30d avg ${row.dailyKm30d} km/day (threshold < 30 km)`);
  if (row.overdueDays > 0) bullets.push(`EMI overdue ${row.overdueDays} days`);
  if (row.sohTrend === "down") bullets.push(`SOH trending down at ${row.sohPct}%`);
  if (row.isForceMajeure) bullets.push("Force majeure declared (medical emergency) — documented in audit");
  if (row.isRecentlyRestructured) bullets.push("Loan was restructured < 90 days ago — CDS confidence low");
  if (row.isInsufficientHistory) bullets.push("Fewer than 3 EMIs observed — scores not yet reliable");
  if (bullets.length === 0) bullets.push("No anomalies detected. Continue standard monitoring.");
  return (
    <ul className="space-y-1.5 text-sm text-gray-200">
      {bullets.map((b, i) => (
        <li key={i} className="flex gap-2 leading-relaxed">
          <span className="mt-1.5 h-1 w-1 rounded-full bg-accent-amber shrink-0" />
          <span>{b}</span>
        </li>
      ))}
    </ul>
  );
}

function Field({
  label,
  value,
  icon: Icon,
  mono,
  emphasis,
}: {
  label: string;
  value: string;
  icon?: typeof User;
  mono?: boolean;
  emphasis?: boolean;
}) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 flex items-center gap-1">
        {Icon && <Icon className="h-2.5 w-2.5" />}
        {label}
      </p>
      <p className={cn("text-sm text-white", emphasis && "font-bold", mono && "font-mono text-[12px]")}>{value}</p>
    </div>
  );
}

function InfoTile({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{label}</p>
      <p className={cn("text-sm", accent ? "text-brand-200 font-bold" : "text-gray-200")}>{value}</p>
    </div>
  );
}

function ActionRadio({
  id,
  icon: Icon,
  label,
  sub,
  selected,
  onSelect,
  variant = "default",
}: {
  id: ActionId;
  icon: typeof Send;
  label: string;
  sub: string;
  selected: boolean;
  onSelect: () => void;
  variant?: "default" | "danger";
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "flex items-start gap-3 text-left rounded-lg border px-3 py-2.5 transition-colors",
        selected
          ? variant === "danger"
            ? "bg-red-500/10 border-red-500/40"
            : "bg-brand-500/15 border-brand-500/40"
          : "bg-white/5 border-white/10 hover:bg-white/10",
      )}
    >
      <span
        className={cn(
          "mt-0.5 shrink-0 h-4 w-4 rounded-full border-2 flex items-center justify-center",
          selected ? (variant === "danger" ? "border-red-400" : "border-brand-400") : "border-gray-600",
        )}
      >
        {selected && <span className={cn("h-2 w-2 rounded-full", variant === "danger" ? "bg-red-400" : "bg-brand-400")} />}
      </span>
      <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", variant === "danger" ? "text-red-300" : "text-brand-300")} />
      <div>
        <p className="text-sm font-semibold text-white">{label}</p>
        <p className="text-[11px] text-gray-400 mt-0.5">{sub}</p>
      </div>
      <span className="sr-only">{id}</span>
    </button>
  );
}

function actionConfigFor(a: ActionId, row: BatteryRow) {
  if (a === "reminder") {
    return {
      action: {
        title: "You are about to send a payment reminder",
        label: "Send Payment Reminder",
        auditType: "payment-reminder" as const,
        entityLabel: `${row.batteryId} · ${row.customer}`,
        entityId: row.batteryId,
      },
      reasonCodes: ["EMI due today", "EMI overdue 1–7 days", "EMI overdue 8+ days", "Other (specify)"],
      steps: [
        "SMS + app notification dispatched to borrower using the preview below",
        "Audit entry logged with timestamp, requester, reason",
        "Follow-up cadence scheduled: +3d if unpaid, +7d final warning",
      ],
      approvers: [],
      borrowerNotice: undefined,
    };
  }
  if (a === "field-visit") {
    return {
      action: {
        title: "You are about to request a field visit",
        label: "Request Field Visit",
        auditType: "field-visit" as const,
        entityLabel: `${row.batteryId} · ${row.customer}`,
        entityId: row.batteryId,
      },
      reasonCodes: ["Usage drop + idle days", "Battery offline > 48h", "Geo-shift alert", "Borrower unresponsive", "Other (specify)"],
      steps: [
        "Recovery agent assigned based on proximity and workload",
        "Agent receives pre-call briefing (telemetry + EMI history, no PII beyond contact)",
        "Outcome recorded in case file; updates borrower-visible timeline",
      ],
      approvers: [{ role: "Risk Head", name: "Amit Raghavan", etaHours: "~1 hr" }],
      borrowerNotice: undefined,
    };
  }
  if (a === "immobilize") {
    return {
      action: {
        title: "You are about to request battery immobilization",
        label: "Request Immobilization",
        auditType: "immobilization-requested" as const,
        entityLabel: `${row.batteryId} · ${row.customer}`,
        entityId: row.batteryId,
      },
      reasonCodes: [
        "EMI overdue + high CDS + usage anomaly",
        "Suspected theft (FIR on file)",
        "Borrower absconding (geo-shift + offline)",
        "Other (specify)",
      ],
      steps: [
        "Request routed to Risk Head + Ops Lead for dual approval (governance check)",
        "On approval, immobilization command sent only when battery is stationary & ignition off",
        "Borrower notified via SMS + App with lender identity, LSP identity, grievance URL and reversal path",
        "Audit log entry records requester, both approvers, reason code and reversibility window",
      ],
      approvers: [
        { role: "Risk Head", name: "Amit Raghavan", etaHours: "~2 hrs" },
        { role: "Ops Lead", name: "Meera Khanna", etaHours: "~2–4 hrs" },
      ],
      borrowerNotice: {
        borrowerName: row.customer,
        loanId: row.loanId,
        outstanding: row.outstanding,
        actionLabel: "battery immobilization",
        reversibility: "Yes — re-mobilization within 2–4 hours after EMI settlement + dual approval",
      },
    };
  }
  return {
    action: {
      title: "You are about to initiate a loan restructuring review",
      label: "Loan Restructuring Review",
      auditType: "restructuring-review" as const,
      entityLabel: `${row.batteryId} · ${row.customer}`,
      entityId: row.batteryId,
    },
    reasonCodes: ["Force majeure (documented)", "Income disruption", "Borrower request", "Other (specify)"],
    steps: [
      "Request routed to Risk Head for first-pass review",
      "Ops Lead confirms eligibility + compliance approvals",
      "On approval, tenure / EMI schedule updated; borrower notified with new repayment schedule",
    ],
    approvers: [
      { role: "Risk Head", name: "Amit Raghavan", etaHours: "~4 hrs" },
      { role: "Ops Lead", name: "Meera Khanna", etaHours: "~24 hrs" },
    ],
    borrowerNotice: {
      borrowerName: row.customer,
      loanId: row.loanId,
      outstanding: row.outstanding,
      actionLabel: "loan restructuring review",
      reversibility: "Restructuring does not take effect until the borrower signs the updated schedule",
    },
  };
}
