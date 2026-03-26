"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import SectionHeading from "@/components/shared/SectionHeading";
import { Shield, Check, Code, FileSliders, Landmark } from "lucide-react";

const positioningPoints = [
  {
    icon: Code,
    title: "Technology Service Provider (not a lender)",
    description:
      "We provide the rails — telemetry, scoring, lifecycle management. We never originate loans or take credit risk on our balance sheet.",
  },
  {
    icon: FileSliders,
    title: "API-first Integration for Existing LMS",
    description:
      "Drop-in APIs that plug into your existing Loan Management System. No rip-and-replace — start with underwriting data, expand to monitoring.",
  },
  {
    icon: Landmark,
    title: "No Balance Sheet Risk or NBFC Licensing Needed",
    description:
      "iTarang operates as a pure-play technology partner. We earn SaaS fees and risk scoring fees — aligned incentives, zero regulatory overlap.",
  },
];

export default function CompetitivePosition() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.15 });

  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="Our Position"
          title="We Enable NBFCs, We Don't Compete"
          subtitle="iTarang is a Technology Service Provider — we power your lending, not replace it."
        />

        <div ref={ref} className="mt-12 grid grid-cols-1 lg:grid-cols-5 gap-10 items-center">
          {/* Shield visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={inView ? { opacity: 1, scale: 1 } : {}}
            transition={{ duration: 0.6 }}
            className="lg:col-span-2 flex justify-center"
          >
            <div className="relative">
              <div className="flex h-40 w-40 items-center justify-center rounded-full bg-brand-50 border-2 border-brand-100">
                <Shield className="h-20 w-20 text-brand-500" />
              </div>
              {/* Floating checkmarks */}
              {[
                { top: "0%", right: "0%", delay: 0.3 },
                { top: "60%", right: "-10%", delay: 0.5 },
                { top: "10%", left: "-5%", delay: 0.7 },
              ].map((pos, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={inView ? { opacity: 1, scale: 1 } : {}}
                  transition={{ delay: pos.delay, type: "spring" }}
                  className="absolute flex h-8 w-8 items-center justify-center rounded-full bg-accent-green text-white shadow-lg"
                  style={{
                    top: pos.top,
                    right: pos.right,
                    left: (pos as { left?: string }).left,
                  }}
                >
                  <Check className="h-4 w-4" />
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Points */}
          <div className="lg:col-span-3 space-y-6">
            {positioningPoints.map((point, i) => (
              <motion.div
                key={point.title}
                initial={{ opacity: 0, x: 30 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.2 + i * 0.12 }}
                className="flex gap-4 rounded-xl border border-gray-100 bg-white p-5 shadow-sm hover:shadow-md transition-shadow"
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-brand-50">
                  <point.icon className="h-5 w-5 text-brand-600" />
                </div>
                <div>
                  <h4 className="text-base font-semibold text-gray-900">
                    {point.title}
                  </h4>
                  <p className="mt-1 text-sm text-gray-600 leading-relaxed">
                    {point.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
