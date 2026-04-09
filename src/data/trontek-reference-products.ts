/**
 * Trontek Reference Product Data
 *
 * Structured competitive reference data extracted from trontek.com and verified
 * external sources. Used for iTarang product page development reference.
 *
 * IMPORTANT: Values marked as null are image-locked on trontek.com and could not
 * be extracted automatically. They require manual verification from spec sheet images.
 *
 * Sources: trontek.com, Amazon.in, IndiaMART, Energetica India, ESS News
 * Extraction date: 2026-04-08
 */

// ============================================================================
// Types
// ============================================================================

export interface SpecValue {
  value: string | number | boolean | null;
  unit?: string;
  source: "trontek-page" | "amazon" | "indiamart" | "press" | "blog" | "inferred" | "image-locked";
  confidence: "high" | "medium" | "low" | "unverified";
}

export interface ElectricalSpecs {
  nominalVoltage: SpecValue;
  ratedCapacity: SpecValue;
  energy: SpecValue;
  cellChemistry: SpecValue;
  chargingVoltage: SpecValue;
  chargingCurrent: SpecValue;
  dischargeCurrent: SpecValue;
  peakDischargeCurrent: SpecValue;
  cutoffVoltage: SpecValue;
  internalResistance: SpecValue;
}

export interface MechanicalSpecs {
  dimensions: SpecValue; // "L x W x H" format
  weight: SpecValue;
  casingMaterial: SpecValue;
  ipRating: SpecValue;
  mountingType: SpecValue;
}

export interface OperatingConditions {
  chargingTempRange: SpecValue;
  dischargingTempRange: SpecValue;
  storageTempRange: SpecValue;
  humidity: SpecValue;
}

export interface PerformanceSpecs {
  cycleLife: SpecValue;
  chargingTime: SpecValue;
  rangePerCharge: SpecValue | null; // battery only
  backupTime: SpecValue | null; // inverter only
  batteryLifespan: SpecValue;
  roundTripEfficiency: SpecValue | null; // inverter only
}

export interface SafetySpecs {
  overchargeProtection: SpecValue;
  overDischargeProtection: SpecValue;
  shortCircuitProtection: SpecValue;
  thermalProtection: SpecValue;
  cellBalancing: SpecValue;
  shockVibrationResistance: SpecValue;
  thermalRunawayResistance: SpecValue;
  bmsMonitoring: SpecValue;
}

export interface CertificationSpecs {
  aisCertification: SpecValue;
  otherCertifications: SpecValue;
}

export interface WarrantyInfo {
  warrantyDuration: SpecValue;
  serviceNotes: SpecValue;
  priceReference: SpecValue;
}

export interface PresentationData {
  seriesName: string;
  variantLabel: string;
  useCasePositioning: string;
  customerType: string;
  ctaWording: string;
  faqTopics: string[];
  specImageUrl: string;
  productImageUrl: string;
}

export interface TrontekProduct {
  category: "3w-battery" | "inverter" | "charger";
  variantId: string;
  pageUrl: string;
  electrical: ElectricalSpecs;
  mechanical: MechanicalSpecs;
  operatingConditions: OperatingConditions;
  performance: PerformanceSpecs;
  safety: SafetySpecs;
  certifications: CertificationSpecs;
  warranty: WarrantyInfo;
  presentation: PresentationData;
}

// ============================================================================
// Helper for image-locked specs
// ============================================================================

const imageLocked: SpecValue = {
  value: null,
  source: "image-locked",
  confidence: "unverified",
};

// ============================================================================
// E-Rickshaw / 3W Battery Data
// ============================================================================

const batteryCommonSafety: SafetySpecs = {
  overchargeProtection: { value: true, source: "trontek-page", confidence: "high" },
  overDischargeProtection: { value: true, source: "trontek-page", confidence: "high" },
  shortCircuitProtection: { value: true, source: "trontek-page", confidence: "high" },
  thermalProtection: { value: true, source: "trontek-page", confidence: "high" },
  cellBalancing: { value: true, source: "blog", confidence: "high" },
  shockVibrationResistance: { value: true, source: "trontek-page", confidence: "high" },
  thermalRunawayResistance: { value: true, source: "trontek-page", confidence: "high" },
  bmsMonitoring: {
    value: "Voltage, current, SOC, SOH, temperature, cell balancing",
    source: "blog",
    confidence: "high",
  },
};

const batteryCommonCerts: CertificationSpecs = {
  aisCertification: { value: "Referenced", source: "trontek-page", confidence: "medium" },
  otherCertifications: imageLocked,
};

const batteryCommonOperating: OperatingConditions = {
  chargingTempRange: imageLocked,
  dischargingTempRange: { value: "-20°C to 60°C", source: "indiamart", confidence: "high" },
  storageTempRange: imageLocked,
  humidity: imageLocked,
};

function makeBatteryVariant(
  variantId: string,
  voltage: number,
  capacity: number,
  energyKwh: number,
  positioning: string,
  specImageFile: string,
  productImageFile: string,
  extraMechanical?: Partial<MechanicalSpecs>,
): TrontekProduct {
  return {
    category: "3w-battery",
    variantId,
    pageUrl: "https://trontek.com/products/e-rickshaw-lithium-battery/",
    electrical: {
      nominalVoltage: { value: voltage, unit: "V", source: "trontek-page", confidence: "high" },
      ratedCapacity: { value: capacity, unit: "AH", source: "trontek-page", confidence: "high" },
      energy: { value: energyKwh, unit: "kWh", source: "trontek-page", confidence: "high" },
      cellChemistry: { value: "LiFePO4", source: "trontek-page", confidence: "high" },
      chargingVoltage: imageLocked,
      chargingCurrent: imageLocked,
      dischargeCurrent: imageLocked,
      peakDischargeCurrent: imageLocked,
      cutoffVoltage: imageLocked,
      internalResistance: imageLocked,
    },
    mechanical: {
      dimensions: extraMechanical?.dimensions ?? imageLocked,
      weight: extraMechanical?.weight ?? imageLocked,
      casingMaterial: imageLocked,
      ipRating: imageLocked,
      mountingType: { value: "Vehicle-mounted (e-rickshaw)", source: "inferred", confidence: "high" },
    },
    operatingConditions: batteryCommonOperating,
    performance: {
      cycleLife: { value: "2000+", unit: "cycles at 25°C", source: "indiamart", confidence: "high" },
      chargingTime: imageLocked,
      rangePerCharge: { value: "80-120", unit: "km", source: "blog", confidence: "medium" },
      backupTime: null,
      batteryLifespan: { value: "3-6", unit: "years", source: "trontek-page", confidence: "high" },
      roundTripEfficiency: null,
    },
    safety: batteryCommonSafety,
    certifications: batteryCommonCerts,
    warranty: {
      warrantyDuration: { value: 36, unit: "months", source: "amazon", confidence: "high" },
      serviceNotes: { value: "Via Trontek dealer network", source: "trontek-page", confidence: "high" },
      priceReference: { value: "Starts from INR 55,000", source: "trontek-page", confidence: "high" },
    },
    presentation: {
      seriesName: "E-Rickshaw Lithium Battery",
      variantLabel: `${voltage}V ${capacity}AH (${energyKwh}kWh)`,
      useCasePositioning: positioning,
      customerType: "E-rickshaw drivers, fleet operators",
      ctaWording: "Enquire Now / Visit nearest Trontek dealer",
      faqTopics: [
        "Price of e rickshaw lithium battery in India",
        "Why lithium battery is better for e rickshaw",
        "How long does an e rickshaw lithium battery last",
      ],
      specImageUrl: `https://trontek.com/wp-content/themes/trontek/assets/img/${specImageFile}`,
      productImageUrl: `https://trontek.com/wp-content/themes/trontek/assets/img/${productImageFile}`,
    },
  };
}

export const eRickshawBatteries: TrontekProduct[] = [
  makeBatteryVariant(
    "51v-105ah", 51, 105, 5.376,
    "Standard daily commercial use, longer driving range, faster charging",
    "51v-105ah-product.jpg", "51V%20105AH%20main.png",
  ),
  makeBatteryVariant(
    "51v-132ah", 51, 132, 6.758,
    "High-performance, extended range, superior durability, commercial usage",
    "51v-132ah-product.jpg", "51V%20132AH.png",
    {
      dimensions: { value: "59 x 38 x 28.5 cm", source: "amazon", confidence: "high" },
      weight: { value: 54.1, unit: "kg", source: "amazon", confidence: "high" },
    },
  ),
  makeBatteryVariant(
    "51v-153ah", 51, 153, 7.834,
    "Enhanced power, longer range for demanding routes, continuous commercial use",
    "51v-105ah-product.jpg", "51V%20132AH.png",
  ),
  makeBatteryVariant(
    "51v-232ah", 51, 232, 11.878,
    "Maximum range, heavy-duty performance, fewer charging cycles",
    "51v-232ah-product.jpg", "51V%20232AH.png",
  ),
  makeBatteryVariant(
    "61v-105ah", 61, 105, 6.405,
    "Optimized performance, daily commuting and commercial ops",
    "61V-105Ah-product.jpg", "61V%20105Ah%20d.png",
  ),
  makeBatteryVariant(
    "61v-132ah", 61, 132, 8.052,
    "Extended performance, longer driving range, high efficiency",
    "61V-132Ah-product.jpg", "61V%20132AH.png",
  ),
  makeBatteryVariant(
    "61v-153ah", 61, 153, 9.333,
    "Higher capacity, better efficiency, long-distance usage",
    "61v-153ah-product.jpg", "61V%20153AH.png",
  ),
  makeBatteryVariant(
    "61v-232ah", 61, 232, 14.152,
    "Premium high-capacity, maximum range, heavy-duty, intensive daily ops",
    "61v-232ah-product.jpg", "61V%20153AH.png",
  ),
  makeBatteryVariant(
    "64v-105ah", 64, 105, 6.72,
    "Efficient power delivery, city operations, reduced costs",
    "64v-105ah-product.jpg", "64V%20105AH.png",
  ),
  makeBatteryVariant(
    "64v-132ah", 64, 132, 8.448,
    "Enhanced efficiency, longer range, energy savings",
    "64v-132ah-product.jpg", "64V%20132AH.png",
  ),
  makeBatteryVariant(
    "72v-232ah", 72, 232, 16.704,
    "Highest capacity, maximum performance, long-distance and heavy-load",
    "73v-232ah-product.jpg", "74V%20232AH.png",
  ),
];

// ============================================================================
// Inverter Battery Data (Powercube)
// ============================================================================

export const inverterBatteries: TrontekProduct[] = [
  {
    category: "inverter",
    variantId: "powercube-1.4-plus",
    pageUrl: "https://trontek.com/products/lithium-inverter-battery-home/",
    electrical: {
      nominalVoltage: { value: 12.8, unit: "V", source: "press", confidence: "high" },
      ratedCapacity: { value: 105, unit: "AH", source: "press", confidence: "high" },
      energy: { value: 1.4, unit: "kWh", source: "press", confidence: "high" },
      cellChemistry: { value: "LiFePO4", source: "press", confidence: "high" },
      chargingVoltage: imageLocked,
      chargingCurrent: imageLocked,
      dischargeCurrent: imageLocked,
      peakDischargeCurrent: imageLocked,
      cutoffVoltage: imageLocked,
      internalResistance: imageLocked,
    },
    mechanical: {
      dimensions: imageLocked,
      weight: imageLocked,
      casingMaterial: { value: "Compact, sealed", source: "press", confidence: "high" },
      ipRating: imageLocked,
      mountingType: imageLocked,
    },
    operatingConditions: {
      chargingTempRange: imageLocked,
      dischargingTempRange: imageLocked,
      storageTempRange: imageLocked,
      humidity: imageLocked,
    },
    performance: {
      cycleLife: { value: "4000+", unit: "cycles", source: "press", confidence: "high" },
      chargingTime: imageLocked,
      rangePerCharge: null,
      backupTime: imageLocked,
      batteryLifespan: { value: "8-10", unit: "years", source: "trontek-page", confidence: "high" },
      roundTripEfficiency: { value: ">90%", source: "press", confidence: "high" },
    },
    safety: {
      overchargeProtection: { value: true, source: "press", confidence: "high" },
      overDischargeProtection: { value: true, source: "press", confidence: "high" },
      shortCircuitProtection: { value: true, source: "press", confidence: "high" },
      thermalProtection: { value: true, source: "press", confidence: "high" },
      cellBalancing: { value: true, source: "inferred", confidence: "medium" },
      shockVibrationResistance: imageLocked,
      thermalRunawayResistance: imageLocked,
      bmsMonitoring: {
        value: "Real-time SOC, SOH, voltage, temperature",
        source: "press",
        confidence: "high",
      },
    },
    certifications: {
      aisCertification: { value: "N/A", source: "inferred", confidence: "medium" },
      otherCertifications: imageLocked,
    },
    warranty: {
      warrantyDuration: imageLocked,
      serviceNotes: { value: "Via authorised distributors", source: "press", confidence: "high" },
      priceReference: { value: "Starts from Rs. 20,000", source: "trontek-page", confidence: "high" },
    },
    presentation: {
      seriesName: "Powercube",
      variantLabel: "Powercube 1.4+ (1.4 kWh)",
      useCasePositioning: "Home power backup, solar integration, reliable backup during outages",
      customerType: "Homeowners, small businesses, solar users",
      ctaWording: "Enquire Now / Visit nearest Trontek dealer",
      faqTopics: [
        "What is a lithium ion battery for inverter",
        "Inverter battery price in India",
        "Best inverter battery for home",
        "How long does a lithium inverter battery last",
      ],
      specImageUrl:
        "https://trontek.com/wp-content/themes/trontek/assets/img/Home%20(TK12100%20TK25100).jpg",
      productImageUrl:
        "https://trontek.com/wp-content/themes/trontek/assets/img/home-product.png",
    },
  },
  {
    category: "inverter",
    variantId: "powercube-2.7-plus",
    pageUrl: "https://trontek.com/products/lithium-inverter-battery-home/",
    electrical: {
      nominalVoltage: { value: 25.6, unit: "V", source: "press", confidence: "high" },
      ratedCapacity: { value: 105, unit: "AH", source: "press", confidence: "high" },
      energy: { value: 2.7, unit: "kWh", source: "press", confidence: "high" },
      cellChemistry: { value: "LiFePO4", source: "press", confidence: "high" },
      chargingVoltage: imageLocked,
      chargingCurrent: imageLocked,
      dischargeCurrent: imageLocked,
      peakDischargeCurrent: imageLocked,
      cutoffVoltage: imageLocked,
      internalResistance: imageLocked,
    },
    mechanical: {
      dimensions: imageLocked,
      weight: imageLocked,
      casingMaterial: { value: "Compact, sealed", source: "press", confidence: "high" },
      ipRating: imageLocked,
      mountingType: imageLocked,
    },
    operatingConditions: {
      chargingTempRange: imageLocked,
      dischargingTempRange: imageLocked,
      storageTempRange: imageLocked,
      humidity: imageLocked,
    },
    performance: {
      cycleLife: { value: "4000+", unit: "cycles", source: "press", confidence: "high" },
      chargingTime: imageLocked,
      rangePerCharge: null,
      backupTime: imageLocked,
      batteryLifespan: { value: "8-10", unit: "years", source: "trontek-page", confidence: "high" },
      roundTripEfficiency: { value: ">90%", source: "press", confidence: "high" },
    },
    safety: {
      overchargeProtection: { value: true, source: "press", confidence: "high" },
      overDischargeProtection: { value: true, source: "press", confidence: "high" },
      shortCircuitProtection: { value: true, source: "press", confidence: "high" },
      thermalProtection: { value: true, source: "press", confidence: "high" },
      cellBalancing: { value: true, source: "inferred", confidence: "medium" },
      shockVibrationResistance: imageLocked,
      thermalRunawayResistance: imageLocked,
      bmsMonitoring: {
        value: "Real-time SOC, SOH, voltage, temperature",
        source: "press",
        confidence: "high",
      },
    },
    certifications: {
      aisCertification: { value: "N/A", source: "inferred", confidence: "medium" },
      otherCertifications: imageLocked,
    },
    warranty: {
      warrantyDuration: imageLocked,
      serviceNotes: { value: "Via authorised distributors", source: "press", confidence: "high" },
      priceReference: { value: "Starts from Rs. 20,000", source: "trontek-page", confidence: "high" },
    },
    presentation: {
      seriesName: "Powercube",
      variantLabel: "Powercube 2.7+ (2.7 kWh)",
      useCasePositioning: "Home power backup, solar integration, higher capacity for larger homes",
      customerType: "Homeowners, small businesses, solar users",
      ctaWording: "Enquire Now / Visit nearest Trontek dealer",
      faqTopics: [
        "What is a lithium ion battery for inverter",
        "Inverter battery price in India",
        "Best inverter battery for home",
        "How long does a lithium inverter battery last",
      ],
      specImageUrl:
        "https://trontek.com/wp-content/themes/trontek/assets/img/Home%20(TK12100%20TK25100).jpg",
      productImageUrl:
        "https://trontek.com/wp-content/themes/trontek/assets/img/home-product.png",
    },
  },
];

// ============================================================================
// EV Charger Data (TK W-Series)
// ============================================================================

const chargerCommonSafety: SafetySpecs = {
  overchargeProtection: { value: true, source: "amazon", confidence: "high" },
  overDischargeProtection: imageLocked,
  shortCircuitProtection: { value: true, source: "amazon", confidence: "high" },
  thermalProtection: { value: true, source: "amazon", confidence: "high" },
  cellBalancing: { value: "N/A", source: "inferred", confidence: "high" },
  shockVibrationResistance: imageLocked,
  thermalRunawayResistance: imageLocked,
  bmsMonitoring: { value: "N/A (charger, not battery)", source: "inferred", confidence: "high" },
};

function makeCharger(
  modelNumber: string,
  wattage: number,
  imageFile: string,
  specImageFile: string,
  extraMechanical?: Partial<MechanicalSpecs>,
): TrontekProduct {
  return {
    category: "charger",
    variantId: `tk${wattage}-w-series`,
    pageUrl: `https://trontek.com/products/tk${wattage}-w-series`,
    electrical: {
      nominalVoltage: imageLocked,
      ratedCapacity: { value: "N/A", source: "inferred", confidence: "high" },
      energy: { value: wattage, unit: "W (from model name)", source: "inferred", confidence: "medium" },
      cellChemistry: { value: "N/A (charger)", source: "inferred", confidence: "high" },
      chargingVoltage: imageLocked,
      chargingCurrent: imageLocked,
      dischargeCurrent: imageLocked,
      peakDischargeCurrent: imageLocked,
      cutoffVoltage: imageLocked,
      internalResistance: imageLocked,
    },
    mechanical: {
      dimensions: extraMechanical?.dimensions ?? imageLocked,
      weight: extraMechanical?.weight ?? imageLocked,
      casingMaterial: { value: "Hermetic and durable seal structure", source: "trontek-page", confidence: "high" },
      ipRating: imageLocked,
      mountingType: imageLocked,
    },
    operatingConditions: {
      chargingTempRange: imageLocked,
      dischargingTempRange: imageLocked,
      storageTempRange: imageLocked,
      humidity: imageLocked,
    },
    performance: {
      cycleLife: { value: "N/A (charger)", source: "inferred", confidence: "high" },
      chargingTime: imageLocked,
      rangePerCharge: null,
      backupTime: null,
      batteryLifespan: { value: "N/A (charger)", source: "inferred", confidence: "high" },
      roundTripEfficiency: imageLocked,
    },
    safety: {
      ...chargerCommonSafety,
      overchargeProtection: { value: true, source: "amazon", confidence: "high" },
    },
    certifications: {
      aisCertification: imageLocked,
      otherCertifications: imageLocked,
    },
    warranty: {
      warrantyDuration: modelNumber === "TK-500"
        ? { value: 1, unit: "year", source: "amazon", confidence: "high" }
        : imageLocked,
      serviceNotes: imageLocked,
      priceReference: imageLocked,
    },
    presentation: {
      seriesName: "EV Charger W-Series",
      variantLabel: `${modelNumber} W-Series`,
      useCasePositioning: "EV charging across multiple verticals",
      customerType: "E-rickshaw owners, EV users, fleet operators",
      ctaWording: "Enquire Now",
      faqTopics: [], // No FAQ on charger pages
      specImageUrl: `https://trontek.com/wp-content/themes/trontek/assets/img/${specImageFile}`,
      productImageUrl: `https://trontek.com/wp-content/themes/trontek/assets/img/${imageFile}`,
    },
  };
}

export const evChargers: TrontekProduct[] = [
  makeCharger("TK-500", 500, "TK500W.png", "Tk-500.jpg", {
    dimensions: { value: "12.2 x 18.7 x 6.8 cm", source: "amazon", confidence: "high" },
    weight: { value: 1.65, unit: "kg", source: "amazon", confidence: "high" },
  }),
  makeCharger("TK-840", 840, "TK840W.png", "Tk-840.jpg"),
  makeCharger("TK-1350", 1350, "TK1350W.png", "Tk-1350.jpg"),
  makeCharger("TK-2000", 2000, "TK2000W.png", "Tk-2000.jpg"),
  makeCharger("TK-3000", 3000, "TK3000W.png", "Tk-3000.jpg"),
];

// ============================================================================
// Combined export
// ============================================================================

export const trontekReferenceProducts = {
  eRickshawBatteries,
  inverterBatteries,
  evChargers,
};

export default trontekReferenceProducts;
