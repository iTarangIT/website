export type AlertSeverity = "critical" | "warning" | "info";

export interface PortfolioAlert {
  id: string;
  severity: AlertSeverity;
  category: "usage-drop" | "offline" | "geo-shift" | "emi-overdue" | "cell-imbalance" | "warranty" | "service";
  title: string;
  subtitle: string;
  entityId: string;       // driver or battery id
  entityLabel: string;    // e.g. "BT-3567 · Mohan Sharma"
  city: string;
  dealer?: string;
  timeAgo: string;
  actionHref?: string;
}

export const priorityQueue: PortfolioAlert[] = [
  { id: "a-c-1", severity: "critical", category: "usage-drop", title: "Usage drop 43% in 7 days", subtitle: "BT-3567 Mohan Sharma · 65 → 28 km/day", entityId: "drv-014", entityLabel: "BT-3567 · Mohan Sharma", city: "Prayagraj", dealer: "XYZ Battery Trading", timeAgo: "12 min ago", actionHref: "/nbfc/batteries?case=drv-014" },
  { id: "a-c-2", severity: "critical", category: "emi-overdue", title: "EMI overdue 42 days, CDS 82", subtitle: "BT-DL-0170 Raju Kumar · recovery escalation recommended", entityId: "drv-014", entityLabel: "BT-DL-0170 · Raju Kumar", city: "Delhi NCR", timeAgo: "27 min ago", actionHref: "/nbfc/batteries?case=drv-014" },
  { id: "a-c-3", severity: "critical", category: "offline", title: "Battery offline > 7 days", subtitle: "BT-VNS-0028 Guddu Yadav · possible tamper / absconding", entityId: "drv-015", entityLabel: "BT-VNS-0028 · Guddu Yadav", city: "Varanasi", timeAgo: "1 hr ago", actionHref: "/nbfc/batteries?case=drv-015" },
  { id: "a-c-4", severity: "critical", category: "geo-shift", title: "Geo-shift 168 km from onboarding", subtitle: "BT-VNS-0028 · outside serviceable radius", entityId: "drv-015", entityLabel: "BT-VNS-0028 · Guddu Yadav", city: "Varanasi", timeAgo: "1 hr ago", actionHref: "/nbfc/batteries?case=drv-015" },
  { id: "a-c-5", severity: "critical", category: "emi-overdue", title: "CDS crossed 80 — immobilization eligible", subtitle: "BT-PAT-0055 Pappu Sahni · DPD 31, idle 4 days", entityId: "drv-013", entityLabel: "BT-PAT-0055 · Pappu Sahni", city: "Patna", timeAgo: "2 hr ago", actionHref: "/nbfc/batteries?case=drv-013" },

  { id: "a-w-1", severity: "warning", category: "usage-drop", title: "Declining usage — 28% in 7 days", subtitle: "BT-KOL-0082 Santosh Mandal · 32 → 22 km", entityId: "drv-010", entityLabel: "BT-KOL-0082 · Santosh Mandal", city: "Kolkata", timeAgo: "3 hr ago" },
  { id: "a-w-2", severity: "warning", category: "cell-imbalance", title: "Cell imbalance cluster (4 events / 7d)", subtitle: "BT-LKO-0103 Feroz Alam · Δv > 0.08V", entityId: "drv-012", entityLabel: "BT-LKO-0103 · Feroz Alam", city: "Lucknow", timeAgo: "4 hr ago" },
  { id: "a-w-3", severity: "warning", category: "emi-overdue", title: "EMI overdue 14 days", subtitle: "BT-VNS-0021 Mukesh Pandey · PCI dropping to 0.62", entityId: "drv-011", entityLabel: "BT-VNS-0021 · Mukesh Pandey", city: "Varanasi", timeAgo: "5 hr ago" },
  { id: "a-w-4", severity: "warning", category: "offline", title: "Intermittent connectivity", subtitle: "BT-DL-0155 Imran Shaikh · 6.4 offline hrs/7d", entityId: "drv-009", entityLabel: "BT-DL-0155 · Imran Shaikh", city: "Delhi NCR", timeAgo: "6 hr ago" },

  { id: "a-i-1", severity: "info", category: "warranty", title: "Warranty expires in 30 days", subtitle: "BT-PAT-0068 Chintu Paswan · 17 months deployed", entityId: "drv-022", entityLabel: "BT-PAT-0068 · Chintu Paswan", city: "Patna", timeAgo: "Today" },
  { id: "a-i-2", severity: "info", category: "service", title: "Service reminder due", subtitle: "BT-LKO-0120 Anwar Khan · scheduled 2026-05-02", entityId: "drv-021", entityLabel: "BT-LKO-0120 · Anwar Khan", city: "Lucknow", timeAgo: "Today" },
];

export const alertCounts = {
  critical: 89,
  warning: 156,
  info: 97,
};
