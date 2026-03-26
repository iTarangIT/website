"use client";

import { Play } from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function FounderVideoPlaceholder() {
  return (
    <FadeInOnScroll>
      <div className="relative rounded-2xl overflow-hidden aspect-video max-w-4xl mx-auto cursor-pointer group">
        {/* Dark background */}
        <div className="absolute inset-0 bg-brand-900" />

        {/* Pattern overlay */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.5) 1px, transparent 0)",
            backgroundSize: "24px 24px",
          }}
        />

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-brand-950/90 via-brand-900/50 to-transparent" />
        <div className="absolute inset-0 bg-gradient-to-br from-brand-800/30 via-transparent to-accent-pink/10" />

        {/* Content */}
        <div className="relative flex flex-col items-center justify-center h-full px-6 text-center">
          {/* Play button */}
          <div className="w-20 h-20 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center mb-6 group-hover:bg-white/20 group-hover:scale-110 transition-all duration-300">
            <Play className="h-8 w-8 text-white ml-1" />
          </div>

          <p className="text-white text-lg md:text-xl font-semibold max-w-md">
            Hear directly from our founders about the iTarang vision
          </p>
          <p className="text-brand-300 text-sm mt-2">Coming soon</p>
        </div>
      </div>
    </FadeInOnScroll>
  );
}
