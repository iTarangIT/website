"use client";

import { motion } from "framer-motion";
import {
  Target,
  Building2,
  MapPin,
  Banknote,
  ShieldCheck,
  Rocket,
} from "lucide-react";
import { deckMetrics } from "@/data/metrics";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import Badge from "@/components/ui/Badge";
import { staggerContainer, staggerItem } from "@/lib/animations";

const allocationItems = [
  deckMetrics.allocation.techMVP,
  deckMetrics.allocation.team,
  deckMetrics.allocation.workingCapital,
  deckMetrics.allocation.gtm,
  deckMetrics.allocation.regulatory,
];

const allocationColors = [
  "from-brand-500 to-brand-600",
  "from-accent-sky to-brand-500",
  "from-brand-400 to-brand-500",
  "from-accent-green to-brand-500",
  "from-brand-300 to-brand-400",
];

const milestones = [
  {
    icon: Target,
    metric: deckMetrics.targetBUM,
    label: "Batteries Under Management",
  },
  {
    icon: Building2,
    metric: `${deckMetrics.targetNBFCIntegrations}`,
    label: "NBFC Integrations Live",
  },
  {
    icon: MapPin,
    metric: `${deckMetrics.targetCitiesLive}`,
    label: "Cities Operational",
  },
  {
    icon: Banknote,
    metric: deckMetrics.targetAUMFacilitated,
    label: "AUM Facilitated",
  },
  {
    icon: ShieldCheck,
    metric: deckMetrics.targetNPA,
    label: "NPA Rate",
  },
];

export default function TheAskSection() {
  return (
    <section className="py-20 md:py-28 bg-brand-900 text-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="The Ask"
            title="Raising to Build, Not to Burn"
            subtitle="A capital-efficient raise designed to hit Series Seed readiness in 12 months."
            dark
          />
        </FadeInOnScroll>

        {/* Headline amount */}
        <FadeInOnScroll>
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-3 rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 px-8 py-5">
              <p className="text-4xl md:text-5xl lg:text-6xl font-bold text-white">
                {deckMetrics.raiseAmount}
              </p>
              <div className="text-left">
                <Badge className="bg-accent-yellow text-gray-900 font-bold">
                  {deckMetrics.raiseType}
                </Badge>
              </div>
            </div>
          </div>
        </FadeInOnScroll>

        {/* Use of Funds */}
        <FadeInOnScroll>
          <div className="rounded-2xl bg-white/5 border border-white/10 p-8 md:p-10 mb-16">
            <h3 className="text-lg font-bold text-white mb-1">
              Use of Funds
            </h3>
            <p className="text-sm text-brand-200 mb-8">
              Capital allocation across 5 focus areas for 12-month runway
            </p>

            <motion.div
              variants={staggerContainer}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true, amount: 0.3 }}
              className="space-y-6"
            >
              {allocationItems.map((item, i) => (
                <motion.div
                  key={item.label}
                  variants={staggerItem}
                  transition={{ duration: 0.4 }}
                >
                  <div className="flex items-baseline justify-between mb-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-white">
                        {item.label}
                      </span>
                      <span className="text-xs text-brand-300">
                        {item.amount}
                      </span>
                    </div>
                    <span className="text-sm font-bold text-white">
                      {item.percent}%
                    </span>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-4">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: `${item.percent}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 1, ease: "easeOut", delay: i * 0.1 }}
                      className={`h-4 rounded-full bg-gradient-to-r ${allocationColors[i]}`}
                    />
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </FadeInOnScroll>

        {/* 12-Month Milestones */}
        <FadeInOnScroll>
          <div className="mb-12">
            <h3 className="text-lg font-bold text-white mb-1 text-center">
              12-Month Milestones
            </h3>
            <p className="text-sm text-brand-200 mb-8 text-center">
              Clear, measurable targets that de-risk the next raise
            </p>

            <motion.div
              variants={staggerContainer}
              initial="initial"
              whileInView="animate"
              viewport={{ once: true, amount: 0.2 }}
              className="grid grid-cols-2 md:grid-cols-5 gap-4"
            >
              {milestones.map((milestone) => {
                const Icon = milestone.icon;
                return (
                  <motion.div
                    key={milestone.label}
                    variants={staggerItem}
                    transition={{ duration: 0.5 }}
                    className="rounded-xl bg-white/5 border border-white/10 p-5 text-center hover:bg-white/10 transition-colors"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 mx-auto mb-3">
                      <Icon className="h-5 w-5 text-brand-300" />
                    </div>
                    <p className="text-2xl md:text-3xl font-bold text-white mb-1">
                      {milestone.metric}
                    </p>
                    <p className="text-xs text-brand-300 leading-tight">
                      {milestone.label}
                    </p>
                  </motion.div>
                );
              })}
            </motion.div>
          </div>
        </FadeInOnScroll>

        {/* Outcome Highlight */}
        <FadeInOnScroll delay={0.2}>
          <div className="rounded-2xl bg-gradient-to-r from-accent-green/20 to-brand-500/20 border border-accent-green/30 p-8 text-center">
            <div className="flex items-center justify-center gap-3 mb-3">
              <Rocket className="h-6 w-6 text-accent-green" />
              <h3 className="text-xl md:text-2xl font-bold text-white">
                Outcome: Series Seed Ready
              </h3>
            </div>
            <p className="text-brand-200 max-w-2xl mx-auto text-sm md:text-base leading-relaxed">
              With {deckMetrics.targetBUM} BUM, {deckMetrics.targetNBFCIntegrations} live
              NBFC integrations, {deckMetrics.targetCitiesLive} cities operational, and{" "}
              {deckMetrics.targetNPA} NPA rate, iTarang will be positioned for a
              strong Series Seed raise with demonstrated unit economics and
              product-market fit.
            </p>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
