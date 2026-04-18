export type InsightSeverity = "critical" | "warning" | "info" | "positive";

export interface Insight {
  id: string;
  severity: InsightSeverity;
  headline: string;
  body: string;
  accountsAffected: number;
  primaryAction: { label: string; href?: string };
  secondaryAction?: { label: string; href?: string };
}

export const riskInsights: Insight[] = [
  {
    id: "ins-1",
    severity: "critical",
    headline: "Drivers running <40 km/day show 3.2× higher default risk",
    body: "234 accounts flagged. Majority are in Patna and Varanasi clusters. Early signal: usage drop precedes EMI default by a median of 11 days.",
    accountsAffected: 234,
    primaryAction: { label: "View accounts", href: "/nbfc/batteries?filter=low-usage" },
    secondaryAction: { label: "Deploy field team" },
  },
  {
    id: "ins-2",
    severity: "warning",
    headline: "Irregular charging patterns detected in 156 batteries",
    body: "Delinquency probability +45% when charging cadence drops below 4 events per 7 days. Suggest proactive reminders within 48 hours.",
    accountsAffected: 156,
    primaryAction: { label: "Send reminders" },
    secondaryAction: { label: "View accounts", href: "/nbfc/batteries?filter=irregular-charging" },
  },
  {
    id: "ins-3",
    severity: "critical",
    headline: "89 batteries idle for 2+ days — potential absconding",
    body: "Geo-shift flag triggered on 34 of these. Recommend ground verification before escalation to recovery.",
    accountsAffected: 89,
    primaryAction: { label: "Trigger review" },
    secondaryAction: { label: "View accounts", href: "/nbfc/batteries?filter=idle-2d" },
  },
  {
    id: "ins-4",
    severity: "positive",
    headline: "Patna region shows improvement",
    body: "Defaults down 6% in Patna after the July reminder campaign. Playbook can be replicated in Varanasi where default rate is still 13.6%.",
    accountsAffected: 480,
    primaryAction: { label: "View campaign report" },
  },
];

export const preDisbursementRecs = [
  {
    id: "pd-1",
    segment: "Applicants from high-risk clusters (CDS 41+)",
    recommendation: "+150 bps on interest rate + mandatory ground verification before disbursal",
    evidence: "Default rate in this cohort is 14.8% vs portfolio average 9.2%. A 150 bps premium covers expected loss + field cost.",
  },
  {
    id: "pd-2",
    segment: "First-time borrowers, <3 EMI references",
    recommendation: "Require co-signer OR 110% collateralization via IoT-locked battery + 5% principal deposit",
    evidence: "Insufficient EMI history accounts show 2.1× higher variance in PCI. Collateralization reduces LGD by ~35%.",
  },
  {
    id: "pd-3",
    segment: "Varanasi & Patna clusters",
    recommendation: "Route through ground-verification team before approval; waive only after 2 months of telemetry hygiene",
    evidence: "These regions contribute 38% of at-risk accounts despite holding 19% of portfolio.",
  },
];
