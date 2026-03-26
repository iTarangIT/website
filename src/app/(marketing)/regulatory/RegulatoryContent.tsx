"use client";

import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import CTASection from "@/components/shared/CTASection";
import RegulatoryTimeline from "@/components/regulatory/RegulatoryTimeline";
import ComplianceCards from "@/components/regulatory/ComplianceCards";
import { Card, CardContent } from "@/components/ui/Card";
import {
  ShieldCheck,
  CircleDollarSign,
  TrendingUp,
  Scale,
  CheckCircle,
} from "lucide-react";

const tspAdvantages = [
  {
    icon: ShieldCheck,
    title: "No Balance Sheet Risk",
    description:
      "As a TSP, iTarang does not lend or carry loan exposure. All credit risk sits with the NBFC partner, keeping our balance sheet clean and capital-efficient.",
  },
  {
    icon: CircleDollarSign,
    title: "Fee-Based Revenue",
    description:
      "We earn fees for services rendered -- underwriting enablement, monitoring, and collection facilitation. This creates predictable, high-margin revenue without interest rate or NPA risk.",
  },
  {
    icon: TrendingUp,
    title: "Scalable Model",
    description:
      "Without the constraints of capital adequacy requirements or provisioning norms, we can scale across geographies and NBFC partners simultaneously.",
  },
  {
    icon: Scale,
    title: "RBI-Compliant Without NBFC License",
    description:
      "Operating as a Technology Service Provider means we stay outside the RBI lending framework. No NBFC registration needed, no FLDG caps, no regulatory capital requirements.",
  },
];

export default function RegulatoryContent() {
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
              badge="Regulatory Strategy"
              title="Regulatory Moat"
              subtitle="Tightening EPR mandates, data privacy rules, and lending regulations create tailwinds for iTarang's technology-first, asset-light approach."
              dark
            />
          </FadeInOnScroll>
        </div>
      </section>

      {/* Regulatory Timeline */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="EPR Trajectory"
              title="Regulatory Timeline"
              subtitle="Battery recovery mandates are tightening every year. iTarang's lifecycle tracking becomes more essential with each milestone."
            />
          </FadeInOnScroll>
          <RegulatoryTimeline />
        </div>
      </section>

      {/* Compliance Areas */}
      <section className="py-20 md:py-28 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Compliance Landscape"
              title="Key Regulatory Areas"
              subtitle="Three regulatory domains shaping the EV battery ecosystem -- each creating strategic opportunities for iTarang."
            />
          </FadeInOnScroll>
          <ComplianceCards />
        </div>
      </section>

      {/* TSP Advantage */}
      <section className="py-20 md:py-28 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <FadeInOnScroll>
            <SectionHeading
              badge="Strategic Positioning"
              title="The TSP Advantage"
              subtitle="Why operating as a Technology Service Provider -- not a lender -- is the right structural choice."
            />
          </FadeInOnScroll>

          <div className="grid gap-6 sm:grid-cols-2">
            {tspAdvantages.map((advantage, idx) => {
              const Icon = advantage.icon;
              return (
                <FadeInOnScroll key={advantage.title} delay={idx * 0.1}>
                  <Card className="h-full hover:shadow-md transition-shadow">
                    <CardContent>
                      <div className="flex items-start gap-4">
                        <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-brand-100">
                          <Icon className="h-5 w-5 text-brand-600" />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-gray-900 mb-2">
                            {advantage.title}
                          </h3>
                          <p className="text-sm text-gray-600 leading-relaxed">
                            {advantage.description}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </FadeInOnScroll>
              );
            })}
          </div>

          {/* Summary callout */}
          <FadeInOnScroll delay={0.3}>
            <div className="mt-12 rounded-2xl bg-brand-50 border border-brand-200 p-8 md:p-10">
              <div className="flex items-start gap-4">
                <CheckCircle className="h-8 w-8 text-brand-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-xl font-bold text-brand-800 mb-2">
                    Bottom Line
                  </h3>
                  <p className="text-gray-700 leading-relaxed">
                    By positioning as a TSP rather than an NBFC, iTarang avoids the
                    capital-intensive, heavily-regulated lending model. Instead, we provide
                    the technology infrastructure that makes EV battery lending possible --
                    earning fees at every stage while our NBFC partners handle the credit
                    book. This is the same structural insight that made India&apos;s most
                    successful fintech platforms (like account aggregators and lending
                    marketplaces) capital-efficient and highly scalable.
                  </p>
                </div>
              </div>
            </div>
          </FadeInOnScroll>
        </div>
      </section>

      {/* CTA */}
      <CTASection
        title="Partner with a Regulation-Ready Platform"
        subtitle="Whether you're an NBFC looking for compliant infrastructure or an investor seeking regulatory defensibility."
        primaryCTA={{ label: "For NBFCs", href: "/for-nbfcs" }}
        secondaryCTA={{ label: "For Investors", href: "/for-investors" }}
      />
    </>
  );
}
