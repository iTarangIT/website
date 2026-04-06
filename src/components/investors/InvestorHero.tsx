"use client";

import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { GridPattern } from "@/components/ui/grid-pattern";
import { deckMetrics } from "@/data/metrics";
import { cn } from "@/lib/utils";
import { TrendingUp } from "lucide-react";

export default function InvestorHero() {
  return (
    <section className="pt-28 pb-20 md:pt-36 md:pb-28 relative overflow-hidden grain-overlay">
      {/* Dark gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />

      {/* Ambient glows */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-[radial-gradient(ellipse,rgba(5,27,154,0.2),transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-[radial-gradient(ellipse,rgba(252,81,133,0.08),transparent_70%)] pointer-events-none" />

      <GridPattern
        width={40}
        height={40}
        squares={[
          [3, 3], [6, 2], [8, 4], [12, 6], [15, 3],
          [4, 8], [7, 10], [10, 12],
        ]}
        className={cn(
          "fill-brand-400/8 stroke-brand-400/15",
          "[mask-image:radial-gradient(500px_circle_at_center,white,transparent)]",
        )}
      />
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 relative z-10">
        <FadeInOnScroll>
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 px-4 py-1.5 mb-6">
            <TrendingUp className="h-3.5 w-3.5 text-accent-amber" />
            <span className="text-xs font-semibold text-brand-200 tracking-widest uppercase font-sans">
              For Investors
            </span>
          </div>

          <h1 className="text-4xl md:text-6xl lg:text-7xl text-white tracking-tight leading-[1.05]">
            The Full Battery Lifecycle.
            <br />
            <span className="gradient-text">One Platform.</span>
          </h1>
          <p className="mt-6 text-xl text-brand-200/80 max-w-2xl leading-relaxed font-sans">
            India&apos;s EV battery economy is a{" "}
            <strong className="text-white">
              {deckMetrics.annualReplacementTAM}
            </strong>{" "}
            annual market with no intelligence layer. We&apos;re building it.
          </p>
        </FadeInOnScroll>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent" />
    </section>
  );
}
