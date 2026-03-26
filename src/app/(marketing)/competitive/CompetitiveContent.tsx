"use client";

import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import CTASection from "@/components/shared/CTASection";
import ComparisonTable from "@/components/competitive/ComparisonTable";
import { Card, CardContent } from "@/components/ui/Card";
import { Database, Shield, Layers } from "lucide-react";

const moats = [
  {
    icon: Database,
    title: "Data Flywheel",
    description:
      "Every battery monitored feeds behavioral and SOH data back into our risk engine. More data means better underwriting scores, lower defaults, and more NBFC demand -- creating a self-reinforcing loop that competitors cannot replicate without similar scale.",
    color: "bg-brand-100 text-brand-600",
  },
  {
    icon: Shield,
    title: "Regulatory Moat (EPR)",
    description:
      "Battery Waste Management Rules (2022) mandate 70-90% recovery targets. iTarang's lifecycle tracking is built from Day 1 to address EPR compliance. Competitors focused only on lending or swapping cannot offer this, giving us a structural advantage as regulations tighten.",
    color: "bg-green-100 text-green-600",
  },
  {
    icon: Layers,
    title: "Full-Lifecycle TSP Positioning",
    description:
      "No other player spans origination, monitoring, collection, and end-of-life in a single platform. This positioning means we earn fees at every stage of the battery journey, are the single integration point for NBFCs, and own the asset relationship from cradle to grave.",
    color: "bg-purple-100 text-purple-600",
  },
];

export default function CompetitiveContent() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-brand-900 py-20 md:py-28">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.15) 1px, transparent 0)",
            backgroundSize: "40px 40px",
          }}
        />
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Market Position"
              title="Competitive Landscape"
              subtitle="Mapping the EV battery ecosystem: from BaaS operators and lenders to recyclers -- and where iTarang uniquely fits."
              dark
            />
          </FadeInOnScroll>
        </div>
      </section>

      {/* Positioning Statement */}
      <section className="py-16 md:py-20 bg-brand-50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <FadeInOnScroll>
            <p className="text-2xl md:text-3xl font-bold text-brand-800 leading-snug">
              iTarang is the only full-lifecycle TSP in the market.
            </p>
            <p className="mt-4 text-lg text-gray-600 max-w-3xl mx-auto leading-relaxed">
              While competitors focus on individual segments -- lending, battery swapping,
              or recycling -- iTarang connects the entire chain from origination through
              monitoring, collection, and end-of-life recovery. This creates a compounding
              data advantage and multi-stream revenue model that no single-point solution
              can match.
            </p>
          </FadeInOnScroll>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Head-to-Head"
              title="How We Compare"
              subtitle="A detailed look at key players in the EV battery ecosystem and their capabilities."
            />
          </FadeInOnScroll>
          <ComparisonTable />
        </div>
      </section>

      {/* Moat Analysis */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Defensibility"
              title="Competitive Moats"
              subtitle="Three reinforcing moats that deepen over time and make iTarang's position increasingly defensible."
            />
          </FadeInOnScroll>

          <div className="grid gap-8 md:grid-cols-3">
            {moats.map((moat, idx) => {
              const Icon = moat.icon;
              return (
                <FadeInOnScroll key={moat.title} delay={idx * 0.12}>
                  <Card className="h-full hover:shadow-md transition-shadow">
                    <CardContent>
                      <div
                        className={`flex h-12 w-12 items-center justify-center rounded-xl ${moat.color} mb-5`}
                      >
                        <Icon className="h-6 w-6" />
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 mb-3">
                        {moat.title}
                      </h3>
                      <p className="text-sm text-gray-600 leading-relaxed">
                        {moat.description}
                      </p>
                    </CardContent>
                  </Card>
                </FadeInOnScroll>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA */}
      <CTASection
        title="Ready to Partner with the Market Leader?"
        subtitle="Learn how iTarang's full-lifecycle platform can transform your EV battery financing operations."
        primaryCTA={{ label: "For Investors", href: "/for-investors" }}
        secondaryCTA={{ label: "For NBFCs", href: "/for-nbfcs" }}
      />
    </>
  );
}
