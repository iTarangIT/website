import type { Metadata } from "next";
import { Shield } from "lucide-react";
import AnimatedCounter from "@/components/shared/AnimatedCounter";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

export const metadata: Metadata = {
  title: "About | iTarang",
  description:
    "The team behind iTarang — building India's first full-lifecycle EV battery management platform.",
};

const traction = [
  { value: 150, suffix: "+", label: "Batteries monitored" },
  { value: 20, suffix: "+", label: "Dealer partners" },
  { value: 98, suffix: "%", label: "Recovery rate" },
  { value: 2, suffix: "", label: "NBFC LOIs" },
] as const;

export default function AboutPage() {
  return (
    <>
      {/* Hero */}
      <section className="pt-28 pb-16 md:pt-36 md:pb-20 relative overflow-hidden">
        <div className="absolute inset-0 bg-surface-warm" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(103,61,230,0.06),transparent_60%)]" />
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
          <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
            Our Story
          </span>
          <h1 className="text-5xl md:text-7xl text-gray-900 tracking-tight leading-[1.05]">
            About iTarang
          </h1>
          <p className="mt-6 text-xl text-gray-500 max-w-2xl leading-relaxed font-sans">
            We&apos;re building the infrastructure that makes EV batteries
            bankable, trackable, and recyclable across India.
          </p>
          <div className="mt-6 flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-lg bg-brand-500/10 flex items-center justify-center">
              <Shield className="h-3.5 w-3.5 text-brand-500" />
            </div>
            <span className="text-sm text-brand-600 font-semibold font-sans">
              DPIIT Recognised Startup &middot; Gurugram, India
            </span>
          </div>
        </div>
      </section>

      {/* Founder */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="flex flex-col md:flex-row gap-12 items-center">
              {/* Photo placeholder */}
              <div className="w-full md:w-1/3">
                <div className="rounded-3xl bg-gradient-to-br from-brand-100 to-surface-cream aspect-square flex items-center justify-center border border-brand-200/30">
                  <span className="text-sm text-gray-400 font-sans">
                    PHOTO: Founder headshot
                  </span>
                </div>
              </div>

              {/* Bio */}
              <div className="w-full md:w-2/3">
                <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-3 font-sans">
                  The Founder
                </span>
                <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight">
                  Building from the ground up
                </h2>
                <p className="mt-5 text-lg text-gray-500 leading-relaxed font-sans">
                  Vision and strategy leader driving iTarang&apos;s mission to
                  bring formal financing and lifecycle intelligence to
                  India&apos;s EV battery market. Previously worked across
                  fintech and clean-energy sectors.
                </p>

                {/* Video placeholder */}
                <div className="mt-8 rounded-2xl bg-gradient-to-br from-gray-50 to-surface-cream border border-gray-200/50 aspect-video flex items-center justify-center max-w-lg overflow-hidden group cursor-pointer hover:border-brand-300 transition-colors">
                  <div className="text-center">
                    <div className="w-14 h-14 rounded-full bg-brand-500/10 flex items-center justify-center mx-auto mb-3 group-hover:bg-brand-500/20 transition-colors">
                      <span className="text-brand-500 text-2xl ml-1">&#9654;</span>
                    </div>
                    <span className="text-sm text-gray-400 font-sans">
                      60-second founder intro
                    </span>
                  </div>
                </div>
              </div>
            </div>
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
              Where We Are Today
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

      {/* Field Photos Grid */}
      <section className="py-20 md:py-28 bg-surface-warm">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <div className="text-center mb-14">
              <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4 font-sans">
                From the Field
              </span>
              <h2 className="text-3xl md:text-4xl text-gray-900 tracking-tight">
                Real work, real impact
              </h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                "Team at work",
                "Dealer visit",
                "Battery warehouse",
                "E-rickshaw with battery",
                "IoT device installation",
                "Driver interaction",
              ].map((label) => (
                <div
                  key={label}
                  className="rounded-2xl bg-gradient-to-br from-gray-100 to-surface-cream aspect-[4/3] flex items-center justify-center border border-gray-200/40 hover:border-brand-200 transition-colors group overflow-hidden"
                >
                  <span className="text-xs text-gray-400 font-sans group-hover:text-gray-500 transition-colors">
                    PHOTO: {label}
                  </span>
                </div>
              ))}
            </div>
          </FadeInOnScroll>
        </div>
      </section>
    </>
  );
}
