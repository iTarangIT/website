export interface BlogPost {
  slug: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: string;
  coverImage: string;
}

export const blogPosts: BlogPost[] = [
  {
    slug: "informal-financing",
    title: "Why 90% of E-Rickshaw Battery Financing Is Informal — And What It Costs",
    excerpt:
      "Over 90% of e-rickshaw batteries are financed informally at 30–60% interest rates. We break down the real cost to drivers and the structural opportunity for institutional capital.",
    date: "2026-03-20",
    readTime: "6 min read",
    category: "Industry Insights",
    coverImage: "/images/blog/informal-financing-cover.webp",
  },
  {
    slug: "battery-passport",
    title: "The Battery Passport: What It Means for India's EV Circular Economy",
    excerpt:
      "From EU regulations to India's Battery Waste Management Rules — how lifecycle data creates the foundation for a bankable, circular EV battery economy.",
    date: "2026-03-15",
    readTime: "8 min read",
    category: "Vision",
    coverImage: "/images/blog/battery-passport-cover.webp",
  },
  {
    slug: "e-rickshaw-lithium-battery-compatibility-installation",
    title: "How to Check E-Rickshaw Lithium Battery Compatibility and Installation Requirements",
    excerpt:
      "A practical checklist for vehicle compatibility, model selection, dealer installation, IoT pairing, activation, and safety checks.",
    date: "2026-07-24",
    readTime: "7 min read",
    category: "Driver Guides",
    coverImage: "/images/blog/e-rickshaw-battery-compatibility-cover.webp",
  },
];
