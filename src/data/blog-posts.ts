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
  /** Optional. `BlogCard` renders a category gradient, so no post needs one today. */
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
    slug: "e-rickshaw-battery-repair-or-replacement-real-cost",
    title: "E-Rickshaw Battery Repair or Replacement: How Drivers Can Judge the Real Cost",
    excerpt: "A practical guide for e-rickshaw drivers and fleet owners comparing battery repair and replacement cost, warning signs, downtime, safety, and long-term value.",
    date: "2026-08-12",
    readTime: "5 min read",
    category: "battery-selection",
  },
  {
    slug: "independence-day-ai-powered-ev-energy-network",
    title: "iTarang : Building Bharat's AI-Powered EV Energy Network",
    excerpt: "How an AI-powered EV Energy Network connects OEMs, dealers, financiers and consumers across every stage of an electric vehicle's lifecycle.",
    date: "2026-08-14",
    readTime: "6 min read",
    category: "partners-industry",
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
