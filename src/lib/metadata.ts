import type { Metadata } from "next";

interface MetadataInput {
  title: string;
  description: string;
  path: string;
  ogImage?: string;
}

export function createMetadata({ title, description, path, ogImage }: MetadataInput): Metadata {
  const fullTitle = `${title} | iTarang Technologies`;
  return {
    title: fullTitle,
    description,
    openGraph: {
      title: fullTitle,
      description,
      url: `https://www.itarang.com${path}`,
      siteName: "iTarang Technologies",
      images: [ogImage || "/og-image.jpg"],
      type: "website",
    },
    twitter: { card: "summary_large_image" },
    alternates: { canonical: `https://www.itarang.com${path}` },
  };
}
