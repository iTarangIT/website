"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { cn } from "@/lib/utils";
import SectionHeading from "@/components/shared/SectionHeading";
import { Users, Activity, Building2, LineChart, RefreshCcw, ArrowRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface WorkflowStep {
  step: number;
  title: string;
  description: string;
  icon: LucideIcon;
}

const steps: WorkflowStep[] = [
  {
    step: 1,
    title: "Driver & Dealer",
    description: "Origination at POS",
    icon: Users,
  },
  {
    step: 2,
    title: "iTarang Platform",
    description: "Telemetry + Risk Score",
    icon: Activity,
  },
  {
    step: 3,
    title: "NBFC Partner",
    description: "Decision & Disbursement",
    icon: Building2,
  },
  {
    step: 4,
    title: "Monitoring",
    description: "Health & Repayment",
    icon: LineChart,
  },
  {
    step: 5,
    title: "Lifecycle Ops",
    description: "Recovery & Second Life",
    icon: RefreshCcw,
  },
];

export default function WorkflowSteps() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.2 });

  return (
    <section className="py-16 md:py-24 bg-white">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="How it works"
          title="End-to-End Battery Financing Workflow"
          subtitle="From origination to lifecycle management — a fully integrated pipeline."
        />

        <div ref={ref} className="mt-12">
          {/* Desktop: horizontal */}
          <div className="hidden md:flex items-start justify-between gap-2">
            {steps.map((s, i) => (
              <div key={s.step} className="flex items-start flex-1">
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={inView ? { opacity: 1, y: 0 } : {}}
                  transition={{ duration: 0.5, delay: i * 0.15 }}
                  className="flex flex-col items-center text-center flex-1"
                >
                  {/* Numbered circle with icon */}
                  <div
                    className={cn(
                      "relative flex h-16 w-16 items-center justify-center rounded-full border-2 transition-all duration-500",
                      inView
                        ? "border-brand-500 bg-brand-50"
                        : "border-gray-200 bg-gray-50"
                    )}
                  >
                    <s.icon
                      className={cn(
                        "h-6 w-6 transition-colors duration-500",
                        inView ? "text-brand-600" : "text-gray-400"
                      )}
                    />
                    <span className="absolute -top-2 -right-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-xs font-bold text-white">
                      {s.step}
                    </span>
                  </div>

                  <h4 className="mt-4 text-sm font-semibold text-gray-900">
                    {s.title}
                  </h4>
                  <p className="mt-1 text-xs text-gray-500 max-w-[140px]">
                    {s.description}
                  </p>
                </motion.div>

                {/* Arrow connector */}
                {i < steps.length - 1 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={inView ? { opacity: 1 } : {}}
                    transition={{ duration: 0.4, delay: i * 0.15 + 0.1 }}
                    className="flex items-center pt-7 px-1"
                  >
                    <ArrowRight className="h-5 w-5 text-brand-300" />
                  </motion.div>
                )}
              </div>
            ))}
          </div>

          {/* Mobile: vertical */}
          <div className="md:hidden space-y-6">
            {steps.map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, x: -20 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.5, delay: i * 0.12 }}
                className="flex items-start gap-4"
              >
                <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-brand-500 bg-brand-50">
                  <s.icon className="h-5 w-5 text-brand-600" />
                  <span className="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
                    {s.step}
                  </span>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-gray-900">
                    {s.title}
                  </h4>
                  <p className="text-xs text-gray-500">{s.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
