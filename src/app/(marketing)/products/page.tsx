import type { Metadata } from "next";
import ProductHero from "@/components/products/ProductHero";
import ProductsPageClient from "@/components/products/ProductsPageClient";
import StatsStrip from "@/components/shared/StatsStrip";
import TrustBadgeStrip from "@/components/shared/TrustBadgeStrip";

const productStats = [
  { value: 12, suffix: "+", label: "Battery Variants" },
  { value: 2000, suffix: "+", label: "Cycle Life" },
  { value: 3, suffix: " Year", label: "Warranty" },
  { value: 18, suffix: "+", label: "Products" },
] as const;

export const metadata: Metadata = {
  title: "Products | iTarang",
  description:
    "Browse iTarang's range of 3-wheeler lithium batteries, pure sine wave inverters, and smart EV chargers. Longer lifespan, faster charging, built-in IoT.",
};

export default function ProductsPage() {
  return (
    <>
      <ProductHero
        title="Our Products"
        subtitle="LiFePO4 batteries, pure sine wave inverters, and smart chargers — engineered for Indian commercial EVs and homes. Explore our full range below."
        breadcrumb={[{ label: "Products", href: "/products" }]}
      />

      <StatsStrip stats={productStats} />
      <TrustBadgeStrip />

      <ProductsPageClient />
    </>
  );
}
