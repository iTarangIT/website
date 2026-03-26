"use client";

import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import PillarCard from "@/components/solutions/PillarCard";
import { Cpu, ShieldCheck, Recycle } from "lucide-react";

const pillars = [
  {
    icon: Cpu,
    title: "Smart Battery Telemetry",
    description:
      "IoT-enabled real-time monitoring that transforms every battery into a data-rich, financeable asset. Know the exact health, location, and usage of every battery in your portfolio.",
    features: [
      "Real-time State of Health (SOH) and State of Charge (SOC) tracking",
      "GPS location and geofencing for every connected battery",
      "Usage pattern analysis — charge cycles, depth of discharge, temperature",
      "Anomaly detection for misuse, tampering, or rapid degradation",
      "Over-the-air firmware updates for connected BMS modules",
    ],
    keyBenefit:
      "For the first time, lenders can see the exact health and value of battery collateral in real-time — not just at origination.",
    color: "brand" as const,
    iconBg: "bg-brand-100",
    iconText: "text-brand-600",
  },
  {
    icon: ShieldCheck,
    title: "Intelligent Risk Evaluation Engine",
    description:
      "Proprietary scoring model that combines traditional credit data with telemetry and behavioral signals to make faster, smarter underwriting decisions.",
    features: [
      "Behavioral risk scoring using charge patterns and usage frequency",
      "API-first integration — plugs directly into your existing LMS",
      "Alternative data enrichment: telemetry + GPS + usage + bureau",
      "Real-time portfolio risk monitoring with automated alerts",
      "Predictive default signals 30+ days before missed payments",
    ],
    keyBenefit:
      "Reduce NPAs from 8-12% to under 2% with data-driven underwriting that sees what traditional credit scoring cannot.",
    color: "green" as const,
    iconBg: "bg-green-100",
    iconText: "text-green-600",
  },
  {
    icon: Recycle,
    title: "Lifecycle Asset Management",
    description:
      "End-to-end battery lifecycle management from origination through second-life and responsible recycling, ensuring maximum asset value recovery.",
    features: [
      "Remote immobilisation — disable charging on default without physical recovery",
      "Automated second-life routing for batteries below financing threshold",
      "Certified recycler network integration with chain-of-custody tracking",
      "EPR (Extended Producer Responsibility) compliance reporting",
      "Battery passport data for resale and residual value certification",
    ],
    keyBenefit:
      "Every battery retains recoverable value throughout its lifecycle — whether through continued financing, second-life applications, or recycling credits.",
    color: "pink" as const,
    iconBg: "bg-pink-100",
    iconText: "text-pink-600",
  },
];

export default function SolutionsPillarsSection() {
  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="Three Pillars"
          title="Full-Stack Battery Intelligence"
          subtitle="Each pillar is powerful alone. Together, they create an unassailable data moat."
        />

        {/* Alternating pillar sections */}
        <div className="mt-16 space-y-20">
          {pillars.map((pillar, i) => (
            <div
              key={pillar.title}
              className={`flex flex-col ${
                i % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"
              } gap-10 items-center`}
            >
              {/* Text side */}
              <div className="flex-1">
                <FadeInOnScroll direction={i % 2 === 0 ? "left" : "right"}>
                  <div className="flex items-center gap-3 mb-4">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-xl ${pillar.iconBg}`}
                    >
                      <pillar.icon className={`h-5 w-5 ${pillar.iconText}`} />
                    </div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                      Pillar {i + 1}
                    </span>
                  </div>
                  <h3 className="text-2xl md:text-3xl font-bold text-gray-900">
                    {pillar.title}
                  </h3>
                  <p className="mt-3 text-base text-gray-600 leading-relaxed">
                    {pillar.description}
                  </p>
                </FadeInOnScroll>
              </div>

              {/* Card side */}
              <div className="flex-1 w-full">
                <FadeInOnScroll
                  direction={i % 2 === 0 ? "right" : "left"}
                  delay={0.15}
                >
                  <PillarCard {...pillar} />
                </FadeInOnScroll>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
