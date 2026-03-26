export interface RegulatoryMilestone {
  year: string;
  label: string;
  description: string;
}

export const regulatoryTimeline: RegulatoryMilestone[] = [
  { year: "FY24", label: "70% Recovery", description: "EPR mandate begins with 70% battery recovery target for OEMs." },
  { year: "FY25", label: "80% Recovery", description: "Recovery targets tighten to 80%, increasing compliance costs for OEMs." },
  { year: "FY26+", label: "90% Recovery", description: "Near-total recovery required. iTarang's lifecycle tracking becomes essential." },
  { year: "FY30", label: "20% Recycled Content", description: "Mandatory recycled material in new batteries. Full circular economy compliance." },
];

export const complianceAreas = [
  {
    title: "Battery Waste Management Rules (2022)",
    type: "Strong Tailwind" as const,
    points: [
      "EPR mandate: OEMs must ensure collection & recycling of end-of-life batteries",
      "Recycling targets: 70% recovery (FY24) ramping to 90% (FY26+)",
      "Recycled content: ~20% recycled material in new batteries by FY30",
    ],
    advantage: "Our lifecycle tracking module becomes essential compliance tooling for OEMs, creating a regulatory moat.",
  },
  {
    title: "Data Privacy & Devices",
    type: "Compliance" as const,
    points: [
      "DPDP Act (2023): Strict consent requirements for personal data processing",
      "BIS Certification: Mandatory safety standards for all IoT hardware",
    ],
    advantage: "Consent-first onboarding flow + exclusive procurement of BIS-certified hardware partners.",
  },
  {
    title: "RBI & Lending Framework",
    type: "Strategic Pivot" as const,
    points: [
      "FLDG Cap: First Loss Default Guarantee capped at 5% (RBI 2023 guidelines)",
      "Lending License: Operating as a lender requires NBFC registration and capital adequacy",
    ],
    advantage: "iTarang operates as a Technology Service Provider (TSP), earning fees rather than taking balance sheet risk. We enable NBFCs, we don't compete with them.",
  },
];
