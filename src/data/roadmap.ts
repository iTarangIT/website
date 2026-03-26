export interface RoadmapPhase {
  phase: number;
  title: string;
  timeline: string;
  keyMetric: string;
  metricLabel: string;
  details: string[];
  color: string;
}

export const roadmapPhases: RoadmapPhase[] = [
  {
    phase: 1,
    title: "Foundation",
    timeline: "0–12 Months",
    keyMetric: "~3,000 BUM",
    metricLabel: "Batteries Under Management",
    details: [
      "MVP Platform Live",
      "2 NBFC API Integrations",
      "3 Cities Launched",
      "Core Team Hired",
    ],
    color: "#673de6",
  },
  {
    phase: 2,
    title: "Scale",
    timeline: "12–24 Months",
    keyMetric: "~25,000 BUM",
    metricLabel: "Batteries Under Management",
    details: [
      "15 Cities Operational",
      "100 Dealer Network",
      "Launch i-Distribution",
      "Lifecycle Ops Active",
    ],
    color: "#5025d1",
  },
  {
    phase: 3,
    title: "Product Depth",
    timeline: "24–36 Months",
    keyMetric: ">1M Data Points",
    metricLabel: "National Platform",
    details: [
      "National Footprint (90 Cities)",
      "Private Label Launch",
      "Deep EPR Tooling",
      "Second-Life Partnerships",
    ],
    color: "#2f1c6a",
  },
];

export const executionLayers = [
  {
    title: "Dealer Network",
    target: "20–30 Key EV Dealers in UP/NCR",
    offer: "POS Integration + Referral Fees",
    goal: "Origination Pipeline",
    timing: "Months 1–6",
  },
  {
    title: "NBFC Integrations",
    target: "2–3 EV-focused NBFCs",
    offer: "API Risk Score + Real-time Monitoring",
    goal: "Capital Throughput",
    timing: "Months 3–9",
  },
  {
    title: "Data Flywheel",
    target: "Network Effects",
    offer: "Telemetry → Better Risk Score → Lower NPA",
    goal: "Defensible Moat",
    timing: "Month 6+",
  },
];
