export type AlertSeverity = "critical" | "warning" | "info";
export type AlertChannel = "email" | "sms" | "dashboard";

export interface AlertRule {
  id: string;
  label: string;
  description: string;
  severity: AlertSeverity;
  enabled: boolean;
  channels: Record<AlertChannel, boolean>;
  affectsAccounts: number;
}

export const defaultAlertRules: AlertRule[] = [
  {
    id: "usage-drop",
    label: "Usage drop > 40% (7d)",
    description: "Daily km dropped more than the configured threshold vs prior 7 days.",
    severity: "warning",
    enabled: true,
    channels: { email: false, sms: false, dashboard: true },
    affectsAccounts: 234,
  },
  {
    id: "offline-48h",
    label: "Battery offline > 48h",
    description: "No telemetry heartbeat received for 48 hours — possible tamper or connectivity failure.",
    severity: "critical",
    enabled: true,
    channels: { email: true, sms: false, dashboard: true },
    affectsAccounts: 18,
  },
  {
    id: "geo-shift-100",
    label: "Geo-shift > 100 km",
    description: "Asset moved beyond configured distance from onboarding location.",
    severity: "critical",
    enabled: true,
    channels: { email: true, sms: true, dashboard: true },
    affectsAccounts: 8,
  },
  {
    id: "cell-imbalance",
    label: "Cell imbalance (Δv > 0.08V)",
    description: "Cell voltage delta crossed BMS warning band.",
    severity: "warning",
    enabled: true,
    channels: { email: false, sms: false, dashboard: true },
    affectsAccounts: 52,
  },
  {
    id: "temp-stress",
    label: "Temperature stress > 45°C (cumulative 120 min/7d)",
    description: "Battery operated above safe temperature for extended duration.",
    severity: "warning",
    enabled: true,
    channels: { email: false, sms: false, dashboard: true },
    affectsAccounts: 102,
  },
  {
    id: "emi-1-7",
    label: "EMI overdue 1–7 days",
    description: "Soft-bucket reminder cadence.",
    severity: "info",
    enabled: true,
    channels: { email: false, sms: true, dashboard: true },
    affectsAccounts: 18,
  },
  {
    id: "emi-8-30",
    label: "EMI overdue 8–30 days",
    description: "Medium-bucket — escalate to collections team.",
    severity: "warning",
    enabled: true,
    channels: { email: true, sms: true, dashboard: true },
    affectsAccounts: 11,
  },
  {
    id: "emi-30+",
    label: "EMI overdue 30+ days",
    description: "Hard-bucket — immobilization eligible once CDS crosses 70.",
    severity: "critical",
    enabled: true,
    channels: { email: true, sms: true, dashboard: true },
    affectsAccounts: 5,
  },
  {
    id: "cds-80",
    label: "CDS crossed 80",
    description: "Chronic Default Score entered very-high band — recovery action queue.",
    severity: "critical",
    enabled: true,
    channels: { email: true, sms: false, dashboard: true },
    affectsAccounts: 12,
  },
  {
    id: "pci-below-05",
    label: "PCI below 0.5",
    description: "Payment Consistency Index below reliable-payer floor.",
    severity: "warning",
    enabled: false,
    channels: { email: false, sms: false, dashboard: true },
    affectsAccounts: 9,
  },
];
