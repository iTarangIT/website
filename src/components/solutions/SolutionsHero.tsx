"use client";

import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function SolutionsHero() {
  return (
    <section className="relative bg-gradient-to-b from-brand-950 to-brand-900 py-20 md:py-28 overflow-hidden">
      {/* Subtle grid */}
      <div
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
        <FadeInOnScroll>
          <span className="inline-block mb-4 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest rounded-full text-brand-200 bg-brand-800">
            Platform
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight">
            The Platform That Makes{" "}
            <span className="bg-gradient-to-r from-brand-300 to-accent-green bg-clip-text text-transparent">
              Batteries Bankable
            </span>
          </h1>
          <p className="mt-6 text-lg md:text-xl text-brand-200 max-w-2xl mx-auto leading-relaxed">
            Three integrated pillars — telemetry, risk intelligence, and
            lifecycle management — working together to transform EV batteries
            from blind assets into data-rich, financeable collateral.
          </p>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
