export type BlogCategorySlug =
  | "financing"
  | "battery-selection"
  | "charging-maintenance"
  | "safety"
  | "lifecycle-recycling"
  | "partners-industry";

export interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: BlogCategorySlug;
  coverImage: string;
}

export interface BlogCategory {
  name: string;
  slug: BlogCategorySlug;
  description: string;
}

export const blogCategories: BlogCategory[] = [
  { name: "Financing", slug: "financing", description: "Battery price, EMI, eligibility, and financing workflows." },
  { name: "Battery Selection", slug: "battery-selection", description: "Voltage, capacity, compatibility, and purchase decisions." },
  { name: "Charging & Maintenance", slug: "charging-maintenance", description: "Charging practice, battery care, alerts, and troubleshooting." },
  { name: "Safety", slug: "safety", description: "Safe charging, handling, installation checks, and escalation." },
  { name: "Lifecycle & Recycling", slug: "lifecycle-recycling", description: "Battery health, replacement, second life, and recycling." },
  { name: "Partners & Industry", slug: "partners-industry", description: "Dealer, OEM, NBFC, policy, and ecosystem topics." },
];

export const blogPosts: BlogPost[] = [
  {
    slug: "informal-financing",
    title: "Why 90% of E-Rickshaw Battery Financing Is Informal — And What It Costs",
    excerpt:
      "Over 90% of e-rickshaw batteries are financed informally at 30–60% interest rates. We break down the real cost to drivers and the structural opportunity for institutional capital.",
    date: "2026-03-20",
    readTime: "6 min read",
    category: "financing",
    coverImage: "/images/blog/informal-financing-cover.webp",
  },
  {
    slug: "battery-passport",
    title: "The Battery Passport: What It Means for India's EV Circular Economy",
    excerpt:
      "From EU regulations to India's Battery Waste Management Rules — how lifecycle data creates the foundation for a bankable, circular EV battery economy.",
    date: "2026-03-15",
    readTime: "8 min read",
    category: "partners-industry",
    coverImage: "/images/blog/battery-passport-cover.webp",
  },
  {
    slug: "e-rickshaw-lithium-battery-compatibility-installation",
    title: "How to Check E-Rickshaw Lithium Battery Compatibility and Installation Requirements",
    excerpt:
      "A practical checklist for vehicle compatibility, model selection, dealer installation, IoT pairing, activation, and safety checks.",
    date: "2026-07-24",
    readTime: "7 min read",
    category: "battery-selection",
    coverImage: "/images/blog/e-rickshaw-battery-compatibility-cover.webp",
  },
  {
    slug: "e-rickshaw-battery-maintenance-alerts-troubleshooting",
    title: "E-Rickshaw Battery Maintenance Alerts and Troubleshooting FAQ",
    excerpt:
      "Understand battery health, charging, temperature, range, and anomaly alerts, with safe driver checks and service-escalation guidance.",
    date: "2026-07-27",
    readTime: "8 min read",
    category: "charging-maintenance",
    coverImage: "/images/blog/e-rickshaw-battery-maintenance-cover.webp",
  },
];
