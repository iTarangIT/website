"use client";

import {
  ImageComparison,
  ImageComparisonImage,
  ImageComparisonSlider,
} from "@/components/ui/image-comparison";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export default function BatteryComparison() {
  return (
    <section className="py-20 md:py-28 bg-surface-warm">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <div className="text-center mb-12">
            <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
              Compare
            </span>
            <h2 className="text-3xl sm:text-4xl text-gray-900 tracking-tight">
              Lead-Acid vs Lithium
            </h2>
            <p className="mt-4 text-lg text-gray-500 max-w-xl mx-auto font-sans">
              Drag the slider to compare. Same e-rickshaw, different battery
              technology.
            </p>
          </div>
        </FadeInOnScroll>

        <FadeInOnScroll delay={0.2}>
          <div className="rounded-3xl overflow-hidden border border-gray-200/60 shadow-xl shadow-gray-900/5">
            <ImageComparison
              className="aspect-video w-full"
              enableHover
            >
              <ImageComparisonImage
                src="/images/lead-acid-battery.jpg"
                className="grayscale"
                alt="Lead-acid battery — heavy, short-lived"
                position="left"
              />
              <ImageComparisonImage
                src="/images/lithium-battery.jpg"
                alt="iTarang lithium battery — lighter, longer-lasting"
                position="right"
              />
              <ImageComparisonSlider className="w-0.5 bg-white/60 backdrop-blur-sm">
                <div className="absolute top-1/2 left-1/2 size-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white shadow-lg shadow-black/20 flex items-center justify-center border border-gray-200/50">
                  <span className="text-xs font-bold text-gray-500">⟷</span>
                </div>
              </ImageComparisonSlider>
            </ImageComparison>
          </div>

          {/* Labels */}
          <div className="flex justify-between mt-6 px-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gray-400" />
              <span className="text-sm font-medium text-gray-500 font-sans">Lead-Acid: Heavy, 300 cycles</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-brand-500" />
              <span className="text-sm font-medium text-gray-500 font-sans">Lithium: Light, 2000+ cycles</span>
            </div>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
