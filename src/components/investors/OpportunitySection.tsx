"use client";

import { motion } from "framer-motion";
import { TrendingUp, Percent, IndianRupee, ShieldCheck } from "lucide-react";
import { deckMetrics } from "@/data/metrics";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { staggerContainer, staggerItem } from "@/lib/animations";

const opportunities = [
  {
    icon: TrendingUp,
    number: deckMetrics.newEV3WheelersByFY27,
    label: "New EVs by FY'27",
    description:
      "India's 3-wheeler EV fleet is set to surge, creating massive demand for battery financing and lifecycle management.",
    gradient: "from-brand-500 to-brand-700",
  },
  {
    icon: Percent,
    number: `~${deckMetrics.informalFinancingPercent}%`,
    label: "Informal Financing",
    description:
      "The vast majority of EV battery purchases are financed through informal channels at 30-60% interest rates.",
    gradient: "from-accent-pink to-brand-600",
  },
  {
    icon: IndianRupee,
    number: deckMetrics.annualReplacementTAM,
    label: "Annual Replacement TAM",
    description:
      "With 2-3 year replacement cycles and 30 Lakh+ installed base, the addressable market is enormous and recurring.",
    gradient: "from-brand-600 to-accent-pink",
  },
  {
    icon: ShieldCheck,
    number: "Mandatory",
    label: "Battery Waste Management Rules",
    description:
      "India's regulatory framework now mandates lifecycle tracking and EPR compliance — creating a structural moat for compliant platforms.",
    gradient: "from-accent-green to-brand-600",
  },
];

export default function OpportunitySection() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Market Opportunity"
            title="A Category-Defining Moment"
            subtitle="Four converging forces are creating an unprecedented window for an intelligence layer in India's EV battery economy."
          />
        </FadeInOnScroll>

        <motion.div
          variants={staggerContainer}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.2 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
        >
          {opportunities.map((item) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.label}
                variants={staggerItem}
                transition={{ duration: 0.5 }}
                className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${item.gradient} p-8 text-white shadow-lg hover:shadow-xl transition-shadow duration-300`}
              >
                {/* Decorative circle */}
                <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-white/10" />

                <div className="relative">
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 mb-5">
                    <Icon className="h-6 w-6 text-white" />
                  </div>

                  <p className="text-3xl sm:text-4xl font-bold tracking-tight mb-1">
                    {item.number}
                  </p>
                  <p className="text-sm font-semibold uppercase tracking-wider text-white/80 mb-4">
                    {item.label}
                  </p>

                  <p className="text-sm leading-relaxed text-white/75">
                    {item.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
