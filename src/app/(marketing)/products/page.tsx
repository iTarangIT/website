import type { Metadata } from "next";
import ProductHero from "@/components/products/ProductHero";
import ERickshawProductView from "@/components/products/ERickshawProductView";
import SafetyFeatures from "@/components/products/SafetyFeatures";
import KeyAdvantages from "@/components/products/KeyAdvantages";
import ComparisonToggle from "@/components/products/ComparisonToggle";
import FAQAccordion from "@/components/products/FAQAccordion";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import Button from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "Products | iTarang",
  description:
    "Browse iTarang's range of LiFePO4 lithium batteries for commercial EVs. Longer lifespan, faster charging, built-in IoT.",
};

export default function ProductsPage() {
  return (
    <>
      <ProductHero
        title="Our Products"
        subtitle="LiFePO4 batteries engineered for Indian commercial EVs — longer lifespan, faster charging, and lower maintenance compared to lead-acid. Explore our variants below."
        breadcrumb={[{ label: "Products", href: "/products" }]}
      />

      {/* The pills and variant details are rendered here */}
      <ERickshawProductView />

      {/* Comparison section */}
      <section className="py-16 md:py-24 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-12">
              <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
                Comparison
              </span>
              <h2 className="text-3xl sm:text-4xl text-gray-900 tracking-tight">
                Lithium vs Lead-Acid
              </h2>
              <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto font-sans">
                See why drivers and fleet owners are switching to LiFePO4.
              </p>
            </div>
          </FadeInOnScroll>
          <ComparisonToggle />
        </div>
      </section>

      {/* FAQ Accordion */}
      <FAQAccordion />

      {/* Bottom CTA */}
      <section className="py-16 md:py-24 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-950 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(5,27,154,0.3),transparent_60%)]" />
        <div className="relative z-10 mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Ready to Switch to Lithium?
          </h2>
          <p className="mt-4 text-lg text-brand-200/70 font-sans">
            Get a custom quote for your fleet. We handle financing, installation, and IoT setup.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Button href="/contact" size="lg" className="shadow-xl shadow-brand-500/30">
              Get a Quote
            </Button>
            <Button href="/how-it-works" size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10">
              How It Works
            </Button>
          </div>
        </div>
      </section>
    </>
  );
}
