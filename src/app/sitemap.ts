import type { MetadataRoute } from "next";
import { blogPosts } from "@/data/blog-posts";

const BASE_URL = "https://www.itarang.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    { path: "/", priority: 1.0, changeFrequency: "weekly" as const },
    { path: "/how-it-works", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/e-rickshaw-lithium-battery-models-specifications", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/e-rickshaw-battery-warranty-service-replacement-support", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/for-partners", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/for-drivers", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/for-dealers", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/for-oems", priority: 0.9, changeFrequency: "monthly" as const },
    { path: "/about", priority: 0.8, changeFrequency: "monthly" as const },
    { path: "/contact", priority: 0.8, changeFrequency: "yearly" as const },
    { path: "/for-investors", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/blog", priority: 0.7, changeFrequency: "weekly" as const },
  ];

  return [
    ...routes.map((route) => ({
      url: `${BASE_URL}${route.path}`,
      lastModified: new Date(),
      changeFrequency: route.changeFrequency,
      priority: route.priority,
    })),
    ...blogPosts.map((post) => ({
      url: `${BASE_URL}/blog/${post.slug}`,
      lastModified: post.date,
      changeFrequency: "yearly" as const,
      priority: 0.6,
    })),
  ];
}
