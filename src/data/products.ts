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
    slug: "3-wheeler-batteries",
    name: "3-Wheeler Batteries",
    description: "LiFePO4 batteries engineered for Indian e-rickshaws and 3-wheelers — longer lifespan, faster charging, and lower maintenance.",
    icon: "battery",
  },
  {
    slug: "inverters",
    name: "Inverters",
    description: "Pure sine wave inverters with smart monitoring, solar-ready architecture, and robust overload protection.",
    icon: "power",
  },
  {
    slug: "chargers",
    name: "Chargers",
    description: "Smart EV chargers with multi-voltage support, fast-charge capability, and intelligent safety cutoff.",
    icon: "plug",
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

/* ──────────────────────────────────────────────
   Inverter Products
   ────────────────────────────────────────────── */

export interface InverterProduct {
  id: string;
  label: string;
  outputWattage: number;
  inputVoltage: string;
  outputVoltage: string;
  waveform: string;
  efficiency: string;
  transferTime: string;
  weight: string;
  dimensions: string;
  protections: string[];
  price: number;
  warranty: string;
  badge?: string;
}

export const inverterProducts: InverterProduct[] = [
  {
    id: "inv-1kw",
    label: "iTarang 1kW Inverter",
    outputWattage: 1000,
    inputVoltage: "12V DC",
    outputVoltage: "230V AC",
    waveform: "Pure Sine Wave",
    efficiency: "≥ 90%",
    transferTime: "< 10ms",
    weight: "5.2 kg",
    dimensions: "300 × 200 × 120 mm",
    protections: ["Overload", "Short Circuit", "Over Temperature", "Low Battery Cutoff"],
    price: 8500,
    warranty: "2 Years",
  },
  {
    id: "inv-2kw",
    label: "iTarang 2kW Inverter",
    outputWattage: 2000,
    inputVoltage: "24V DC",
    outputVoltage: "230V AC",
    waveform: "Pure Sine Wave",
    efficiency: "≥ 92%",
    transferTime: "< 10ms",
    weight: "8.4 kg",
    dimensions: "380 × 250 × 140 mm",
    protections: ["Overload", "Short Circuit", "Over Temperature", "Low Battery Cutoff", "Surge Protection"],
    price: 14500,
    warranty: "2 Years",
    badge: "Best Seller",
  },
  {
    id: "inv-3kw",
    label: "iTarang 3kW Inverter",
    outputWattage: 3000,
    inputVoltage: "48V DC",
    outputVoltage: "230V AC",
    waveform: "Pure Sine Wave",
    efficiency: "≥ 93%",
    transferTime: "< 8ms",
    weight: "12.6 kg",
    dimensions: "440 × 300 × 160 mm",
    protections: ["Overload", "Short Circuit", "Over Temperature", "Low Battery Cutoff", "Surge Protection", "Solar MPPT Ready"],
    price: 22000,
    warranty: "2 Years",
    badge: "Premium",
  },
];

export const inverterFeatures = [
  {
    title: "Pure Sine Wave Output",
    description: "Clean 230V AC output safe for sensitive electronics, fans, refrigerators, and medical equipment.",
  },
  {
    title: "Solar-Ready Architecture",
    description: "Compatible with MPPT charge controllers for seamless solar panel integration and hybrid operation.",
  },
  {
    title: "Smart Monitoring",
    description: "LED/LCD display with real-time load, battery voltage, and fault status. IoT-ready for remote monitoring.",
  },
  {
    title: "Overload Protection",
    description: "Automatic shutdown and recovery on overload, short circuit, and over-temperature conditions.",
  },
];

export const inverterFaqs = [
  {
    question: "What appliances can I run on an iTarang inverter?",
    answer: "Our pure sine wave inverters support fans, lights, TVs, refrigerators, computers, and other household electronics. The 1kW model handles basic loads, the 2kW handles medium homes, and the 3kW supports larger setups including AC units.",
  },
  {
    question: "Can I use the inverter with solar panels?",
    answer: "Yes. Our 3kW inverter is solar MPPT-ready and works with standard solar panel setups. The 1kW and 2kW models can be paired with external MPPT controllers for solar integration.",
  },
  {
    question: "What warranty do iTarang inverters come with?",
    answer: "All iTarang inverters come with a 2-year manufacturer warranty covering defects in materials and workmanship.",
  },
];

/* ──────────────────────────────────────────────
   Charger Products
   ────────────────────────────────────────────── */

export interface ChargerProduct {
  id: string;
  label: string;
  inputVoltage: string;
  outputVoltage: string;
  outputCurrent: string;
  chargingTime: string;
  efficiency: string;
  weight: string;
  dimensions: string;
  compatibility: string[];
  protections: string[];
  price: number;
  warranty: string;
  badge?: string;
}

export const chargerProducts: ChargerProduct[] = [
  {
    id: "chg-48v-15a",
    label: "iTarang 48V 15A Charger",
    inputVoltage: "170–270V AC",
    outputVoltage: "48V DC",
    outputCurrent: "15A",
    chargingTime: "3–4 hours (100Ah)",
    efficiency: "≥ 92%",
    weight: "2.8 kg",
    dimensions: "240 × 160 × 80 mm",
    compatibility: ["E-Rickshaw", "E-Cart", "48V Battery Packs"],
    protections: ["Over Voltage", "Over Current", "Short Circuit", "Reverse Polarity", "Temperature Cutoff"],
    price: 4500,
    warranty: "1 Year",
  },
  {
    id: "chg-60v-20a",
    label: "iTarang 60V 20A Charger",
    inputVoltage: "170–270V AC",
    outputVoltage: "60V DC",
    outputCurrent: "20A",
    chargingTime: "3–4 hours (130Ah)",
    efficiency: "≥ 93%",
    weight: "3.5 kg",
    dimensions: "260 × 170 × 90 mm",
    compatibility: ["E-Auto", "E-Loader", "60V Battery Packs"],
    protections: ["Over Voltage", "Over Current", "Short Circuit", "Reverse Polarity", "Temperature Cutoff", "Auto Cutoff"],
    price: 6500,
    warranty: "1 Year",
    badge: "Best Seller",
  },
  {
    id: "chg-72v-25a",
    label: "iTarang 72V 25A Charger",
    inputVoltage: "170–270V AC",
    outputVoltage: "72V DC",
    outputCurrent: "25A",
    chargingTime: "3–5 hours (232Ah)",
    efficiency: "≥ 94%",
    weight: "4.2 kg",
    dimensions: "280 × 180 × 100 mm",
    compatibility: ["E-Auto", "L5 Category", "72V Battery Packs", "Fleet Vehicles"],
    protections: ["Over Voltage", "Over Current", "Short Circuit", "Reverse Polarity", "Temperature Cutoff", "Auto Cutoff", "Fan Cooling"],
    price: 9000,
    warranty: "1 Year",
    badge: "Fleet Grade",
  },
];

export const chargerFeatures = [
  {
    title: "Smart Charging Algorithm",
    description: "CC-CV charging profile with automatic cutoff ensures optimal charging and maximum battery lifespan.",
  },
  {
    title: "Multi-Voltage Support",
    description: "Available in 48V, 60V, and 72V variants matching all iTarang battery packs and common EV platforms.",
  },
  {
    title: "Safety Cutoff System",
    description: "5-layer protection including over-voltage, over-current, short circuit, reverse polarity, and thermal cutoff.",
  },
  {
    title: "Fast Charge Capability",
    description: "High-current output (up to 25A) enables full charge in 3–5 hours, minimizing vehicle downtime.",
  },
];

export const chargerFaqs = [
  {
    question: "Which charger do I need for my e-rickshaw?",
    answer: "Match the charger voltage to your battery voltage. Most e-rickshaws use 48V or 60V batteries. Check your battery label or contact us via WhatsApp for a recommendation.",
  },
  {
    question: "Can I use the charger with non-iTarang batteries?",
    answer: "Yes. Our chargers work with any LiFePO4 battery pack of the matching voltage. However, we recommend pairing with iTarang batteries for optimal BMS communication.",
  },
  {
    question: "How long does it take to fully charge a battery?",
    answer: "Charging time depends on battery capacity and charger current. Typical times: 48V/100Ah battery with 15A charger takes 3–4 hours. 60V/130Ah with 20A charger takes 3–4 hours.",
  },
];
