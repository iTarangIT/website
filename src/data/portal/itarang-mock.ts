export interface Alert {
  id: string;
  type: "temp-stress" | "cell-imbalance" | "offline" | "geo-shift" | "default-risk";
  title: string;
  subtitle: string;
  city: string;
  timeAgo: string;
  severity: "info" | "warning" | "critical";
}

export interface OEMAnomalyRow {
  oem: string;
  modelMix: string;
  deployed: number;
  anomalyRatePct: number;
}

export interface SLATicket {
  id: string;
  customer: string;
  issue: string;
  city: string;
  slaRemainingMinutes: number;
  severity: "High" | "Critical";
}

export const controlTowerKpi = {
  batteriesUnderManagement: 152,
  onlinePctLastHour: 94.7,
  fleetAvgSoh: 94.2,
  assetsUnder80Soh: 5,
  highRiskFinanced: 18,
  openCriticalTickets: 2,
};

export const controlTowerAlerts: Alert[] = [
  {
    id: "alrt-1",
    type: "temp-stress",
    title: "Temperature spike — BAT-DL-0170",
    subtitle: "142 min > 45°C in 7d · driver Raju Kumar",
    city: "Delhi NCR",
    timeAgo: "12 min ago",
    severity: "critical",
  },
  {
    id: "alrt-2",
    type: "geo-shift",
    title: "Geo-shift flagged — BAT-VNS-0028",
    subtitle: "Asset moved 168 km from onboarding pin",
    city: "Varanasi",
    timeAgo: "34 min ago",
    severity: "critical",
  },
  {
    id: "alrt-3",
    type: "offline",
    title: "Offline > 48h — BAT-VNS-0028",
    subtitle: "Last packet 7 days ago · possible tamper",
    city: "Varanasi",
    timeAgo: "1 hr ago",
    severity: "warning",
  },
  {
    id: "alrt-4",
    type: "cell-imbalance",
    title: "Cell imbalance cluster — BAT-LKO-0103",
    subtitle: "4 events in 7d · Δv > 0.08V",
    city: "Lucknow",
    timeAgo: "2 hr ago",
    severity: "warning",
  },
  {
    id: "alrt-5",
    type: "default-risk",
    title: "Risk score crossed 80 — BAT-DL-0170",
    subtitle: "Escalate to NBFC collections queue",
    city: "Delhi NCR",
    timeAgo: "3 hr ago",
    severity: "warning",
  },
];

export const oemAnomalyRates: OEMAnomalyRow[] = [
  { oem: "iEnerzy", modelMix: "48V / 60V pack", deployed: 96, anomalyRatePct: 2.1 },
  { oem: "Trontek", modelMix: "51V / 61V pack", deployed: 38, anomalyRatePct: 3.8 },
  { oem: "GoEl", modelMix: "72V pack", deployed: 18, anomalyRatePct: 5.6 },
];

export const slaBreachQueue: SLATicket[] = [
  { id: "TKT-2026-0417", customer: "Raju Kumar", issue: "Battery not charging", city: "Delhi NCR", slaRemainingMinutes: 90, severity: "Critical" },
  { id: "TKT-2026-0412", customer: "Mukesh Pandey", issue: "No power after rain", city: "Varanasi", slaRemainingMinutes: 180, severity: "High" },
  { id: "TKT-2026-0408", customer: "Feroz Alam", issue: "Charger port damage", city: "Lucknow", slaRemainingMinutes: 240, severity: "High" },
];
