"use client";

import { motion } from "framer-motion";
import { FileText, Users, Cpu, ShieldCheck, ExternalLink } from "lucide-react";
import { deckMetrics } from "@/data/metrics";
import AnimatedCounter from "@/components/shared/AnimatedCounter";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import Badge from "@/components/ui/Badge";
import { staggerContainer, staggerItem } from "@/lib/animations";

const tractionItems = [
  {
    icon: FileText,
    value: deckMetrics.nbfcLOIs,
    suffix: "",
    prefix: "",
    label: "NBFC LOIs in Pipeline",
  },
  {
    icon: Users,
    value: deckMetrics.dealersOnboarded,
    suffix: "+",
    prefix: "",
    label: "Dealers Onboarded",
  },
  {
    icon: Cpu,
    value: deckMetrics.pilotBatteries,
    suffix: "+",
    prefix: "~",
    label: "Pilot Units Live",
  },
  {
    icon: ShieldCheck,
    value: deckMetrics.recoveryRate,
    suffix: "%",
    prefix: "",
    label: "Recovery Rate",
  },
];

interface TechReadinessItem {
  label: string;
  percent: number;
}

const techReadiness: TechReadinessItem[] = [
  { label: "IoT Hardware (BMS Integration)", percent: 85 },
  { label: "Telemetry Cloud Platform", percent: 75 },
  { label: "Risk Scoring Engine v1", percent: 60 },
  { label: "NBFC API Integration Layer", percent: 50 },
  { label: "Dealer Onboarding Portal", percent: 70 },
];

const categoryValidation = [
  {
    company: "Chargeup",
    details: "₹20 Cr ARR, 7,000+ drivers, EBITDA positive",
    relevance: "Validates driver demand and fleet-scale operations in EV 3-wheelers",
  },
  {
    company: "Mufin Green Finance",
    details: "Specialized green NBFC, growing EV portfolio",
    relevance: "Validates NBFC appetite for EV battery lending when risk is managed",
  },
];

export default function TractionMetrics() {
  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Traction & Validation"
            title="Early Proof Points, Real Signal"
            subtitle="Pre-revenue traction that demonstrates product-market pull from both supply (NBFCs) and demand (dealers/drivers)."
          />
        </FadeInOnScroll>

        {/* Main Metrics */}
        <FadeInOnScroll>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
            {tractionItems.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.label}
                  className="rounded-2xl border border-gray-100 bg-white shadow-sm p-6 text-center hover:shadow-md transition-shadow"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 mx-auto mb-4">
                    <Icon className="h-6 w-6 text-brand-500" />
                  </div>
                  <AnimatedCounter
                    value={item.value}
                    prefix={item.prefix}
                    suffix={item.suffix}
                    label={item.label}
                  />
                </div>
              );
            })}
          </div>
        </FadeInOnScroll>

        {/* Tech Readiness */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <FadeInOnScroll direction="left">
            <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8">
              <h3 className="text-lg font-bold text-gray-900 mb-1">
                Tech Readiness
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Platform development progress across key modules
              </p>

              <motion.div
                variants={staggerContainer}
                initial="initial"
                whileInView="animate"
                viewport={{ once: true, amount: 0.3 }}
                className="space-y-5"
              >
                {techReadiness.map((item) => (
                  <motion.div
                    key={item.label}
                    variants={staggerItem}
                    transition={{ duration: 0.4 }}
                  >
                    <div className="flex items-baseline justify-between mb-1.5">
                      <p className="text-sm font-medium text-gray-700">
                        {item.label}
                      </p>
                      <span className="text-sm font-bold text-brand-600">
                        {item.percent}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2.5">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${item.percent}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 1, ease: "easeOut" }}
                        className="h-2.5 rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
                      />
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </FadeInOnScroll>

          {/* Category Validation */}
          <FadeInOnScroll direction="right">
            <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8">
              <h3 className="text-lg font-bold text-gray-900 mb-1">
                Category Validation
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Market proof that this category is investable and scalable
              </p>

              <div className="space-y-6">
                {categoryValidation.map((item) => (
                  <div
                    key={item.company}
                    className="rounded-xl bg-gray-50 border border-gray-100 p-5"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-gray-900">
                        {item.company}
                      </h4>
                      <ExternalLink className="h-3.5 w-3.5 text-gray-400" />
                    </div>
                    <Badge variant="success" className="mb-3">
                      {item.details}
                    </Badge>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {item.relevance}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 rounded-lg bg-brand-50 border border-brand-100">
                <p className="text-sm text-brand-700 font-medium">
                  iTarang sits at the intersection of these validations — providing
                  the missing intelligence layer that makes battery lending
                  scalable, compliant, and profitable.
                </p>
              </div>
            </div>
          </FadeInOnScroll>
        </div>
      </div>
    </section>
  );
}
