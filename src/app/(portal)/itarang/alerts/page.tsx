"use client";

import { useState } from "react";
import { Bell, Mail, Smartphone, Monitor } from "lucide-react";
import { cn } from "@/lib/utils";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";
import DualApprovalModal from "@/components/portal/shared/DualApprovalModal";
import { defaultAlertRules, type AlertRule, type AlertChannel, type AlertSeverity } from "@/data/portal/alert-rules";

const SEVERITY_STYLES: Record<AlertSeverity, string> = {
  critical: "bg-red-500/15 text-red-300 border-red-500/30",
  warning: "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  info: "bg-brand-500/15 text-brand-200 border-brand-500/30",
};

const CHANNEL_META: Record<AlertChannel, { label: string; icon: typeof Mail }> = {
  email: { label: "Email", icon: Mail },
  sms: { label: "SMS", icon: Smartphone },
  dashboard: { label: "Dashboard", icon: Monitor },
};

export default function AlertsConfigPage() {
  const [rules, setRules] = useState<AlertRule[]>(defaultAlertRules);
  const [pending, setPending] = useState<{ rule: AlertRule; change: string; before: string; after: string } | null>(null);

  const applyChange = () => {
    if (!pending) return;
    const { rule, change } = pending;
    setRules((prev) =>
      prev.map((r) => {
        if (r.id !== rule.id) return r;
        if (change === "enabled") return { ...r, enabled: !r.enabled };
        if (change.startsWith("channel:")) {
          const ch = change.replace("channel:", "") as AlertChannel;
          return { ...r, channels: { ...r.channels, [ch]: !r.channels[ch] } };
        }
        if (change.startsWith("severity:")) {
          return { ...r, severity: change.replace("severity:", "") as AlertSeverity };
        }
        return r;
      }),
    );
    setPending(null);
  };

  const queueChange = (rule: AlertRule, change: string, before: string, after: string) => {
    setPending({ rule, change, before, after });
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Alert Configuration</h1>
          <p className="text-sm text-gray-400 mt-1">
            {rules.length} rules · toggle, change severity or channels · every change routes through dual approval + audit
          </p>
        </div>
        <DataFreshnessBadge />
      </header>

      <section className="rounded-xl bg-white/5 border border-white/10 divide-y divide-white/10">
        {rules.map((r) => (
          <article key={r.id} className="px-5 py-4 grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-4 items-center">
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-sm font-semibold text-white">{r.label}</p>
                <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", SEVERITY_STYLES[r.severity])}>
                  {r.severity}
                </span>
                <span className="text-[10px] text-gray-500">{r.affectsAccounts.toLocaleString("en-IN")} accounts</span>
              </div>
              <p className="text-[11px] text-gray-400 mt-0.5">{r.description}</p>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-[10px] uppercase tracking-wider text-gray-500">Severity</label>
              <select
                value={r.severity}
                onChange={(e) =>
                  queueChange(
                    r,
                    `severity:${e.target.value}`,
                    r.severity,
                    e.target.value,
                  )
                }
                className="bg-white/5 border border-white/10 text-white text-[11px] rounded-md px-2 py-1 focus:outline-none"
              >
                <option value="critical" className="bg-gray-950">Critical</option>
                <option value="warning" className="bg-gray-950">Warning</option>
                <option value="info" className="bg-gray-950">Info</option>
              </select>

              <div className="flex items-center gap-1">
                {(Object.keys(CHANNEL_META) as AlertChannel[]).map((ch) => {
                  const Icon = CHANNEL_META[ch].icon;
                  const on = r.channels[ch];
                  return (
                    <button
                      key={ch}
                      onClick={() =>
                        queueChange(r, `channel:${ch}`, on ? "on" : "off", on ? "off" : "on")
                      }
                      aria-label={`Toggle ${CHANNEL_META[ch].label} channel`}
                      aria-pressed={on}
                      className={cn(
                        "h-7 w-7 rounded-md border flex items-center justify-center transition-colors",
                        on
                          ? "bg-brand-500/20 border-brand-500/40 text-brand-200"
                          : "bg-white/5 border-white/10 text-gray-500 hover:text-gray-300",
                      )}
                      title={`${CHANNEL_META[ch].label} · ${on ? "on" : "off"}`}
                    >
                      <Icon className="h-3 w-3" />
                    </button>
                  );
                })}
              </div>
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <span className="text-[10px] uppercase tracking-wider text-gray-500">{r.enabled ? "On" : "Off"}</span>
              <span
                onClick={() => queueChange(r, "enabled", r.enabled ? "on" : "off", r.enabled ? "off" : "on")}
                role="switch"
                aria-checked={r.enabled}
                tabIndex={0}
                className={cn(
                  "relative inline-block w-9 h-5 rounded-full transition-colors",
                  r.enabled ? "bg-accent-green" : "bg-white/10",
                )}
              >
                <span
                  className={cn(
                    "absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform",
                    r.enabled ? "translate-x-4" : "translate-x-0.5",
                  )}
                />
              </span>
            </label>
          </article>
        ))}
      </section>

      {pending && (
        <DualApprovalModal
          open={!!pending}
          onClose={() => setPending(null)}
          onConfirmed={applyChange}
          title={`Update alert rule · ${pending.rule.label}`}
          description="Rule changes propagate to the alert engine on next evaluation cycle."
          impact={`Affects ${pending.rule.affectsAccounts.toLocaleString("en-IN")} accounts.`}
          approverLabel="Ops Head approval required (MFA sim)"
          beforeLabel="Before"
          beforeValue={pending.before}
          afterLabel="After"
          afterValue={pending.after}
          auditType="threshold-change"
          actionLabel={`Alert rule: ${pending.rule.label}`}
          entityLabel={pending.rule.id}
          reasonCode="Alert configuration"
        />
      )}

      <p className="text-[10px] text-gray-500 flex items-center gap-2 leading-relaxed">
        <Bell className="h-3 w-3" />
        Every change is routed through dual approval and logged to the shared audit trail.
      </p>

      <RegulatoryFooter />
    </div>
  );
}
