export interface RevenueStream {
  name: string;
  description: string;
  phase: string;
  unitEconomics: string;
  nature: string;
  icon: string;
}

export const revenueStreams: RevenueStream[] = [
  {
    name: "Underwriting Enablement Fee",
    description: "Charged to NBFC per loan approved",
    phase: "Phase 1 (Day 1)",
    unitEconomics: "₹1,500 – ₹2,500 per approved loan",
    nature: "Cash Flow Engine",
    icon: "FileCheck",
  },
  {
    name: "Telemetry SaaS Subscription",
    description: "Recurring fee for data & monitoring",
    phase: "Phase 1 (Day 1)",
    unitEconomics: "₹200 – ₹300 per battery/month",
    nature: "High Margin ARR",
    icon: "Activity",
  },
  {
    name: "Collection Infrastructure Fee",
    description: "Platform-facilitated repayment",
    phase: "Phase 2+",
    unitEconomics: "~1–2% of AUM collected",
    nature: "Volume Upside",
    icon: "Wallet",
  },
  {
    name: "Lifecycle Recovery Margin",
    description: "End-of-life value capture",
    phase: "Phase 2+ (Year 3)",
    unitEconomics: "₹3,000 – ₹8,000 per asset",
    nature: "Regulatory Moat",
    icon: "Recycle",
  },
];

export const unitEconomicsBreakdown = {
  revenue: [
    { label: "Underwriting Fee (Year 1)", amount: 2000, note: "Upfront per loan" },
    { label: "Telemetry SaaS (18 mo.)", amount: 4500, note: "₹250/mo × 18 months" },
    { label: "Collection Fee (1.5%)", amount: 1100, note: "% of AUM collected" },
    { label: "Lifecycle Margin (Year 3)", amountRange: "₹4,000 – ₹8,000", note: "Resale / Recycling" },
  ],
  totalLTV: "₹11,600 – ₹15,600",
  costs: [
    { label: "IoT Hardware", amount: 1000, note: "Amortized cost" },
    { label: "Dealer Origination", amount: 650, note: "Partner incentive" },
    { label: "Platform Ops (Cloud)", amount: 300, note: "Data storage/compute" },
    { label: "Support & Maintenance", amount: 500, note: "Service allocation" },
  ],
  totalCACCOGS: "~₹2,450",
  grossMargin: "~65–70%",
};
