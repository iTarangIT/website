export interface BatterySKU {
  id: string;
  name: string;
  voltage: number;
  capacity: number;
  energy: string;
  weight: string;
  dimensions: string;
  cycleLife: number;
  bmsFeatures: string[];
  compatibleVehicles: string[];
  price: number;
  warranty: string;
  badge?: string;
}

export const batteryProducts: BatterySKU[] = [
  {
    id: "it-48v-100ah",
    name: "iTarang 48V 100Ah",
    voltage: 48,
    capacity: 100,
    energy: "4.8 kWh",
    weight: "28 kg",
    dimensions: "340 × 225 × 280 mm",
    cycleLife: 2000,
    bmsFeatures: ["Overcharge Protection", "Short Circuit Protection", "Temperature Monitoring", "Cell Balancing", "IoT Telemetry Ready"],
    compatibleVehicles: ["E-Rickshaw (Passenger)", "E-Rickshaw (Cargo)"],
    price: 42000,
    warranty: "3 Years / 2000 Cycles",
  },
  {
    id: "it-48v-130ah",
    name: "iTarang 48V 130Ah",
    voltage: 48,
    capacity: 130,
    energy: "6.2 kWh",
    weight: "35 kg",
    dimensions: "380 × 250 × 300 mm",
    cycleLife: 2000,
    bmsFeatures: ["Overcharge Protection", "Short Circuit Protection", "Temperature Monitoring", "Cell Balancing", "IoT Telemetry Ready"],
    compatibleVehicles: ["E-Rickshaw (Passenger)", "E-Rickshaw (Cargo)", "E-Auto"],
    price: 49000,
    warranty: "3 Years / 2000 Cycles",
    badge: "Best Seller",
  },
  {
    id: "it-60v-100ah",
    name: "iTarang 60V 100Ah",
    voltage: 60,
    capacity: 100,
    energy: "6.0 kWh",
    weight: "33 kg",
    dimensions: "390 × 250 × 310 mm",
    cycleLife: 2000,
    bmsFeatures: ["Overcharge Protection", "Short Circuit Protection", "Temperature Monitoring", "Cell Balancing", "IoT Telemetry Ready", "GPS Tracking"],
    compatibleVehicles: ["E-Auto", "E-Loader"],
    price: 55000,
    warranty: "3 Years / 2000 Cycles",
  },
  {
    id: "it-60v-130ah",
    name: "iTarang 60V 130Ah",
    voltage: 60,
    capacity: 130,
    energy: "7.8 kWh",
    weight: "40 kg",
    dimensions: "420 × 270 × 320 mm",
    cycleLife: 2000,
    bmsFeatures: ["Overcharge Protection", "Short Circuit Protection", "Temperature Monitoring", "Cell Balancing", "IoT Telemetry Ready", "GPS Tracking"],
    compatibleVehicles: ["E-Auto", "E-Loader", "E-Cart"],
    price: 62000,
    warranty: "3 Years / 2000 Cycles",
    badge: "High Range",
  },
  {
    id: "it-72v-100ah",
    name: "iTarang 72V 100Ah",
    voltage: 72,
    capacity: 100,
    energy: "7.2 kWh",
    weight: "38 kg",
    dimensions: "430 × 270 × 330 mm",
    cycleLife: 2000,
    bmsFeatures: ["Overcharge Protection", "Short Circuit Protection", "Temperature Monitoring", "Cell Balancing", "IoT Telemetry Ready", "GPS Tracking", "Remote Immobilisation"],
    compatibleVehicles: ["E-Auto", "E-Loader", "E-Cart", "L5 Category"],
    price: 72000,
    warranty: "3 Years / 2000 Cycles",
    badge: "Premium",
  },
];

export const leadAcidComparison = {
  headers: ["Feature", "iTarang Lithium", "Lead-Acid"],
  rows: [
    ["Cycle Life", "2,000+ cycles", "300–400 cycles"],
    ["Weight", "28–40 kg", "60–80 kg"],
    ["Charging Time", "3–4 hours", "8–10 hours"],
    ["Range per Charge", "80–120 km", "40–60 km"],
    ["Replacement Frequency", "Every 3–5 years", "Every 8–12 months"],
    ["Total Cost (3 Years)", "₹49,000 (one-time)", "₹45,000–60,000 (3–4 replacements)"],
    ["BMS & IoT", "Built-in smart BMS + telemetry", "None"],
    ["Warranty", "3 years", "6–12 months"],
    ["Environmental Impact", "Recyclable, EPR compliant", "Toxic lead, disposal issues"],
  ],
};
