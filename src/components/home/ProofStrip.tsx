"use client";

import AnimatedCounter from "@/components/shared/AnimatedCounter";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const proofStats = [
  { value: 150, suffix: "+", label: "Batteries monitored live", accent: "text-brand-500" },
  { value: 20, suffix: "+", label: "Dealer partners", accent: "text-blue-500" },
  { value: 98, suffix: "%", label: "Recovery rate", accent: "text-emerald-500" },
  { value: 2, suffix: "", label: "NBFC partnerships in pipeline", accent: "text-amber-500" },
] as const;

export default function ProofStrip() {
  return (
    <section className="py-20 md:py-24 relative overflow-hidden">
      {/* Rich gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(5,27,154,0.3),transparent_70%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(245,158,11,0.1),transparent_60%)]" />

      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 relative z-10">
        <FadeInOnScroll>
          <p className="text-center text-sm font-semibold text-brand-300/60 uppercase tracking-[0.2em] mb-12">
            Traction to date
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
            {proofStats.map((stat, i) => (
              <FadeInOnScroll key={i} delay={i * 0.1}>
                <div className="text-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10 transition-colors">
                  <AnimatedCounter
                    value={stat.value}
                    suffix={stat.suffix}
                    label={stat.label}
                  />
                </div>
              </FadeInOnScroll>
            ))}
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
