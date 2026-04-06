import type { Metadata } from "next";
import LifecycleJourney from "@/components/how-it-works/LifecycleJourney";
import BatterySpecs from "@/components/how-it-works/BatterySpecs";
import EMICalculator from "@/components/products/EMICalculator";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import HowItWorksHero from "@/components/how-it-works/HowItWorksHero";
import BatteryComparison from "@/components/how-it-works/BatteryComparison";

export const metadata: Metadata = {
  title: "How It Works | iTarang",
  description:
    "The full EV battery lifecycle — from financing to recycling. See how iTarang manages every stage.",
};

export default function HowItWorksPage() {
  return (
    <>
      <HowItWorksHero />
      <LifecycleJourney />
      <BatteryComparison />
      <BatterySpecs />

      {/* EMI Calculator section */}
      <section className="py-20 md:py-28 bg-surface-warm">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-12">
              <span className="inline-block text-sm font-semibold text-accent-green tracking-widest uppercase mb-4 font-sans">
                Calculate
              </span>
              <h2 className="text-3xl sm:text-4xl text-gray-900 tracking-tight">
                What Will It Cost?
              </h2>
              <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto font-sans">
                Slide the price and tenure to see your daily EMI. Compare with
                what you&apos;d pay for lead-acid.
              </p>
            </div>
          </FadeInOnScroll>
          <EMICalculator />
        </div>
      </section>
    </>
  );
}
