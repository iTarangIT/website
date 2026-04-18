export interface InventoryItem {
  serial: string;
  status: "In Stock" | "Deployed" | "In Service" | "In Transit";
  health: number;
  consumer: string | null;
  model: string;
}

export interface EMIRow {
  consumer: string;
  battery: string;
  amount: number;
  dueDate: string;
  status: "Overdue" | "Due Today" | "Upcoming" | "Paid";
  dpd?: number;
}

export interface ServiceTicket {
  id: string;
  battery: string;
  consumer: string;
  issue: string;
  priority: "Low" | "Medium" | "High" | "Critical";
  slaRemainingHours: number;
  assignedTo: string | null;
}

export const dealerKpi = {
  activeBatteriesDeployed: 87,
  activeBatteriesDelta: 8,
  inventoryInStock: 14,
  inventoryReorderLevel: 10,
  emiCollectedMtdLakhs: 2.68,
  emiCollectionPct: 94.6,
  openServiceTickets: 6,
  criticalTickets: 1,
};

export const dealerInventory: InventoryItem[] = [
  { serial: "BAT-DL-0180", status: "Deployed", health: 98, consumer: "Bablu Sharma", model: "61V 132AH" },
  { serial: "BAT-DL-0195", status: "Deployed", health: 96, consumer: "Vikas Chauhan", model: "72V 232AH" },
  { serial: "BAT-DL-0205", status: "Deployed", health: 97, consumer: "Shiv Narayan", model: "51V 105AH" },
  { serial: "BAT-DL-0220", status: "In Stock", health: 100, consumer: null, model: "51V 105AH" },
  { serial: "BAT-DL-0221", status: "In Stock", health: 100, consumer: null, model: "61V 132AH" },
  { serial: "BAT-DL-0222", status: "In Service", health: 88, consumer: "Raju Kumar", model: "51V 132AH" },
];

export const dealerEMIs: EMIRow[] = [
  { consumer: "Raju Kumar", battery: "BAT-DL-0170", amount: 3240, dueDate: "2026-03-22", status: "Overdue", dpd: 27 },
  { consumer: "Imran Shaikh", battery: "BAT-DL-0155", amount: 3600, dueDate: "2026-04-12", status: "Overdue", dpd: 6 },
  { consumer: "Ramesh Yadav", battery: "BAT-DL-0142", amount: 3850, dueDate: "2026-04-28", status: "Due Today" },
  { consumer: "Sanjay Kumar", battery: "BAT-DL-0143", amount: 3420, dueDate: "2026-04-22", status: "Upcoming" },
  { consumer: "Vikas Chauhan", battery: "BAT-DL-0195", amount: 7140, dueDate: "2026-04-29", status: "Upcoming" },
];

export const dealerServiceTickets: ServiceTicket[] = [
  {
    id: "TKT-2026-0417",
    battery: "BAT-DL-0170",
    consumer: "Raju Kumar",
    issue: "Battery not charging fully",
    priority: "Critical",
    slaRemainingHours: 1.5,
    assignedTo: "Tech-04",
  },
  {
    id: "TKT-2026-0418",
    battery: "BAT-DL-0222",
    consumer: "Anil Singh",
    issue: "Reduced range reported",
    priority: "Medium",
    slaRemainingHours: 5.2,
    assignedTo: "Tech-02",
  },
  {
    id: "TKT-2026-0419",
    battery: "BAT-DL-0155",
    consumer: "Imran Shaikh",
    issue: "Charger connector warm",
    priority: "Low",
    slaRemainingHours: 12.0,
    assignedTo: null,
  },
];
