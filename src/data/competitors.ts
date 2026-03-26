export interface Competitor {
  name: string;
  highlight?: boolean;
  assetFocus: string;
  iotRiskTech: string;
  lifecycleEPR: string;
  businessModel: string;
  validation?: string;
}

export const competitors: Competitor[] = [
  {
    name: "iTarang",
    highlight: true,
    assetFocus: "Battery Lifecycle (Origination → EPR)",
    iotRiskTech: "Behavioral Score + Real-time SOH",
    lifecycleEPR: "Full EPR Suite",
    businessModel: "Fee-based TSP",
  },
  {
    name: "Chargeup",
    assetFocus: "Battery-as-a-Service (BaaS)",
    iotRiskTech: "Digital Twin",
    lifecycleEPR: "Not Core",
    businessModel: "B2C Financing + Fleet Ops",
    validation: "₹20 Cr ARR, 7,000+ drivers, EBITDA+",
  },
  {
    name: "Revfin",
    assetFocus: "Vehicle-First EV Lender",
    iotRiskTech: "Psychometric Scoring",
    lifecycleEPR: "None",
    businessModel: "Lending Book (Balance Sheet)",
  },
  {
    name: "Battery Smart",
    assetFocus: "Network-First Swapping Infra",
    iotRiskTech: "Asset Tracking Only",
    lifecycleEPR: "None",
    businessModel: "Swapping Subscription Fees",
  },
  {
    name: "Attero / Lohum",
    assetFocus: "Material-First Recyclers",
    iotRiskTech: "Processing Only",
    lifecycleEPR: "Material Recovery",
    businessModel: "Recycling & Material Sales",
  },
];
