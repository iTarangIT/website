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
  /** Optional cover art for `BlogCard`; posts without one fall back to the category gradient. */
  coverImage?: string;
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
    slug: "electric-light-goods-vehicle-battery-planning-delhi-ncr",
    title: "Electric Light Goods Vehicles in Delhi-NCR: Battery Planning Before the Mandate",
    excerpt: "A plain-language guide for Delhi-NCR fleet owners planning lithium batteries, charging access, replacement timing, and reliability for electric light goods vehicles.",
    date: "2026-08-26",
    readTime: "6 min read",
    category: "battery-selection",
    coverImage: "/images/blog/electric-light-goods-vehicle-battery-planning-delhi-ncr-cover.svg",
  },
  {
    slug: "battery-waste-management-rules-2022-gazette-vs-market",
    title: "Battery Waste Management Rules 2022: what the gazette says, and what the internet keeps repeating",
    excerpt:
      "S.O. 958(E) makes battery QR codes optional, not mandatory. What the notifications actually say, why the wrong version spread, and three questions that let you check any compliance claim in ten minutes.",
    date: "2026-08-25",
    readTime: "6 min read",
    category: "lifecycle-recycling",
    coverImage: "/images/blog/battery-waste-management-rules-2022-gazette-vs-market-cover.svg",
  },
  {
    slug: "e-rickshaw-battery-repair-or-replacement-real-cost",
    title: "E-Rickshaw Battery Repair or Replacement: How Drivers Can Judge the Real Cost",
    excerpt: "A practical guide for e-rickshaw drivers and fleet owners comparing battery repair and replacement cost, warning signs, downtime, safety, and long-term value.",
    date: "2026-08-12",
    readTime: "5 min read",
    category: "battery-selection",
    coverImage: "/images/blog/e-rickshaw-battery-repair-or-replacement-real-cost-cover.svg",
  },
  {
    slug: "independence-day-ai-powered-ev-energy-network",
    title: "iTarang : Building Bharat's AI-Powered EV Energy Network",
    excerpt: "How an AI-powered EV Energy Network connects OEMs, dealers, financiers and consumers across every stage of an electric vehicle's lifecycle.",
    date: "2026-08-14",
    readTime: "6 min read",
    category: "partners-industry",
    coverImage: "/images/blog/independence-day-ai-powered-ev-energy-network-cover.svg",
  },
  {
    slug: "battery-as-a-service-india-electric-mobility",
    title: "Why India Is a Strong Use Case for Battery-as-a-Service in Electric Mobility",
    excerpt: "A plain-language guide to why dense urban routes, limited home charging, and e-rickshaw growth make India a strong fit for Battery-as-a-Service models.",
    date: "2026-08-14",
    readTime: "6 min read",
    category: "financing",
    coverImage: "/images/blog/battery-as-a-service-india-electric-mobility-cover.svg",
  },
];

export function categoryHasPosts(slug: BlogCategorySlug): boolean {
  return blogPosts.some((post) => post.category === slug);
}

// Categories with at least one post. Single source of truth for both the
// sitemap and the category route's robots directive, so an empty archive is
// never submitted to Google and never indexed.
export const activeBlogCategories: BlogCategory[] = blogCategories.filter(({ slug }) =>
  categoryHasPosts(slug),
);

// ISO YYYY-MM-DD dates compare correctly as strings.
export function latestPostDateInCategory(slug: BlogCategorySlug): string | undefined {
  return blogPosts
    .filter((post) => post.category === slug)
    .reduce<string | undefined>(
      (latest, post) => (latest === undefined || post.date > latest ? post.date : latest),
      undefined,
    );
}
