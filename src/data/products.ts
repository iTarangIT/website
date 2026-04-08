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

/* ──────────────────────────────────────────────
   Product Categories
   ────────────────────────────────────────────── */

export interface ProductCategory {
  slug: string;
  name: string;
  description: string;
  icon: string;
}

export const productCategories: ProductCategory[] = [
  {
    slug: "e-rickshaw-lithium-battery",
    name: "E-Rickshaw Lithium Battery",
    description: "LiFePO4 batteries engineered for Indian e-rickshaws — longer lifespan, faster charging, and lower maintenance compared to lead-acid.",
    icon: "battery",
  },
];

/* ──────────────────────────────────────────────
   E-Rickshaw Battery Variants (12 SKUs)
   ────────────────────────────────────────────── */

export interface ERickshawBattery {
  id: string;
  label: string;
  voltage: number;
  capacity: number;
  energy: string;
  weight: string;
  dimensions: string;
  cycleLife: number;
  chemistry: string;
  chargingTime: string;
  operatingTemp: string;
  range: string;
  warranty: string;
  price: number;
  badge?: string;
}

export const eRickshawBatteries: ERickshawBattery[] = [
  // 51V Series
  {
    id: "er-51v-105ah",
    label: "51V 105AH",
    voltage: 51,
    capacity: 105,
    energy: "5.376 kWh",
    weight: "32 kg",
    dimensions: "520 × 230 × 260 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "3–4 hours",
    operatingTemp: "-20°C to 60°C",
    range: "70–90 km",
    warranty: "3 Years / 2000 Cycles",
    price: 45000,
    badge: "Popular",
  },
  {
    id: "er-51v-132ah",
    label: "51V 132AH",
    voltage: 51,
    capacity: 132,
    energy: "6.758 kWh",
    weight: "38 kg",
    dimensions: "520 × 260 × 280 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "4–5 hours",
    operatingTemp: "-20°C to 60°C",
    range: "90–110 km",
    warranty: "3 Years / 2000 Cycles",
    price: 52000,
  },
  {
    id: "er-51v-153ah",
    label: "51V 153AH",
    voltage: 51,
    capacity: 153,
    energy: "7.834 kWh",
    weight: "42 kg",
    dimensions: "530 × 270 × 300 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "4–5 hours",
    operatingTemp: "-20°C to 60°C",
    range: "100–130 km",
    warranty: "3 Years / 2000 Cycles",
    price: 58000,
  },
  {
    id: "er-51v-232ah",
    label: "51V 232AH",
    voltage: 51,
    capacity: 232,
    energy: "11.878 kWh",
    weight: "58 kg",
    dimensions: "580 × 300 × 320 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "5–7 hours",
    operatingTemp: "-20°C to 60°C",
    range: "140–180 km",
    warranty: "3 Years / 2000 Cycles",
    price: 78000,
    badge: "Max Range",
  },
  // 61V Series
  {
    id: "er-61v-105ah",
    label: "61V 105AH",
    voltage: 61,
    capacity: 105,
    energy: "6.405 kWh",
    weight: "35 kg",
    dimensions: "540 × 240 × 270 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "3–4 hours",
    operatingTemp: "-20°C to 60°C",
    range: "80–100 km",
    warranty: "3 Years / 2000 Cycles",
    price: 55000,
  },
  {
    id: "er-61v-132ah",
    label: "61V 132AH",
    voltage: 61,
    capacity: 132,
    energy: "8.052 kWh",
    weight: "42 kg",
    dimensions: "540 × 270 × 290 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "4–5 hours",
    operatingTemp: "-20°C to 60°C",
    range: "100–120 km",
    warranty: "3 Years / 2000 Cycles",
    price: 62000,
    badge: "Best Seller",
  },
  {
    id: "er-61v-153ah",
    label: "61V 153AH",
    voltage: 61,
    capacity: 153,
    energy: "9.333 kWh",
    weight: "48 kg",
    dimensions: "560 × 280 × 310 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "4–6 hours",
    operatingTemp: "-20°C to 60°C",
    range: "120–150 km",
    warranty: "3 Years / 2000 Cycles",
    price: 70000,
  },
  {
    id: "er-61v-232ah",
    label: "61V 232AH",
    voltage: 61,
    capacity: 232,
    energy: "14.152 kWh",
    weight: "65 kg",
    dimensions: "600 × 310 × 340 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "6–8 hours",
    operatingTemp: "-20°C to 60°C",
    range: "160–200 km",
    warranty: "3 Years / 2000 Cycles",
    price: 95000,
    badge: "Premium",
  },
  // 64V Series
  {
    id: "er-64v-105ah",
    label: "64V 105AH",
    voltage: 64,
    capacity: 105,
    energy: "6.72 kWh",
    weight: "37 kg",
    dimensions: "550 × 245 × 275 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "3–4 hours",
    operatingTemp: "-20°C to 60°C",
    range: "85–105 km",
    warranty: "3 Years / 2000 Cycles",
    price: 58000,
  },
  {
    id: "er-64v-132ah",
    label: "64V 132AH",
    voltage: 64,
    capacity: 132,
    energy: "8.448 kWh",
    weight: "44 kg",
    dimensions: "550 × 275 × 295 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "4–5 hours",
    operatingTemp: "-20°C to 60°C",
    range: "105–130 km",
    warranty: "3 Years / 2000 Cycles",
    price: 66000,
  },
  // 72V Series
  {
    id: "er-72v-232ah",
    label: "72V 232AH",
    voltage: 72,
    capacity: 232,
    energy: "16.704 kWh",
    weight: "72 kg",
    dimensions: "620 × 320 × 360 mm",
    cycleLife: 2000,
    chemistry: "LiFePO4",
    chargingTime: "7–9 hours",
    operatingTemp: "-20°C to 60°C",
    range: "180–220 km",
    warranty: "3 Years / 2000 Cycles",
    price: 115000,
    badge: "Max Power",
  },
];

export const safetyFeatures = [
  {
    title: "Over-charge / Over-discharge Protection",
    description: "Smart BMS prevents over-charging and deep discharge, extending battery life and preventing thermal events.",
  },
  {
    title: "Short Circuit Protection",
    description: "Designed to withstand short circuits without fire or thermal runaway. Built-in fuse and BMS cutoff.",
  },
  {
    title: "Acupuncture Resistance",
    description: "LiFePO4 cells handle puncture tests without thermal runaway — the safest lithium chemistry available.",
  },
  {
    title: "Thermal Shock Protection",
    description: "Maintains performance during extreme temperature fluctuations from -20°C to 60°C operating range.",
  },
];

export const keyAdvantages = [
  { title: "Attractive Cycle Life", description: "2,000+ cycles — 5x longer than lead-acid batteries" },
  { title: "Extended Safety", description: "LiFePO4 chemistry with zero thermal runaway risk" },
  { title: "Wide Temperature Range", description: "Operates reliably from -20°C to 60°C" },
  { title: "High Temperature Performance", description: "No capacity degradation up to 45°C ambient" },
  { title: "Zero Metal Contaminants", description: "No lead, no cadmium — fully RoHS compliant" },
  { title: "Steady Voltage Output", description: "Flat discharge curve delivers consistent power throughout the ride" },
  { title: "Minimal Self-Discharge", description: "Less than 3% per month — stays charged during idle periods" },
  { title: "Vibration & Shock Resistant", description: "Engineered for Indian roads with reinforced cell housing" },
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

export const productFaqs = [
  {
    question: "What is the price of lithium battery in India?",
    answer: "The lithium battery price depends on voltage and capacity. To know more about prices visit the nearest itarang dealer, or connect through whatsapp.",
  },
  {
    question: "Why is lithium battery better for e rickshaw?",
    answer: "Lithium batteries are better for e rickshaws because they offer longer lifespan, lightweight design, fast charging and improved vehicle range.",
  },
  {
    question: "How long does an lithium battery last?",
    answer: "A good quality lithium battery can last 3 to 6 years* depending on usage and charging conditions.",
  },
];
