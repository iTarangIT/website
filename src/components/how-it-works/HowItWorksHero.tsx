"use client";

import { Zap, ArrowDown } from "lucide-react";
import { GridPattern } from "@/components/ui/grid-pattern";
import { cn } from "@/lib/utils";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function HowItWorksHero() {
  return (
    <section className="pt-28 pb-20 md:pt-36 md:pb-28 relative overflow-hidden grain-overlay">
      {/* Dark gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800" />

      {/* Ambient glows */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-[radial-gradient(ellipse,rgba(5,27,154,0.2),transparent_70%)] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-[radial-gradient(ellipse,rgba(245,158,11,0.08),transparent_70%)] pointer-events-none" />

      {/* Grid pattern */}
      <GridPattern
        width={48}
        height={48}
        squares={[
          [2, 2], [5, 3], [8, 1], [11, 5], [14, 2],
          [3, 7], [7, 9], [10, 11], [13, 8],
        ]}
        className={cn(
          "fill-brand-400/8 stroke-brand-400/15",
          "[mask-image:radial-gradient(600px_circle_at_70%_30%,white,transparent)]",
        )}
      />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <FadeInOnScroll>
          {/* Eyebrow */}
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/10 px-4 py-1.5 mb-6">
            <Zap className="h-3.5 w-3.5 text-accent-amber" />
            <span className="text-xs font-semibold text-brand-200 tracking-widest uppercase font-sans">
              The Battery Lifecycle
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl text-white tracking-tight leading-[1.05]">
            How It Works
          </h1>
          <p className="mt-6 text-xl md:text-2xl text-brand-200/80 max-w-2xl leading-relaxed font-sans">
            One platform. Six stages. The full lifecycle of every battery —
            managed from first charge to last.
          </p>

          {/* Scroll indicator */}
          <a
            href="#lifecycle-journey"
            className="mt-10 inline-flex items-center gap-2 text-sm text-brand-300/60 hover:text-brand-200 transition-colors font-sans"
          >
            <span>Explore the journey</span>
            <ArrowDown className="h-4 w-4 animate-bounce" />
          </a>
        </FadeInOnScroll>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-white to-transparent" />
    </section>
  );
}
