"use client";

import { motion } from "framer-motion";
import { Radio, Brain, RefreshCw, CheckCircle } from "lucide-react";
import Badge from "@/components/ui/Badge";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { staggerContainer, staggerItem } from "@/lib/animations";

interface Pillar {
  icon: React.ElementType;
  pillarNumber: number;
  title: string;
  subtitle: string;
  features: string[];
  benefitBadge: string;
  badgeVariant: "default" | "success" | "accent";
}

const pillars: Pillar[] = [
  {
    icon: Radio,
    pillarNumber: 1,
    title: "Smart Battery Telemetry",
    subtitle: "Real-time intelligence on every battery in the field",
    features: [
      "IoT-enabled State of Health (SOH) and State of Charge (SOC) monitoring",
      "Usage pattern analytics: charge cycles, depth of discharge, temperature",
      "GPS tracking for asset location and geo-fencing",
      "Tamper detection and anomaly alerts",
      "OTA firmware updates for continuous improvement",
    ],
    benefitBadge: "Turns Opaque Assets into Transparent Collateral",
    badgeVariant: "default",
  },
  {
    icon: Brain,
    pillarNumber: 2,
    title: "Intelligent Risk Evaluation Engine",
    subtitle: "Behavioral scoring that makes thin-file drivers bankable",
    features: [
      "Proprietary battery behavioral scoring (replacement for CIBIL in EV)",
      "Multi-signal risk model: telemetry + usage + repayment behavior",
      "API-first integration with NBFC loan management systems",
      "Dynamic risk re-scoring as battery health evolves",
      "Financial inclusion: enables formal credit for 90%+ underserved drivers",
    ],
    benefitBadge: "30-40% Better Risk-Adjusted Returns for NBFCs",
    badgeVariant: "success",
  },
  {
    icon: RefreshCw,
    pillarNumber: 3,
    title: "Lifecycle Asset Management",
    subtitle: "End-to-end value capture from origination to recycling",
    features: [
      "Remote control: lock/unlock for collections and theft deterrence",
      "Second-life assessment and marketplace for retired batteries",
      "BWMR 2022 compliance tracking and EPR documentation",
      "Recycling partner network and chain-of-custody records",
      "Residual value optimization at every lifecycle stage",
    ],
    benefitBadge: "Regulatory Moat + Recurring Revenue Stream",
    badgeVariant: "accent",
  },
];

export default function SolutionPillars() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Our Solution"
            title="Three Pillars of Battery Intelligence"
            subtitle="iTarang is the intelligence layer that connects telemetry, credit, and lifecycle management into one programmable platform."
          />
        </FadeInOnScroll>

        <motion.div
          variants={staggerContainer}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.1 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-8"
        >
          {pillars.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <motion.div
                key={pillar.title}
                variants={staggerItem}
                transition={{ duration: 0.5 }}
                className="relative flex flex-col h-full rounded-2xl border border-gray-100 bg-white shadow-sm hover:shadow-lg transition-shadow duration-300 overflow-hidden"
              >
                {/* Top gradient bar */}
                <div className="h-1.5 w-full bg-gradient-to-r from-brand-500 to-accent-sky" />

                <div className="p-8 flex flex-col flex-1">
                  {/* Pillar number + icon */}
                  <div className="flex items-center gap-4 mb-5">
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50">
                      <Icon className="h-7 w-7 text-brand-500" />
                    </div>
                    <span className="text-xs font-bold uppercase tracking-widest text-brand-400">
                      Pillar {pillar.pillarNumber}
                    </span>
                  </div>

                  {/* Title + subtitle */}
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {pillar.title}
                  </h3>
                  <p className="text-sm text-gray-500 mb-6">
                    {pillar.subtitle}
                  </p>

                  {/* Features */}
                  <ul className="space-y-3 flex-1 mb-6">
                    {pillar.features.map((feature, j) => (
                      <li
                        key={j}
                        className="flex items-start gap-2.5 text-sm text-gray-600"
                      >
                        <CheckCircle className="h-4 w-4 text-accent-green shrink-0 mt-0.5" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {/* Key benefit badge */}
                  <div className="mt-auto pt-4 border-t border-gray-100">
                    <Badge variant={pillar.badgeVariant}>
                      {pillar.benefitBadge}
                    </Badge>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
