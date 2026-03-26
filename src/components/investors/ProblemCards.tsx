"use client";

import { motion } from "framer-motion";
import { EyeOff, Lock, Recycle } from "lucide-react";
import { cn } from "@/lib/utils";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { staggerContainer, staggerItem } from "@/lib/animations";

interface InvestorProblemCard {
  icon: React.ElementType;
  title: string;
  points: string[];
  consequence: string;
  investorImpact: string;
}

const problems: InvestorProblemCard[] = [
  {
    icon: EyeOff,
    title: "Lenders Fly Blind",
    points: [
      "Zero real-time SOH/SOC data on battery assets",
      "No standardized battery risk scoring framework exists",
      "High risk perception deters institutional capital from EV battery loans",
      "Weak recovery mechanisms drive NPA exposure to 8-12%",
    ],
    consequence: "High NPAs & Reluctance to Lend",
    investorImpact:
      "NBFCs leave billions in lending opportunity on the table, waiting for a trusted underwriting signal.",
  },
  {
    icon: Lock,
    title: "Drivers Locked Out",
    points: [
      "Thin/no credit files for 90%+ of 3-wheeler drivers",
      "Informal financing traps them at 30-60% interest rates",
      "Slow, opaque, paper-heavy approval processes",
      "No formal pathway from informal to institutional credit",
    ],
    consequence: "Financial Exclusion & Predatory Costs",
    investorImpact:
      "A 30 Lakh+ driver base is underserved — the first platform to make them bankable unlocks massive origination volume.",
  },
  {
    icon: Recycle,
    title: "Lifecycle Unmanaged",
    points: [
      "No structured end-of-life pathway for EV batteries",
      "Mandatory BWMR 2022 compliance creates regulatory urgency",
      "Second-life / recycling value worth ₹3,000-8,000 per battery is lost",
      "EPR obligations falling on OEMs with no tracking infrastructure",
    ],
    consequence: "Lost Value & Regulatory Exposure",
    investorImpact:
      "Compliance-ready lifecycle tracking becomes a moat — and a recurring revenue stream from Day 1.",
  },
];

export default function ProblemCards() {
  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="The Problem"
            title="Three Systemic Gaps No One Has Solved"
            subtitle="India's EV battery economy is growing rapidly, but critical infrastructure is missing. This is the gap iTarang fills."
          />
        </FadeInOnScroll>

        <motion.div
          variants={staggerContainer}
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, amount: 0.15 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
        >
          {problems.map((problem) => {
            const Icon = problem.icon;
            return (
              <motion.div
                key={problem.title}
                variants={staggerItem}
                transition={{ duration: 0.5 }}
                className="relative flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 hover:shadow-lg transition-shadow duration-300"
              >
                {/* Icon */}
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 mb-6">
                  <Icon className="h-7 w-7 text-brand-500" />
                </div>

                {/* Title */}
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  {problem.title}
                </h3>

                {/* Points */}
                <ul className="space-y-3 flex-1 mb-6">
                  {problem.points.map((point, j) => (
                    <li
                      key={j}
                      className="flex items-start gap-2 text-sm text-gray-600"
                    >
                      <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-brand-400 shrink-0" />
                      {point}
                    </li>
                  ))}
                </ul>

                {/* Consequence badge */}
                <div className="mb-4">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold",
                      "bg-red-50 text-red-700 border border-red-100"
                    )}
                  >
                    <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                    {problem.consequence}
                  </span>
                </div>

                {/* Investor impact */}
                <div className="mt-auto pt-4 border-t border-gray-100">
                  <p className="text-xs font-semibold uppercase tracking-wider text-brand-600 mb-1">
                    Investor Takeaway
                  </p>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {problem.investorImpact}
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
