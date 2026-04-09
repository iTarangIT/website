"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  productCategories,
  productFaqs,
  inverterFaqs,
  chargerFaqs,
} from "@/data/products";
import ERickshawProductView from "./ERickshawProductView";
import InverterProductView from "./InverterProductView";
import ChargerProductView from "./ChargerProductView";
import ComparisonToggle from "./ComparisonToggle";
import EMICalculator from "./EMICalculator";
import FAQAccordion from "./FAQAccordion";
import WhyITarang from "./WhyITarang";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import CTASection from "@/components/shared/CTASection";

const faqMap: Record<string, { question: string; answer: string }[]> = {
  "3-wheeler-batteries": productFaqs,
  inverters: inverterFaqs,
  chargers: chargerFaqs,
};

export default function ProductsPageClient() {
  const [activeCategory, setActiveCategory] = useState(productCategories[0].slug);
  const [initialVariant, setInitialVariant] = useState<string | null>(null);

  // Read hash from URL: supports #category or #category:variantId
  useEffect(() => {
    function handleHash() {
      const raw = window.location.hash.replace("#", "");
      if (!raw) return;

      const [category, variant] = raw.split(":");
      if (category && productCategories.some((c) => c.slug === category)) {
        setActiveCategory(category);
        setInitialVariant(variant ?? null);
      }
    }

    handleHash();
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  return (
    <>
      {/* Category Content — category is selected via URL hash from navbar dropdown */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeCategory}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          {activeCategory === "3-wheeler-batteries" && (
            <>
              <ERickshawProductView initialVariantId={initialVariant} />

              {/* Comparison — only for batteries */}
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
            </>
          )}

          {activeCategory === "inverters" && <InverterProductView initialVariantId={initialVariant} />}

          {activeCategory === "chargers" && <ChargerProductView initialVariantId={initialVariant} />}
        </motion.div>
      </AnimatePresence>

      {/* Why iTarang — universal across all categories */}
      <WhyITarang />

      {/* EMI Calculator — always visible */}
      <section className="py-16 md:py-24 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-12">
              <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
                Financing
              </span>
              <h2 className="text-3xl sm:text-4xl text-gray-900 tracking-tight">
                EMI Calculator
              </h2>
              <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto font-sans">
                Estimate your monthly payments and total cost of ownership.
              </p>
            </div>
          </FadeInOnScroll>
          <EMICalculator />
        </div>
      </section>

      {/* FAQ — category-specific */}
      <FAQAccordion faqs={faqMap[activeCategory]} />

      {/* Bottom CTA */}
      <CTASection
        title="Ready to Power Your Fleet?"
        subtitle="Get a custom quote for batteries, inverters, or chargers. We handle financing, installation, and IoT setup."
        primaryCTA={{ label: "Get a Quote", href: "/contact" }}
        secondaryCTA={{ label: "How It Works", href: "/how-it-works" }}
      />
    </>
  );
}
