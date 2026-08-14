import type { Metadata } from "next";
import dynamic from "next/dynamic";
import LifecycleJourney from "@/components/how-it-works/LifecycleJourney";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import HowItWorksHero from "@/components/how-it-works/HowItWorksHero";

const BatteryComparison = dynamic(() => import("@/components/how-it-works/BatteryComparison"), {
  loading: () => <div className="min-h-[420px] bg-white" aria-hidden="true" />,
});
const LoanCalculator = dynamic(() => import("@/components/products/LoanCalculator"), {
  loading: () => <div className="min-h-[520px] rounded-2xl border border-gray-200 bg-white/50" aria-label="Loan calculator loading" />,
});

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

      {/* Loan Calculator section */}
      <section className="py-20 md:py-28 bg-surface-warm">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-12">
              <span className="inline-block text-sm font-semibold text-accent-green tracking-widest uppercase mb-4 font-sans">
                Calculate
              </span>
              <h2 className="text-3xl sm:text-4xl text-gray-900 tracking-tight">
                What Will It Cost?
              </h2>
              <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto font-sans">
                Pick your city, battery model and tenure to see the EMI schemes
                you qualify for across our financing partners.
              </p>
            </div>
          </FadeInOnScroll>
          <LoanCalculator />
        </div>
      </section>
    </>
  );
}
