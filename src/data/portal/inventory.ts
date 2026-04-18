export type InventoryStatus = "Received" | "Under Inspection" | "Refurbished" | "Ready for Auction" | "Scrapped";
export type Warehouse = "Delhi · Khair" | "Kolkata · Howrah" | "Lucknow · Amausi";
export type AgeBand = "0-6 mo" | "6-12 mo" | "12-18 mo" | "18-24 mo" | "24+ mo";

export interface InventoryUnit {
  id: string;
  serial: string;
  batteryId: string;
  warehouse: Warehouse;
  status: InventoryStatus;
  ageBand: AgeBand;
  sohPct: number;
  receivedOn: string;
  model: string;
  estRecoveryValue: number;
  note?: string;
}

const MODELS = ["48V 100AH", "48V 130AH", "60V 100AH", "60V 130AH", "72V 100AH", "51V 132AH", "61V 105AH"];
const STATUSES: InventoryStatus[] = ["Received", "Under Inspection", "Refurbished", "Ready for Auction", "Scrapped"];
const AGE_BANDS: AgeBand[] = ["0-6 mo", "6-12 mo", "12-18 mo", "18-24 mo", "24+ mo"];
const WAREHOUSES: Warehouse[] = ["Delhi · Khair", "Kolkata · Howrah", "Lucknow · Amausi"];

function seeded(i: number, max: number): number {
  const t = (i * 9301 + 49297) % 233280;
  return t / 233280 * max;
}

export const inventoryUnits: InventoryUnit[] = Array.from({ length: 60 }, (_, i) => {
  const status = STATUSES[Math.floor(seeded(i, STATUSES.length))];
  const warehouse = WAREHOUSES[i % WAREHOUSES.length];
  const ageBand = AGE_BANDS[Math.floor(seeded(i + 7, AGE_BANDS.length))];
  const soh = status === "Scrapped" ? 45 + Math.floor(seeded(i + 3, 18)) : 70 + Math.floor(seeded(i + 2, 22));
  const model = MODELS[Math.floor(seeded(i + 1, MODELS.length))];
  const baseValue = model.startsWith("72V") ? 75000 : model.startsWith("60V") ? 58000 : 45000;
  return {
    id: `INV-${String(2000 + i).padStart(5, "0")}`,
    serial: `BT-${String(5000 + i * 13).padStart(4, "0")}`,
    batteryId: `BT-${String(5000 + i * 13).padStart(4, "0")}`,
    warehouse,
    status,
    ageBand,
    sohPct: soh,
    receivedOn: `2026-0${Math.max(1, (i % 4) + 1)}-${String(5 + (i % 23)).padStart(2, "0")}`,
    model,
    estRecoveryValue: status === "Scrapped"
      ? Math.round(baseValue * 0.12)
      : Math.round(baseValue * (soh > 85 ? 0.65 : soh > 70 ? 0.55 : 0.4)),
    note: i === 3 ? "Cell imbalance flagged — cell replacement recommended" : i === 11 ? "Eligible for fast-track refurb" : undefined,
  };
});

export const inventorySummary = {
  totalUnits: inventoryUnits.length,
  byStatus: STATUSES.reduce<Record<InventoryStatus, number>>((acc, s) => {
    acc[s] = inventoryUnits.filter((u) => u.status === s).length;
    return acc;
  }, { Received: 0, "Under Inspection": 0, Refurbished: 0, "Ready for Auction": 0, Scrapped: 0 }),
  totalRecoveryValue: inventoryUnits.reduce((a, u) => a + u.estRecoveryValue, 0),
};
