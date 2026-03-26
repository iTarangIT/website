"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { cn } from "@/lib/utils";
import { TrendingUp, ExternalLink } from "lucide-react";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import AnimatedCounter from "@/components/shared/AnimatedCounter";

interface MetricCard {
  value: number;
  prefix?: string;
  suffix?: string;
  label: string;
}

const metricCards: MetricCard[] = [
  { value: 2, label: "NBFC LOIs In Pipeline" },
  { value: 20, suffix: "+", label: "Active Dealers Onboarded" },
  { value: 150, prefix: "~", label: "Units Live Monitoring" },
  { value: 98, suffix: "%", label: "Recovery Rate (Early Data)" },
];

interface ProgressItem {
  label: string;
  percent: number;
}

const techReadiness: ProgressItem[] = [
  { label: "Telemetry Module", percent: 95 },
  { label: "Dealer Portal", percent: 90 },
  { label: "Loan Processing", percent: 85 },
  { label: "Risk Engine v1", percent: 80 },
];

function ProgressBar({ label, percent }: ProgressItem) {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.3 });

  return (
    <div ref={ref} className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm font-semibold text-brand-600">{percent}%</span>
      </div>
      <div className="h-2.5 rounded-full bg-gray-100 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={inView ? { width: `${percent}%` } : { width: 0 }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-brand-400"
        />
      </div>
    </div>
  );
}

export default function TractionSection() {
  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Traction"
            title="Early Execution Signals"
          />
        </FadeInOnScroll>

        {/* Metric cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {metricCards.map((metric, i) => (
            <FadeInOnScroll key={metric.label} delay={i * 0.1}>
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 hover:shadow-md transition-shadow text-brand-600">
                <AnimatedCounter
                  value={metric.value}
                  prefix={metric.prefix || ""}
                  suffix={metric.suffix || ""}
                  label={metric.label}
                />
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          {/* MVP Tech Readiness */}
          <FadeInOnScroll>
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
              <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-brand-500" />
                MVP Tech Readiness
              </h3>
              <div className="space-y-5">
                {techReadiness.map((item) => (
                  <ProgressBar key={item.label} {...item} />
                ))}
              </div>
            </div>
          </FadeInOnScroll>

          {/* Category Validation */}
          <FadeInOnScroll delay={0.15}>
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 flex flex-col">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <ExternalLink className="h-5 w-5 text-brand-500" />
                Category Validation
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                The EV battery financing market has been proven by early movers.
                iTarang brings the intelligence layer that makes it scalable.
              </p>

              <div
                className={cn(
                  "rounded-xl bg-gradient-to-br from-brand-50 to-brand-100/50 border border-brand-200/50 p-6 flex-1"
                )}
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="inline-flex items-center rounded-full bg-brand-500 px-3 py-1 text-xs font-semibold text-white">
                    Benchmark
                  </span>
                  <span className="text-sm font-semibold text-brand-700">
                    Chargeup (Category Leader)
                  </span>
                </div>
                <ul className="space-y-2">
                  {[
                    "₹20 Cr ARR achieved",
                    "7,000+ drivers on platform",
                    "EBITDA positive operations",
                  ].map((item, i) => (
                    <li
                      key={i}
                      className="flex items-center gap-2 text-sm text-brand-700"
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-accent-green" />
                      {item}
                    </li>
                  ))}
                </ul>
                <p className="mt-4 text-xs text-brand-600 italic">
                  iTarang differentiates with deep battery intelligence and
                  NBFC-grade risk infrastructure that category leaders lack.
                </p>
              </div>
            </div>
          </FadeInOnScroll>
        </div>
      </div>
    </section>
  );
}
