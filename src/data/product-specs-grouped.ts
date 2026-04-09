import type { ERickshawBattery, InverterProduct, ChargerProduct } from "./products";

export interface SpecRow {
  label: string;
  value: string | null;
}

export interface SpecGroup {
  groupKey: string;
  groupLabel: string;
  specs: SpecRow[];
}

// ─── Battery Spec Groups ───────────────────────────────────────────────

export function getBatterySpecGroups(b: ERickshawBattery): SpecGroup[] {
  const cells = Math.round(b.voltage / 3.2);
  const maxChargeVoltage = (cells * 3.65).toFixed(1);
  const dischargeCutoff = (cells * 2.8).toFixed(1);
  const stdChargeCurrent = Math.round(b.capacity * 0.5);
  const maxChargeCurrent = b.capacity;
  const continuousDischargeCurrent = b.capacity;
  const peakDischargeCurrent = Math.round(b.capacity * 2);
  const impedance = b.capacity <= 105 ? "≤ 25mΩ" : b.capacity <= 153 ? "≤ 20mΩ" : "≤ 15mΩ";

  return [
    {
      groupKey: "electrical",
      groupLabel: "Electrical Characteristics",
      specs: [
        { label: "Nominal Voltage", value: `${b.voltage}V` },
        { label: "Rated Capacity", value: `${b.capacity}Ah` },
        { label: "Battery Pack Energy", value: b.energy },
        { label: "Cell Chemistry", value: b.chemistry },
        { label: "Cell Configuration", value: `${cells}S` },
        { label: "Impedance (Max. at 1000Hz)", value: impedance },
        { label: "Expected Cycle Life", value: `More than ${b.cycleLife.toLocaleString()} Cycles` },
      ],
    },
    {
      groupKey: "mechanical",
      groupLabel: "Mechanical Characteristics",
      specs: [
        { label: "Dimensions (L × W × H)", value: b.dimensions },
        { label: "Weight", value: b.weight },
        { label: "Casing Material", value: "ABS Flame-retardant" },
        { label: "Mounting", value: "Vehicle-mounted (e-rickshaw)" },
      ],
    },
    {
      groupKey: "operating",
      groupLabel: "Operation Conditions",
      specs: [
        { label: "Max. Charge Voltage", value: `${maxChargeVoltage}V` },
        { label: "Standard Charge Current", value: `${stdChargeCurrent}A (0.5C)` },
        { label: "Max. Charge Current", value: `${maxChargeCurrent}A (1C)` },
        { label: "Continuous Discharge Current", value: `${continuousDischargeCurrent}A` },
        { label: "Peak Instant Discharge Current", value: `${peakDischargeCurrent}A` },
        { label: "Peak Instant Discharge Time", value: "3 seconds" },
        { label: "Discharge Cut-off Voltage", value: `${dischargeCutoff}V` },
        { label: "Discharge Temperature", value: b.operatingTemp },
        { label: "Storage Temperature", value: "-10°C to 45°C" },
      ],
    },
    {
      groupKey: "performance",
      groupLabel: "Performance Characteristics",
      specs: [
        { label: "Cycle Life", value: `${b.cycleLife.toLocaleString()}+ cycles` },
        { label: "Charging Time", value: b.chargingTime },
        { label: "Range per Charge", value: b.range },
        { label: "Expected Lifespan", value: "3–6 years" },
        { label: "Self-Discharge", value: "< 3% per month" },
      ],
    },
    {
      groupKey: "safety",
      groupLabel: "Safety / Protection / BMS",
      specs: [
        { label: "Overcharge Protection", value: "Yes — auto cutoff" },
        { label: "Over-discharge Protection", value: "Yes — low-voltage cutoff" },
        { label: "Short Circuit Protection", value: "Yes — fuse + BMS cutoff" },
        { label: "Thermal Protection", value: "Yes — thermal shutdown" },
        { label: "Cell Balancing", value: "Active balancing via BMS" },
        { label: "Vibration / Shock Resistance", value: "Reinforced cell housing" },
        { label: "BMS Monitoring", value: "Voltage, current, SOC, temperature" },
        { label: "IoT Telemetry", value: "Ready" },
      ],
    },
    {
      groupKey: "certifications",
      groupLabel: "Certifications / Compliance",
      specs: [
        { label: "AIS Compliance", value: "AIS-156 Referenced" },
        { label: "Environmental", value: "RoHS Compliant" },
        { label: "EPR Status", value: "EPR Registered" },
      ],
    },
    {
      groupKey: "warranty",
      groupLabel: "Warranty / Service",
      specs: [
        { label: "Warranty", value: b.warranty },
        { label: "Service Network", value: "Pan-India dealer network" },
        { label: "Price", value: `₹${b.price.toLocaleString("en-IN")}` },
      ],
    },
  ];
}

// ─── Inverter Spec Groups ──────────────────────────────────────────────

export function getInverterSpecGroups(inv: InverterProduct): SpecGroup[] {
  return [
    {
      groupKey: "electrical",
      groupLabel: "Electrical Characteristics",
      specs: [
        { label: "Output Power", value: `${inv.outputWattage}W` },
        { label: "Input Voltage", value: inv.inputVoltage },
        { label: "Output Voltage", value: inv.outputVoltage },
        { label: "Waveform", value: inv.waveform },
        { label: "Efficiency", value: inv.efficiency },
        { label: "Transfer Time", value: inv.transferTime },
      ],
    },
    {
      groupKey: "mechanical",
      groupLabel: "Mechanical Characteristics",
      specs: [
        { label: "Dimensions (L × W × H)", value: inv.dimensions },
        { label: "Weight", value: inv.weight },
        { label: "Casing Material", value: "Powder-coated metal" },
        { label: "Mounting", value: "Wall-mounted / floor-standing" },
        { label: "Cooling", value: "Intelligent fan cooling" },
      ],
    },
    {
      groupKey: "operating",
      groupLabel: "Operating Conditions",
      specs: [
        { label: "Operating Temperature", value: "0°C to 50°C" },
        { label: "Storage Temperature", value: "-10°C to 60°C" },
        { label: "Humidity", value: "≤ 90% RH (non-condensing)" },
      ],
    },
    {
      groupKey: "performance",
      groupLabel: "Performance Characteristics",
      specs: [
        { label: "Efficiency", value: inv.efficiency },
        { label: "Transfer Time", value: inv.transferTime },
        { label: "Solar Compatibility", value: inv.protections.includes("Solar MPPT Ready") ? "MPPT Ready" : "Via external controller" },
      ],
    },
    {
      groupKey: "safety",
      groupLabel: "Safety / Protection",
      specs: inv.protections.map((p) => ({ label: p, value: "Yes" })),
    },
    {
      groupKey: "certifications",
      groupLabel: "Certifications / Compliance",
      specs: [
        { label: "BIS Certification", value: "BIS Certified" },
        { label: "Environmental", value: "RoHS Compliant" },
      ],
    },
    {
      groupKey: "warranty",
      groupLabel: "Warranty / Service",
      specs: [
        { label: "Warranty", value: inv.warranty },
        { label: "Service Network", value: "Pan-India dealer network" },
        { label: "Price", value: `₹${inv.price.toLocaleString("en-IN")}` },
      ],
    },
  ];
}

// ─── Charger Spec Groups ───────────────────────────────────────────────

export function getChargerSpecGroups(chg: ChargerProduct): SpecGroup[] {
  return [
    {
      groupKey: "electrical",
      groupLabel: "Electrical Characteristics",
      specs: [
        { label: "Input Voltage", value: chg.inputVoltage },
        { label: "Output Voltage", value: chg.outputVoltage },
        { label: "Output Current", value: chg.outputCurrent },
        { label: "Charging Algorithm", value: "CC-CV (Constant Current → Constant Voltage)" },
        { label: "Efficiency", value: chg.efficiency },
      ],
    },
    {
      groupKey: "mechanical",
      groupLabel: "Mechanical Characteristics",
      specs: [
        { label: "Dimensions (L × W × H)", value: chg.dimensions },
        { label: "Weight", value: chg.weight },
        { label: "Casing", value: "Hermetic sealed, ABS housing" },
        { label: "Cooling", value: chg.protections.includes("Fan Cooling") ? "Active fan cooling" : "Passive convection" },
      ],
    },
    {
      groupKey: "operating",
      groupLabel: "Operating Conditions",
      specs: [
        { label: "Operating Temperature", value: "-10°C to 45°C" },
        { label: "Storage Temperature", value: "-20°C to 60°C" },
        { label: "Humidity", value: "≤ 85% RH (non-condensing)" },
      ],
    },
    {
      groupKey: "performance",
      groupLabel: "Performance Characteristics",
      specs: [
        { label: "Charging Time", value: chg.chargingTime },
        { label: "Efficiency", value: chg.efficiency },
        { label: "Compatibility", value: chg.compatibility.join(", ") },
        { label: "Indicator", value: "LED status (charging / full / fault)" },
      ],
    },
    {
      groupKey: "safety",
      groupLabel: "Safety / Protection",
      specs: chg.protections.map((p) => ({ label: p, value: "Yes" })),
    },
    {
      groupKey: "certifications",
      groupLabel: "Certifications / Compliance",
      specs: [
        { label: "BIS Certification", value: "BIS Certified" },
        { label: "Environmental", value: "RoHS Compliant" },
      ],
    },
    {
      groupKey: "warranty",
      groupLabel: "Warranty / Service",
      specs: [
        { label: "Warranty", value: chg.warranty },
        { label: "Service Network", value: "Pan-India dealer network" },
        { label: "Price", value: `₹${chg.price.toLocaleString("en-IN")}` },
      ],
    },
  ];
}
