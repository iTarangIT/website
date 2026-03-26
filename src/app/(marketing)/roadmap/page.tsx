import type { Metadata } from "next";
import { createMetadata } from "@/lib/metadata";
import {
  Battery,
  Target,
  Landmark,
  MapPin,
  TrendingUp,
  ShieldCheck,
} from "lucide-react";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import CTASection from "@/components/shared/CTASection";
import PhaseTimeline from "@/components/roadmap/PhaseTimeline";
import ExecutionLayers from "@/components/roadmap/ExecutionLayers";
import { Card, CardContent } from "@/components/ui/Card";
import { deckMetrics } from "@/data/metrics";

export const metadata: Metadata = createMetadata({
  title: "GTM Strategy & Roadmap",
  description:
    "iTarang's go-to-market strategy: scaling from 3 cities to 90 cities across 36 months. Phased execution with Batteries Under Management as the North Star metric.",
  path: "/roadmap",
});

const milestones = [
  {
    icon: Battery,
    value: deckMetrics.targetBUM,
    label: "Batteries Under Management",
    color: "text-brand-600",
    bg: "bg-brand-50",
  },
  {
    icon: Landmark,
    value: `${deckMetrics.targetNBFCIntegrations}`,
    label: "NBFC Integrations",
    color: "text-pink-600",
    bg: "bg-pink-50",
  },
  {
    icon: MapPin,
    value: `${deckMetrics.targetCitiesLive}`,
    label: "Cities Live",
    color: "text-green-600",
    bg: "bg-green-50",
  },
  {
    icon: TrendingUp,
    value: deckMetrics.targetAUMFacilitated,
    label: "AUM Facilitated",
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
  {
    icon: ShieldCheck,
    value: deckMetrics.targetNPA,
    label: "NPA Target",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
];

const bumGrowth = [
  { phase: "Phase 1", value: "3,000", label: "Foundation", width: "15%" },
  { phase: "Phase 2", value: "25,000", label: "Scale", width: "55%" },
  { phase: "Phase 3", value: "1M+", label: "Data Points", width: "100%" },
];

export default function RoadmapPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-brand-900 py-24 md:py-32">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.3) 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-brand-900 via-brand-900 to-brand-800" />

        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <FadeInOnScroll>
            <SectionHeading
              badge="Go-To-Market"
              title="GTM Strategy & Roadmap"
              subtitle="A phased plan to scale from 3 cities to a national footprint of 90 cities -- building India's largest EV battery intelligence network over 36 months."
              dark
            />
          </FadeInOnScroll>
        </div>
      </section>

      {/* Phase Timeline */}
      <div>
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 md:pt-28">
          <FadeInOnScroll>
            <SectionHeading
              badge="3-Phase Plan"
              title="Phased Execution Roadmap"
              subtitle="From MVP to national platform -- each phase builds on the last."
            />
          </FadeInOnScroll>
        </div>
        <PhaseTimeline />
      </div>

      {/* BUM North Star Metric */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="North Star Metric"
              title="Batteries Under Management"
              subtitle="BUM is our single most important metric. It captures the total number of EV batteries financed, monitored, and managed through the iTarang platform -- the foundation of every revenue stream."
            />
          </FadeInOnScroll>

          <FadeInOnScroll delay={0.2}>
            <div className="space-y-6 mt-4">
              {bumGrowth.map((item, idx) => (
                <div key={item.phase} className="space-y-2">
                  <div className="flex items-baseline justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold text-gray-500">
                        {item.phase}
                      </span>
                      <span className="text-xs text-gray-400">
                        {item.label}
                      </span>
                    </div>
                    <span className="text-lg md:text-xl font-extrabold text-brand-700">
                      {item.value}
                    </span>
                  </div>
                  <div className="h-4 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000"
                      style={{
                        width: item.width,
                        background:
                          idx === 0
                            ? "linear-gradient(90deg, #673de6, #8b5cf6)"
                            : idx === 1
                              ? "linear-gradient(90deg, #5025d1, #673de6)"
                              : "linear-gradient(90deg, #2f1c6a, #5025d1)",
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </FadeInOnScroll>

          <FadeInOnScroll delay={0.3}>
            <div className="mt-10 rounded-xl bg-brand-50 border border-brand-100 p-6 text-center">
              <p className="text-sm text-brand-700 font-medium">
                Every battery under management generates underwriting fees,
                telemetry SaaS revenue, collection commissions, and lifecycle
                recovery value -- compounding returns as the network grows.
              </p>
            </div>
          </FadeInOnScroll>
        </div>
      </section>

      {/* Execution Layers */}
      <div className="bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Execution Strategy"
              title="Three Execution Layers"
              subtitle="Parallel workstreams that build on each other to create a defensible moat."
            />
          </FadeInOnScroll>
        </div>
        <ExecutionLayers />
      </div>

      {/* 12-Month Milestones */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Year 1 Targets"
              title="12-Month Milestones"
              subtitle="Concrete, measurable targets for our first year of execution."
            />
          </FadeInOnScroll>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
            {milestones.map((m, idx) => (
              <FadeInOnScroll key={m.label} delay={idx * 0.1}>
                <Card className="text-center hover:shadow-md transition-shadow h-full">
                  <CardContent className="pt-6">
                    <div
                      className={`mx-auto w-12 h-12 rounded-xl ${m.bg} flex items-center justify-center mb-4`}
                    >
                      <m.icon className={`h-6 w-6 ${m.color}`} />
                    </div>
                    <p className={`text-2xl md:text-3xl font-extrabold ${m.color}`}>
                      {m.value}
                    </p>
                    <p className="text-sm text-gray-500 mt-1.5 font-medium">
                      {m.label}
                    </p>
                  </CardContent>
                </Card>
              </FadeInOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTASection
        title="Ready to Back the Platform?"
        subtitle="Join us in building the intelligence layer for India's EV battery economy."
        primaryCTA={{ label: "View Investor Deck", href: "/for-investors" }}
        secondaryCTA={{ label: "Contact Founders", href: "/contact" }}
      />
    </>
  );
}
