export type RiskBand = "low" | "medium" | "high";

export interface Driver {
  id: string;
  name: string;
  phone: string;
  photo?: string;
  city: string;
  dealerName: string;
  batterySerial: string;
  batteryModelId: string;
  batteryModelLabel: string;
  onboardingDate: string;
  monthsDeployed: number;
  cumulativeKm: number;
  avgDailyKm7d: number;
  avgDailyKm30d: number;
  sohPct: number;
  sohDelta30d: number;
  chargeCycles: number;
  tempStressMinutes7d: number;
  imbalanceEvents7d: number;
  offlineHours7d: number;
  loan: {
    principal: number;
    emi: number;
    tenureMonths: number;
    outstanding: number;
    nextDueDate: string;
    dpd: number;
  };
  risk: {
    usageDropPct: number;
    idleDays7d: number;
    geoShiftFlag: boolean;
    tamperEvents30d: number;
    cdsScore: number;
    pci: number;
    defaultRiskScore: number;
    riskBand: RiskBand;
  };
}

export const BATTERY_MODEL_OPTIONS: { id: string; label: string }[] = [
  { id: "all", label: "All batteries" },
  { id: "er-51v-105ah", label: "51V 105AH" },
  { id: "er-51v-132ah", label: "51V 132AH" },
  { id: "er-61v-105ah", label: "61V 105AH" },
  { id: "er-61v-132ah", label: "61V 132AH" },
  { id: "er-64v-105ah", label: "64V 105AH" },
  { id: "er-72v-232ah", label: "72V 232AH" },
];

function bandFromScore(score: number): RiskBand {
  if (score >= 70) return "high";
  if (score >= 40) return "medium";
  return "low";
}

type RiskInputs = { usageDropPct: number; idleDays7d: number; dpd: number; tamperEvents30d: number; tempStress: number; imbalance: number };
type RawDriver = Omit<Driver, "risk"> & { riskInputs: RiskInputs };

const rawDrivers: RawDriver[] = [
  {
    id: "drv-001", name: "Ramesh Yadav", phone: "+91 98110 23456", city: "Delhi NCR",
    dealerName: "Sharma E-Motors", batterySerial: "BAT-DL-0142", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2025-02-14", monthsDeployed: 14,
    cumulativeKm: 18420, avgDailyKm7d: 52, avgDailyKm30d: 48,
    sohPct: 96.2, sohDelta30d: -0.4, chargeCycles: 318, tempStressMinutes7d: 8, imbalanceEvents7d: 0, offlineHours7d: 2.1,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 15400, nextDueDate: "2026-04-28", dpd: 0 },
    riskInputs: { usageDropPct: 0.04, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 8, imbalance: 0 },
  },
  {
    id: "drv-002", name: "Sanjay Kumar", phone: "+91 93110 88002", city: "Delhi NCR",
    dealerName: "Sharma E-Motors", batterySerial: "BAT-DL-0143", batteryModelId: "er-61v-105ah", batteryModelLabel: "61V 105AH",
    onboardingDate: "2025-05-02", monthsDeployed: 11,
    cumulativeKm: 13210, avgDailyKm7d: 45, avgDailyKm30d: 44,
    sohPct: 97.1, sohDelta30d: -0.2, chargeCycles: 255, tempStressMinutes7d: 2, imbalanceEvents7d: 0, offlineHours7d: 0.4,
    loan: { principal: 55000, emi: 3420, tenureMonths: 18, outstanding: 20520, nextDueDate: "2026-04-22", dpd: 0 },
    riskInputs: { usageDropPct: 0.02, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 2, imbalance: 0 },
  },
  {
    id: "drv-003", name: "Prakash Gupta", phone: "+91 95510 44120", city: "Lucknow",
    dealerName: "Awadh E-Wheels", batterySerial: "BAT-LKO-0088", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2024-11-20", monthsDeployed: 17,
    cumulativeKm: 21580, avgDailyKm7d: 38, avgDailyKm30d: 42,
    sohPct: 93.8, sohDelta30d: -0.8, chargeCycles: 412, tempStressMinutes7d: 14, imbalanceEvents7d: 1, offlineHours7d: 3.2,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 6480, nextDueDate: "2026-04-25", dpd: 0 },
    riskInputs: { usageDropPct: 0.1, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 14, imbalance: 1 },
  },
  {
    id: "drv-004", name: "Mohit Verma", phone: "+91 97110 77201", city: "Lucknow",
    dealerName: "Awadh E-Wheels", batterySerial: "BAT-LKO-0091", batteryModelId: "er-51v-105ah", batteryModelLabel: "51V 105AH",
    onboardingDate: "2025-07-01", monthsDeployed: 9,
    cumulativeKm: 9820, avgDailyKm7d: 42, avgDailyKm30d: 40,
    sohPct: 97.8, sohDelta30d: 0, chargeCycles: 198, tempStressMinutes7d: 4, imbalanceEvents7d: 0, offlineHours7d: 0.8,
    loan: { principal: 45000, emi: 2800, tenureMonths: 18, outstanding: 25200, nextDueDate: "2026-04-18", dpd: 0 },
    riskInputs: { usageDropPct: 0.01, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 4, imbalance: 0 },
  },
  {
    id: "drv-005", name: "Aftab Ansari", phone: "+91 90070 11302", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0067", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2025-01-08", monthsDeployed: 15,
    cumulativeKm: 19720, avgDailyKm7d: 48, avgDailyKm30d: 46,
    sohPct: 95.4, sohDelta30d: -0.3, chargeCycles: 342, tempStressMinutes7d: 6, imbalanceEvents7d: 0, offlineHours7d: 1.5,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 11550, nextDueDate: "2026-05-02", dpd: 0 },
    riskInputs: { usageDropPct: 0.03, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 6, imbalance: 0 },
  },
  {
    id: "drv-006", name: "Rajiv Das", phone: "+91 98330 22118", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0070", batteryModelId: "er-64v-105ah", batteryModelLabel: "64V 105AH",
    onboardingDate: "2025-03-12", monthsDeployed: 13,
    cumulativeKm: 15440, avgDailyKm7d: 50, avgDailyKm30d: 45,
    sohPct: 96.8, sohDelta30d: -0.2, chargeCycles: 285, tempStressMinutes7d: 3, imbalanceEvents7d: 0, offlineHours7d: 0.6,
    loan: { principal: 58000, emi: 3600, tenureMonths: 18, outstanding: 18000, nextDueDate: "2026-04-30", dpd: 0 },
    riskInputs: { usageDropPct: 0.05, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 3, imbalance: 0 },
  },
  {
    id: "drv-007", name: "Naresh Singh", phone: "+91 91100 55420", city: "Patna",
    dealerName: "Bihar E-Mobility", batterySerial: "BAT-PAT-0044", batteryModelId: "er-51v-105ah", batteryModelLabel: "51V 105AH",
    onboardingDate: "2025-06-18", monthsDeployed: 10,
    cumulativeKm: 10820, avgDailyKm7d: 46, avgDailyKm30d: 44,
    sohPct: 97.5, sohDelta30d: -0.1, chargeCycles: 215, tempStressMinutes7d: 5, imbalanceEvents7d: 0, offlineHours7d: 0.9,
    loan: { principal: 45000, emi: 2800, tenureMonths: 18, outstanding: 22400, nextDueDate: "2026-04-26", dpd: 0 },
    riskInputs: { usageDropPct: 0.02, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 5, imbalance: 0 },
  },
  // Medium risk
  {
    id: "drv-008", name: "Shailendra Sah", phone: "+91 99300 66710", city: "Patna",
    dealerName: "Bihar E-Mobility", batterySerial: "BAT-PAT-0047", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2024-10-05", monthsDeployed: 18,
    cumulativeKm: 22100, avgDailyKm7d: 18, avgDailyKm30d: 34,
    sohPct: 92.3, sohDelta30d: -1.1, chargeCycles: 438, tempStressMinutes7d: 32, imbalanceEvents7d: 2, offlineHours7d: 8.2,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 3240, nextDueDate: "2026-04-19", dpd: 5 },
    riskInputs: { usageDropPct: 0.47, idleDays7d: 2, dpd: 5, tamperEvents30d: 1, tempStress: 32, imbalance: 2 },
  },
  {
    id: "drv-009", name: "Imran Shaikh", phone: "+91 90110 77822", city: "Delhi NCR",
    dealerName: "Capital E-Zone", batterySerial: "BAT-DL-0155", batteryModelId: "er-64v-105ah", batteryModelLabel: "64V 105AH",
    onboardingDate: "2024-12-22", monthsDeployed: 16,
    cumulativeKm: 17920, avgDailyKm7d: 26, avgDailyKm30d: 38,
    sohPct: 91.5, sohDelta30d: -1.4, chargeCycles: 390, tempStressMinutes7d: 48, imbalanceEvents7d: 3, offlineHours7d: 6.4,
    loan: { principal: 58000, emi: 3600, tenureMonths: 18, outstanding: 7200, nextDueDate: "2026-04-12", dpd: 12 },
    riskInputs: { usageDropPct: 0.31, idleDays7d: 1, dpd: 12, tamperEvents30d: 0, tempStress: 48, imbalance: 3 },
  },
  {
    id: "drv-010", name: "Santosh Mandal", phone: "+91 94440 31188", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0082", batteryModelId: "er-61v-105ah", batteryModelLabel: "61V 105AH",
    onboardingDate: "2025-01-30", monthsDeployed: 15,
    cumulativeKm: 13880, avgDailyKm7d: 22, avgDailyKm30d: 32,
    sohPct: 93.1, sohDelta30d: -0.9, chargeCycles: 360, tempStressMinutes7d: 24, imbalanceEvents7d: 1, offlineHours7d: 12.5,
    loan: { principal: 55000, emi: 3420, tenureMonths: 18, outstanding: 10260, nextDueDate: "2026-04-15", dpd: 9 },
    riskInputs: { usageDropPct: 0.31, idleDays7d: 2, dpd: 9, tamperEvents30d: 1, tempStress: 24, imbalance: 1 },
  },
  {
    id: "drv-011", name: "Mukesh Pandey", phone: "+91 99110 44033", city: "Varanasi",
    dealerName: "Kashi E-Vehicles", batterySerial: "BAT-VNS-0021", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2025-04-14", monthsDeployed: 12,
    cumulativeKm: 12400, avgDailyKm7d: 20, avgDailyKm30d: 35,
    sohPct: 93.8, sohDelta30d: -0.7, chargeCycles: 305, tempStressMinutes7d: 18, imbalanceEvents7d: 2, offlineHours7d: 5.8,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 19440, nextDueDate: "2026-04-10", dpd: 14 },
    riskInputs: { usageDropPct: 0.42, idleDays7d: 1, dpd: 14, tamperEvents30d: 0, tempStress: 18, imbalance: 2 },
  },
  {
    id: "drv-012", name: "Feroz Alam", phone: "+91 90220 11004", city: "Lucknow",
    dealerName: "Awadh E-Wheels", batterySerial: "BAT-LKO-0103", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2024-09-18", monthsDeployed: 19,
    cumulativeKm: 24200, avgDailyKm7d: 28, avgDailyKm30d: 36,
    sohPct: 90.2, sohDelta30d: -1.6, chargeCycles: 478, tempStressMinutes7d: 62, imbalanceEvents7d: 4, offlineHours7d: 9.8,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 7700, nextDueDate: "2026-04-08", dpd: 18 },
    riskInputs: { usageDropPct: 0.24, idleDays7d: 2, dpd: 18, tamperEvents30d: 1, tempStress: 62, imbalance: 4 },
  },
  // High risk
  {
    id: "drv-013", name: "Pappu Sahni", phone: "+91 98200 00145", city: "Patna",
    dealerName: "Bihar E-Mobility", batterySerial: "BAT-PAT-0055", batteryModelId: "er-61v-105ah", batteryModelLabel: "61V 105AH",
    onboardingDate: "2024-08-22", monthsDeployed: 20,
    cumulativeKm: 16800, avgDailyKm7d: 6, avgDailyKm30d: 22,
    sohPct: 88.4, sohDelta30d: -2.1, chargeCycles: 512, tempStressMinutes7d: 96, imbalanceEvents7d: 6, offlineHours7d: 38.5,
    loan: { principal: 55000, emi: 3420, tenureMonths: 18, outstanding: 13680, nextDueDate: "2026-03-28", dpd: 31 },
    riskInputs: { usageDropPct: 0.73, idleDays7d: 4, dpd: 31, tamperEvents30d: 3, tempStress: 96, imbalance: 6 },
  },
  {
    id: "drv-014", name: "Raju Kumar", phone: "+91 94110 22337", city: "Delhi NCR",
    dealerName: "Capital E-Zone", batterySerial: "BAT-DL-0170", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2024-07-14", monthsDeployed: 21,
    cumulativeKm: 14200, avgDailyKm7d: 8, avgDailyKm30d: 18,
    sohPct: 87.1, sohDelta30d: -2.8, chargeCycles: 548, tempStressMinutes7d: 142, imbalanceEvents7d: 8, offlineHours7d: 54.2,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 9720, nextDueDate: "2026-03-22", dpd: 42 },
    riskInputs: { usageDropPct: 0.56, idleDays7d: 5, dpd: 42, tamperEvents30d: 2, tempStress: 142, imbalance: 8 },
  },
  {
    id: "drv-015", name: "Guddu Yadav", phone: "+91 91540 55002", city: "Varanasi",
    dealerName: "Kashi E-Vehicles", batterySerial: "BAT-VNS-0028", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2024-06-30", monthsDeployed: 22,
    cumulativeKm: 12400, avgDailyKm7d: 0, avgDailyKm30d: 12,
    sohPct: 85.6, sohDelta30d: -3.2, chargeCycles: 582, tempStressMinutes7d: 0, imbalanceEvents7d: 12, offlineHours7d: 168,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 11550, nextDueDate: "2026-03-15", dpd: 54 },
    riskInputs: { usageDropPct: 1.0, idleDays7d: 7, dpd: 54, tamperEvents30d: 4, tempStress: 0, imbalance: 12 },
  },
  // More low risk
  {
    id: "drv-016", name: "Bablu Sharma", phone: "+91 97220 33440", city: "Delhi NCR",
    dealerName: "Sharma E-Motors", batterySerial: "BAT-DL-0180", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2025-08-05", monthsDeployed: 8,
    cumulativeKm: 9200, avgDailyKm7d: 54, avgDailyKm30d: 50,
    sohPct: 98.1, sohDelta30d: 0.1, chargeCycles: 168, tempStressMinutes7d: 2, imbalanceEvents7d: 0, offlineHours7d: 0.3,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 38500, nextDueDate: "2026-04-20", dpd: 0 },
    riskInputs: { usageDropPct: 0.03, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 2, imbalance: 0 },
  },
  {
    id: "drv-017", name: "Deepak Thakur", phone: "+91 94440 77665", city: "Lucknow",
    dealerName: "Awadh E-Wheels", batterySerial: "BAT-LKO-0112", batteryModelId: "er-64v-105ah", batteryModelLabel: "64V 105AH",
    onboardingDate: "2025-09-11", monthsDeployed: 7,
    cumulativeKm: 7800, avgDailyKm7d: 48, avgDailyKm30d: 46,
    sohPct: 98.4, sohDelta30d: 0, chargeCycles: 142, tempStressMinutes7d: 1, imbalanceEvents7d: 0, offlineHours7d: 0.2,
    loan: { principal: 58000, emi: 3600, tenureMonths: 18, outstanding: 39600, nextDueDate: "2026-04-17", dpd: 0 },
    riskInputs: { usageDropPct: 0.01, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 1, imbalance: 0 },
  },
  {
    id: "drv-018", name: "Sohan Lal", phone: "+91 98820 00112", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0090", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2025-07-28", monthsDeployed: 9,
    cumulativeKm: 10400, avgDailyKm7d: 44, avgDailyKm30d: 42,
    sohPct: 97.6, sohDelta30d: -0.1, chargeCycles: 182, tempStressMinutes7d: 3, imbalanceEvents7d: 0, offlineHours7d: 0.7,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 29160, nextDueDate: "2026-04-24", dpd: 0 },
    riskInputs: { usageDropPct: 0.04, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 3, imbalance: 0 },
  },
  {
    id: "drv-019", name: "Vikas Chauhan", phone: "+91 99820 54422", city: "Delhi NCR",
    dealerName: "Sharma E-Motors", batterySerial: "BAT-DL-0195", batteryModelId: "er-72v-232ah", batteryModelLabel: "72V 232AH",
    onboardingDate: "2025-04-10", monthsDeployed: 12,
    cumulativeKm: 15200, avgDailyKm7d: 55, avgDailyKm30d: 52,
    sohPct: 96.9, sohDelta30d: -0.2, chargeCycles: 258, tempStressMinutes7d: 4, imbalanceEvents7d: 0, offlineHours7d: 0.5,
    loan: { principal: 115000, emi: 7140, tenureMonths: 18, outstanding: 42840, nextDueDate: "2026-04-29", dpd: 0 },
    riskInputs: { usageDropPct: 0.02, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 4, imbalance: 0 },
  },
  {
    id: "drv-020", name: "Om Prakash", phone: "+91 99330 88001", city: "Patna",
    dealerName: "Bihar E-Mobility", batterySerial: "BAT-PAT-0061", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2025-03-08", monthsDeployed: 13,
    cumulativeKm: 14600, avgDailyKm7d: 46, avgDailyKm30d: 44,
    sohPct: 96.2, sohDelta30d: -0.3, chargeCycles: 275, tempStressMinutes7d: 5, imbalanceEvents7d: 0, offlineHours7d: 1.1,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 19250, nextDueDate: "2026-04-21", dpd: 0 },
    riskInputs: { usageDropPct: 0.04, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 5, imbalance: 0 },
  },
  // More medium
  {
    id: "drv-021", name: "Anwar Khan", phone: "+91 98150 22110", city: "Lucknow",
    dealerName: "Awadh E-Wheels", batterySerial: "BAT-LKO-0120", batteryModelId: "er-51v-105ah", batteryModelLabel: "51V 105AH",
    onboardingDate: "2024-12-10", monthsDeployed: 16,
    cumulativeKm: 15800, avgDailyKm7d: 24, avgDailyKm30d: 36,
    sohPct: 92.5, sohDelta30d: -1.0, chargeCycles: 362, tempStressMinutes7d: 38, imbalanceEvents7d: 2, offlineHours7d: 8.8,
    loan: { principal: 45000, emi: 2800, tenureMonths: 18, outstanding: 8400, nextDueDate: "2026-04-16", dpd: 8 },
    riskInputs: { usageDropPct: 0.33, idleDays7d: 1, dpd: 8, tamperEvents30d: 1, tempStress: 38, imbalance: 2 },
  },
  {
    id: "drv-022", name: "Chintu Paswan", phone: "+91 91440 55447", city: "Patna",
    dealerName: "Bihar E-Mobility", batterySerial: "BAT-PAT-0068", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2024-11-02", monthsDeployed: 17,
    cumulativeKm: 18200, avgDailyKm7d: 30, avgDailyKm30d: 40,
    sohPct: 91.8, sohDelta30d: -1.2, chargeCycles: 398, tempStressMinutes7d: 28, imbalanceEvents7d: 1, offlineHours7d: 6.2,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 6480, nextDueDate: "2026-04-14", dpd: 11 },
    riskInputs: { usageDropPct: 0.25, idleDays7d: 1, dpd: 11, tamperEvents30d: 0, tempStress: 28, imbalance: 1 },
  },
  {
    id: "drv-023", name: "Suresh Biswas", phone: "+91 93330 71102", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0098", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2025-02-26", monthsDeployed: 14,
    cumulativeKm: 14400, avgDailyKm7d: 29, avgDailyKm30d: 36,
    sohPct: 93.4, sohDelta30d: -0.8, chargeCycles: 328, tempStressMinutes7d: 22, imbalanceEvents7d: 1, offlineHours7d: 4.5,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 15400, nextDueDate: "2026-04-13", dpd: 7 },
    riskInputs: { usageDropPct: 0.19, idleDays7d: 1, dpd: 7, tamperEvents30d: 0, tempStress: 22, imbalance: 1 },
  },
  {
    id: "drv-024", name: "Manoj Das", phone: "+91 98900 11442", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0101", batteryModelId: "er-51v-105ah", batteryModelLabel: "51V 105AH",
    onboardingDate: "2025-05-18", monthsDeployed: 11,
    cumulativeKm: 11200, avgDailyKm7d: 25, avgDailyKm30d: 34,
    sohPct: 94.2, sohDelta30d: -0.7, chargeCycles: 268, tempStressMinutes7d: 18, imbalanceEvents7d: 1, offlineHours7d: 3.8,
    loan: { principal: 45000, emi: 2800, tenureMonths: 18, outstanding: 19600, nextDueDate: "2026-04-11", dpd: 6 },
    riskInputs: { usageDropPct: 0.26, idleDays7d: 1, dpd: 6, tamperEvents30d: 0, tempStress: 18, imbalance: 1 },
  },
  // A couple more high risk
  {
    id: "drv-025", name: "Jai Prakash", phone: "+91 90420 66770", city: "Lucknow",
    dealerName: "Awadh E-Wheels", batterySerial: "BAT-LKO-0128", batteryModelId: "er-61v-105ah", batteryModelLabel: "61V 105AH",
    onboardingDate: "2024-09-05", monthsDeployed: 19,
    cumulativeKm: 13200, avgDailyKm7d: 10, avgDailyKm30d: 20,
    sohPct: 86.8, sohDelta30d: -2.4, chargeCycles: 528, tempStressMinutes7d: 115, imbalanceEvents7d: 7, offlineHours7d: 42.8,
    loan: { principal: 55000, emi: 3420, tenureMonths: 18, outstanding: 10260, nextDueDate: "2026-03-19", dpd: 38 },
    riskInputs: { usageDropPct: 0.5, idleDays7d: 4, dpd: 38, tamperEvents30d: 2, tempStress: 115, imbalance: 7 },
  },
  {
    id: "drv-026", name: "Rajesh Tiwari", phone: "+91 99110 77820", city: "Varanasi",
    dealerName: "Kashi E-Vehicles", batterySerial: "BAT-VNS-0032", batteryModelId: "er-51v-132ah", batteryModelLabel: "51V 132AH",
    onboardingDate: "2024-08-12", monthsDeployed: 20,
    cumulativeKm: 15600, avgDailyKm7d: 12, avgDailyKm30d: 24,
    sohPct: 87.9, sohDelta30d: -2.0, chargeCycles: 498, tempStressMinutes7d: 88, imbalanceEvents7d: 5, offlineHours7d: 28.4,
    loan: { principal: 52000, emi: 3240, tenureMonths: 18, outstanding: 9720, nextDueDate: "2026-03-25", dpd: 28 },
    riskInputs: { usageDropPct: 0.5, idleDays7d: 3, dpd: 28, tamperEvents30d: 2, tempStress: 88, imbalance: 5 },
  },
  // More low
  {
    id: "drv-027", name: "Gopal Chandra", phone: "+91 98330 12880", city: "Kolkata",
    dealerName: "Bengal E-Rides", batterySerial: "BAT-KOL-0107", batteryModelId: "er-61v-132ah", batteryModelLabel: "61V 132AH",
    onboardingDate: "2025-08-22", monthsDeployed: 8,
    cumulativeKm: 9600, avgDailyKm7d: 52, avgDailyKm30d: 48,
    sohPct: 97.9, sohDelta30d: 0, chargeCycles: 175, tempStressMinutes7d: 2, imbalanceEvents7d: 0, offlineHours7d: 0.4,
    loan: { principal: 62000, emi: 3850, tenureMonths: 18, outstanding: 38500, nextDueDate: "2026-04-23", dpd: 0 },
    riskInputs: { usageDropPct: 0.02, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 2, imbalance: 0 },
  },
  {
    id: "drv-028", name: "Shiv Narayan", phone: "+91 93440 88102", city: "Delhi NCR",
    dealerName: "Sharma E-Motors", batterySerial: "BAT-DL-0205", batteryModelId: "er-51v-105ah", batteryModelLabel: "51V 105AH",
    onboardingDate: "2025-06-04", monthsDeployed: 10,
    cumulativeKm: 11200, avgDailyKm7d: 50, avgDailyKm30d: 47,
    sohPct: 97.4, sohDelta30d: -0.1, chargeCycles: 218, tempStressMinutes7d: 3, imbalanceEvents7d: 0, offlineHours7d: 0.5,
    loan: { principal: 45000, emi: 2800, tenureMonths: 18, outstanding: 22400, nextDueDate: "2026-04-27", dpd: 0 },
    riskInputs: { usageDropPct: 0.02, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 3, imbalance: 0 },
  },
  {
    id: "drv-029", name: "Jitendra Rai", phone: "+91 91110 22003", city: "Varanasi",
    dealerName: "Kashi E-Vehicles", batterySerial: "BAT-VNS-0040", batteryModelId: "er-51v-105ah", batteryModelLabel: "51V 105AH",
    onboardingDate: "2025-07-19", monthsDeployed: 9,
    cumulativeKm: 10200, avgDailyKm7d: 44, avgDailyKm30d: 42,
    sohPct: 97.7, sohDelta30d: 0, chargeCycles: 195, tempStressMinutes7d: 3, imbalanceEvents7d: 0, offlineHours7d: 0.6,
    loan: { principal: 45000, emi: 2800, tenureMonths: 18, outstanding: 25200, nextDueDate: "2026-04-26", dpd: 0 },
    riskInputs: { usageDropPct: 0.03, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 3, imbalance: 0 },
  },
  {
    id: "drv-030", name: "Kamlesh Kumar", phone: "+91 97780 44100", city: "Patna",
    dealerName: "Bihar E-Mobility", batterySerial: "BAT-PAT-0078", batteryModelId: "er-64v-105ah", batteryModelLabel: "64V 105AH",
    onboardingDate: "2025-08-30", monthsDeployed: 8,
    cumulativeKm: 8800, avgDailyKm7d: 46, avgDailyKm30d: 44,
    sohPct: 98.0, sohDelta30d: 0.1, chargeCycles: 158, tempStressMinutes7d: 2, imbalanceEvents7d: 0, offlineHours7d: 0.3,
    loan: { principal: 58000, emi: 3600, tenureMonths: 18, outstanding: 39600, nextDueDate: "2026-04-25", dpd: 0 },
    riskInputs: { usageDropPct: 0.01, idleDays7d: 0, dpd: 0, tamperEvents30d: 0, tempStress: 2, imbalance: 0 },
  },
];

function clamp01(x: number) {
  return Math.max(0, Math.min(1, x));
}

function computeRisk(inp: RiskInputs) {
  const usageScore = clamp01(inp.usageDropPct / 0.5);
  const idleScore = clamp01(inp.idleDays7d / 3);
  const paymentScore = clamp01(inp.dpd / 15);
  const tamperScore = clamp01(inp.tamperEvents30d / 5);
  const abuseScore = clamp01((inp.tempStress / 120 + inp.imbalance / 10) / 2);
  const score = Math.round(
    35 * usageScore + 20 * idleScore + 20 * paymentScore + 15 * tamperScore + 10 * abuseScore,
  );
  const geoShiftFlag = inp.tamperEvents30d > 0 || inp.usageDropPct > 0.6;
  return { score, geoShiftFlag };
}

export const portalDrivers: Driver[] = rawDrivers.map((d) => {
  const { riskInputs, ...rest } = d;
  const { score, geoShiftFlag } = computeRisk(riskInputs);
  const cds = Math.min(100, Math.round(riskInputs.dpd * 2.2 + riskInputs.idleDays7d * 6 + (riskInputs.usageDropPct > 0.4 ? 15 : 0)));
  const pci = Math.max(0, Math.min(1, 1 - riskInputs.dpd / 60 - riskInputs.usageDropPct * 0.2));
  return {
    ...rest,
    risk: {
      usageDropPct: riskInputs.usageDropPct,
      idleDays7d: riskInputs.idleDays7d,
      geoShiftFlag,
      tamperEvents30d: riskInputs.tamperEvents30d,
      cdsScore: cds,
      pci: parseFloat(pci.toFixed(2)),
      defaultRiskScore: score,
      riskBand: bandFromScore(score),
    },
  };
});

export function driversByBand(band: RiskBand): Driver[] {
  return portalDrivers.filter((d) => d.risk.riskBand === band);
}

export function countsByBand(): Record<RiskBand, number> {
  return {
    low: driversByBand("low").length,
    medium: driversByBand("medium").length,
    high: driversByBand("high").length,
  };
}

export function outstandingByBand(): Record<RiskBand, number> {
  const init = { low: 0, medium: 0, high: 0 } as Record<RiskBand, number>;
  return portalDrivers.reduce((acc, d) => {
    acc[d.risk.riskBand] += d.loan.outstanding;
    return acc;
  }, init);
}
