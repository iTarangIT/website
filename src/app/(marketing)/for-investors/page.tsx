import type { Metadata } from "next";
import {
  Banknote,
  Truck,
  Activity,
  Wrench,
  RotateCcw,
  Recycle,
} from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import AnimatedCounter from "@/components/shared/AnimatedCounter";
import { deckMetrics } from "@/data/metrics";
import InvestorHero from "@/components/investors/InvestorHero";
import DeckRequestDialog from "@/components/investors/DeckRequestDialog";
import { ShineBorder } from "@/components/ui/shine-border";

export const metadata: Metadata = {
  title: "For Investors | iTarang",
  description:
    "Invest in India's first full-lifecycle EV battery platform. ₹11,250 Cr TAM. Pre-seed equity round of ₹8 Crore.",
};

const lifecycleSteps = [
  { icon: Banknote, label: "Finance", color: "from-violet-50 to-purple-50/50", iconColor: "text-violet-600", borderColor: "border-violet-200/40" },
  { icon: Truck, label: "Deploy", color: "from-blue-50 to-indigo-50/50", iconColor: "text-blue-600", borderColor: "border-blue-200/40" },
  { icon: Activity, label: "Monitor", color: "from-cyan-50 to-teal-50/50", iconColor: "text-cyan-600", borderColor: "border-cyan-200/40" },
  { icon: Wrench, label: "Maintain", color: "from-amber-50 to-orange-50/50", iconColor: "text-amber-600", borderColor: "border-amber-200/40" },
  { icon: RotateCcw, label: "Buyback", color: "from-emerald-50 to-green-50/50", iconColor: "text-emerald-600", borderColor: "border-emerald-200/40" },
  { icon: Recycle, label: "Recycle", color: "from-rose-50 to-pink-50/50", iconColor: "text-rose-600", borderColor: "border-rose-200/40" },
];

const traction = [
  { value: 150, suffix: "+", label: "Pilot batteries" },
  { value: 20, suffix: "+", label: "Dealers" },
  { value: 98, suffix: "%", label: "Recovery rate" },
  { value: 2, suffix: "", label: "NBFC LOIs" },
] as const;

export default function ForInvestorsPage() {
  return (
    <>
      <InvestorHero />

      {/* The Problem */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <span className="inline-block text-sm font-semibold text-accent-coral tracking-widest uppercase mb-4 font-sans">
              The Problem
            </span>
            <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight mb-6">
              A broken market hiding in plain sight
            </h2>
            <p className="text-lg text-gray-500 leading-relaxed font-sans">
              {deckMetrics.informalFinancingPercent}% of e-rickshaw batteries are
              financed informally. Drivers pay{" "}
              {deckMetrics.informalInterestRates} interest. Lenders can&apos;t
              see what&apos;s happening to the asset after disbursement. Batteries die
              early, get stolen, or end up in landfills with no tracking.
            </p>
          </FadeInOnScroll>
        </div>
      </section>

      {/* Lifecycle Visual */}
      <section className="py-20 md:py-24 bg-surface-warm">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-14">
              <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
                Our Solution
              </span>
              <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight">
                What We Do
              </h2>
            </div>
            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
              {lifecycleSteps.map((step) => {
                const Icon = step.icon;
                return (
                  <div
                    key={step.label}
                    className={`flex flex-col items-center gap-2.5 rounded-2xl bg-gradient-to-br ${step.color} border ${step.borderColor} p-5 hover:shadow-lg transition-shadow`}
                  >
                    <Icon className={`h-6 w-6 ${step.iconColor}`} />
                    <span className="text-sm font-semibold text-gray-900 font-sans">
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
            <p className="mt-8 text-center text-gray-400 text-sm max-w-xl mx-auto font-sans">
              No competitor covers the entire journey. Battery Smart does
              swapping. Chargeup does financing. Pointo does leasing. We manage
              the full lifecycle.
            </p>
          </FadeInOnScroll>
        </div>
      </section>

      {/* Traction */}
      <section className="py-20 md:py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(103,61,230,0.2),transparent_70%)]" />
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 relative z-10">
          <FadeInOnScroll>
            <h2 className="text-3xl md:text-4xl text-white text-center mb-14 tracking-tight">
              Traction
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {traction.map((stat, i) => (
                <div key={i} className="text-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm">
                  <AnimatedCounter
                    value={stat.value}
                    suffix={stat.suffix}
                    label={stat.label}
                  />
                </div>
              ))}
            </div>
          </FadeInOnScroll>
        </div>
      </section>

      {/* Team */}
      <section className="py-20 md:py-24 bg-white">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-10">
              <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
                Leadership
              </span>
              <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight">
                Team
              </h2>
            </div>
            <div className="flex flex-col md:flex-row gap-8 justify-center">
              <div className="flex-1 rounded-3xl bg-gradient-to-br from-surface-warm to-surface-cream border border-gray-200/40 p-8 text-center max-w-sm mx-auto hover:shadow-lg transition-shadow">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-brand-100 to-brand-200/50 mx-auto mb-4 flex items-center justify-center border border-brand-200/30">
                  <span className="text-xs text-gray-400 font-sans">Photo</span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 font-sans">Founder</h3>
                <p className="text-sm text-brand-500 font-medium font-sans">CEO / Co-founder</p>
                <p className="mt-3 text-sm text-gray-500 leading-relaxed font-sans">
                  Vision, fundraising, partnerships, regulatory
                </p>
              </div>
            </div>
          </FadeInOnScroll>
        </div>
      </section>

      {/* The Ask */}
      <section className="py-20 md:py-28 relative overflow-hidden grain-overlay">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(252,81,133,0.1),transparent_60%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(103,61,230,0.15),transparent_60%)]" />

        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 relative z-10">
          <FadeInOnScroll>
            <div className="flex flex-col md:flex-row gap-12 items-start">
              <div className="flex-1">
                <span className="inline-block text-sm font-semibold text-accent-amber tracking-widest uppercase mb-4 font-sans">
                  Investment
                </span>
                <h2 className="text-3xl md:text-4xl text-white mb-8 tracking-tight">
                  The Ask
                </h2>
                <ShineBorder
                  borderRadius={20}
                  borderWidth={2}
                  duration={8}
                  color={["#A07CFE", "#FE8FB5", "#FFBE7B"]}
                  className="w-full min-w-0 bg-white/5 backdrop-blur-sm"
                >
                  <div className="space-y-4 text-brand-200 text-lg p-5 font-sans">
                    <p>
                      <strong className="text-white">
                        {deckMetrics.raiseAmount}
                      </strong>{" "}
                      {deckMetrics.raiseType}
                    </p>
                    <p>
                      12-month goal:{" "}
                      <strong className="text-white">
                        {deckMetrics.targetBUM} batteries
                      </strong>{" "}
                      under management across{" "}
                      <strong className="text-white">
                        {deckMetrics.targetCitiesLive} cities
                      </strong>
                      .
                    </p>
                    <p>
                      Target AUM facilitated:{" "}
                      <strong className="text-white">
                        {deckMetrics.targetAUMFacilitated}
                      </strong>
                    </p>
                  </div>
                </ShineBorder>
              </div>

              <div className="w-full md:w-96">
                <DeckRequestDialog />
              </div>
            </div>
          </FadeInOnScroll>
        </div>
      </section>
    </>
  );
}
