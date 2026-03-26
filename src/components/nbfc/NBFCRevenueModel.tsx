"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import SectionHeading from "@/components/shared/SectionHeading";
import { deckMetrics } from "@/data/metrics";
import { cn } from "@/lib/utils";
import { TrendingDown, TrendingUp, ArrowRight } from "lucide-react";

interface ComparisonRow {
  metric: string;
  before: string;
  after: string;
  improved: boolean;
}

const comparisonData: ComparisonRow[] = [
  { metric: "NPA Rate", before: "8–12%", after: "<2%", improved: true },
  { metric: "Recovery Mechanism", before: "None", after: "Remote Immobilisation + GPS", improved: true },
  { metric: "SOH Visibility", before: "0%", after: "100% Real-time", improved: true },
  { metric: "Underwriting Data", before: "Credit bureau only", after: "Bureau + Telemetry + Behavioral", improved: true },
  { metric: "Collection Cost", before: "High (field agents)", after: "60% lower (automated)", improved: true },
  { metric: "Portfolio Risk-Adjusted Return", before: "Baseline", after: "30–40% improvement", improved: true },
];

export default function NBFCRevenueModel() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.15 });

  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="Unit Economics"
          title="The Risk-Adjusted Return Case"
          subtitle={`Battery loan of ₹${deckMetrics.typicalBatteryLoanAmount.toLocaleString("en-IN")} @ ${deckMetrics.typicalInterestRate}% p.a. for ${deckMetrics.typicalTenureMonths} months`}
        />

        <div ref={ref} className="mt-12">
          {/* Comparison table */}
          <div className="rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
            {/* Header */}
            <div className="grid grid-cols-3 bg-gray-50 border-b border-gray-100">
              <div className="px-6 py-4 text-sm font-semibold text-gray-600">
                Metric
              </div>
              <div className="px-6 py-4 text-sm font-semibold text-accent-pink text-center flex items-center justify-center gap-1.5">
                <TrendingDown className="h-4 w-4" />
                Before iTarang
              </div>
              <div className="px-6 py-4 text-sm font-semibold text-accent-green text-center flex items-center justify-center gap-1.5">
                <TrendingUp className="h-4 w-4" />
                After iTarang
              </div>
            </div>

            {/* Rows */}
            {comparisonData.map((row, i) => (
              <motion.div
                key={row.metric}
                initial={{ opacity: 0, x: -20 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className={cn(
                  "grid grid-cols-3 border-b border-gray-50 last:border-b-0",
                  i % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                )}
              >
                <div className="px-6 py-4 text-sm font-medium text-gray-900">
                  {row.metric}
                </div>
                <div className="px-6 py-4 text-sm text-gray-500 text-center">
                  {row.before}
                </div>
                <div className="px-6 py-4 text-sm font-semibold text-accent-green text-center">
                  {row.after}
                </div>
              </motion.div>
            ))}
          </div>

          {/* Bottom callout */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 0.6 }}
            className="mt-8 rounded-2xl bg-gradient-to-r from-brand-500 to-brand-700 p-8 text-center"
          >
            <p className="text-lg text-white/80">iTarang improves risk-adjusted returns by</p>
            <p className="mt-2 text-4xl md:text-5xl font-bold text-white">
              {deckMetrics.riskAdjustedReturnImprovement}
            </p>
            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-brand-200">
              <span>Lower NPAs</span>
              <ArrowRight className="h-4 w-4" />
              <span>Better Recovery</span>
              <ArrowRight className="h-4 w-4" />
              <span>Higher Portfolio Yield</span>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
