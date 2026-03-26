"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";
import { unitEconomicsBreakdown } from "@/data/revenue-streams";
import { cn } from "@/lib/utils";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { staggerContainer, staggerItem } from "@/lib/animations";

// Maximum value for bar scaling
const MAX_BAR_VALUE = 5000;

function BarSegment({ amount, maxVal }: { amount: number; maxVal: number }) {
  const widthPercent = Math.min((amount / maxVal) * 100, 100);
  return (
    <motion.div
      initial={{ width: 0 }}
      whileInView={{ width: `${widthPercent}%` }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="h-3 rounded-full bg-gradient-to-r from-brand-400 to-brand-600"
    />
  );
}

function CostBar({ amount, maxVal }: { amount: number; maxVal: number }) {
  const widthPercent = Math.min((amount / maxVal) * 100, 100);
  return (
    <motion.div
      initial={{ width: 0 }}
      whileInView={{ width: `${widthPercent}%` }}
      viewport={{ once: true }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="h-3 rounded-full bg-gradient-to-r from-red-300 to-red-500"
    />
  );
}

export default function UnitEconomicsCard() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Unit Economics"
            title="Built for Margin, Not Just Growth"
            subtitle="Per-battery economics that deliver 65-70% gross margins with compounding LTV over the battery lifecycle."
          />
        </FadeInOnScroll>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Revenue side */}
          <FadeInOnScroll direction="left">
            <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8">
              <div className="flex items-center gap-2 mb-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-50">
                  <TrendingUp className="h-5 w-5 text-accent-green" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Revenue per Battery</h3>
                  <p className="text-sm text-gray-500">
                    LTV: {unitEconomicsBreakdown.totalLTV}
                  </p>
                </div>
              </div>

              <motion.div
                variants={staggerContainer}
                initial="initial"
                whileInView="animate"
                viewport={{ once: true, amount: 0.3 }}
                className="space-y-5"
              >
                {unitEconomicsBreakdown.revenue.map((item) => {
                  const displayAmount =
                    typeof item.amount === "number"
                      ? `₹${item.amount.toLocaleString("en-IN")}`
                      : (item as { amountRange?: string }).amountRange || "";
                  const barAmount =
                    typeof item.amount === "number" ? item.amount : 6000; // midpoint for range items

                  return (
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
                          {displayAmount}
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-3">
                        <BarSegment amount={barAmount} maxVal={MAX_BAR_VALUE} />
                      </div>
                      <p className="mt-1 text-xs text-gray-400">{item.note}</p>
                    </motion.div>
                  );
                })}
              </motion.div>
            </div>
          </FadeInOnScroll>

          {/* Cost side */}
          <FadeInOnScroll direction="right">
            <div className="rounded-2xl border border-gray-100 bg-white shadow-sm p-8">
              <div className="flex items-center gap-2 mb-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-50">
                  <TrendingDown className="h-5 w-5 text-red-500" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">Cost per Battery</h3>
                  <p className="text-sm text-gray-500">
                    CAC + COGS: {unitEconomicsBreakdown.totalCACCOGS}
                  </p>
                </div>
              </div>

              <motion.div
                variants={staggerContainer}
                initial="initial"
                whileInView="animate"
                viewport={{ once: true, amount: 0.3 }}
                className="space-y-5"
              >
                {unitEconomicsBreakdown.costs.map((item) => (
                  <motion.div
                    key={item.label}
                    variants={staggerItem}
                    transition={{ duration: 0.4 }}
                  >
                    <div className="flex items-baseline justify-between mb-1.5">
                      <p className="text-sm font-medium text-gray-700">
                        {item.label}
                      </p>
                      <span className="text-sm font-bold text-red-600">
                        ₹{item.amount.toLocaleString("en-IN")}
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-3">
                      <CostBar amount={item.amount} maxVal={MAX_BAR_VALUE} />
                    </div>
                    <p className="mt-1 text-xs text-gray-400">{item.note}</p>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </FadeInOnScroll>
        </div>

        {/* Gross Margin Highlight */}
        <FadeInOnScroll delay={0.3}>
          <div className="mt-10 rounded-2xl bg-gradient-to-r from-brand-500 to-brand-700 p-8 md:p-10 text-center shadow-lg">
            <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-12">
              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-white/70 mb-1">
                  Per-Battery LTV
                </p>
                <p className="text-2xl md:text-3xl font-bold text-white">
                  {unitEconomicsBreakdown.totalLTV}
                </p>
              </div>

              <div className="hidden md:block text-3xl font-light text-white/40">
                vs
              </div>
              <div className="md:hidden text-lg font-light text-white/40">
                vs
              </div>

              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-white/70 mb-1">
                  CAC + COGS
                </p>
                <p className="text-2xl md:text-3xl font-bold text-white">
                  {unitEconomicsBreakdown.totalCACCOGS}
                </p>
              </div>

              <div
                className={cn(
                  "hidden md:block h-16 w-px bg-white/20"
                )}
              />

              <div>
                <p className="text-sm font-semibold uppercase tracking-wider text-white/70 mb-1">
                  Gross Margin
                </p>
                <p className="text-4xl md:text-5xl font-bold text-accent-yellow">
                  {unitEconomicsBreakdown.grossMargin}
                </p>
              </div>
            </div>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
