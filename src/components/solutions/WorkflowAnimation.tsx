"use client";

import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { cn } from "@/lib/utils";
import SectionHeading from "@/components/shared/SectionHeading";
import {
  Users,
  Activity,
  Building2,
  LineChart,
  RefreshCcw,
  ChevronRight,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface WorkflowStep {
  step: number;
  title: string;
  subtitle: string;
  description: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
}

const steps: WorkflowStep[] = [
  {
    step: 1,
    title: "Driver & Dealer",
    subtitle: "Origination at POS",
    description:
      "Dealer initiates battery financing at point of sale. KYC captured on mobile, battery QR scanned, and loan application submitted in under 5 minutes.",
    icon: Users,
    color: "text-blue-600",
    bgColor: "bg-blue-50",
  },
  {
    step: 2,
    title: "iTarang Platform",
    subtitle: "Telemetry + Risk Score",
    description:
      "IoT module starts streaming SOH, SOC, GPS, and usage data. Our engine generates a composite risk score using telemetry + bureau + behavioral data.",
    icon: Activity,
    color: "text-brand-600",
    bgColor: "bg-brand-50",
  },
  {
    step: 3,
    title: "NBFC Partner",
    subtitle: "Decision & Disbursement",
    description:
      "NBFC receives structured risk report via API. Loan decisioned in real-time using enhanced data. Disbursement to dealer within 24 hours.",
    icon: Building2,
    color: "text-green-600",
    bgColor: "bg-green-50",
  },
  {
    step: 4,
    title: "Monitoring",
    subtitle: "Health & Repayment",
    description:
      "Continuous battery health and usage monitoring. Automated collection nudges aligned to earning patterns. Early warning alerts 30+ days before potential defaults.",
    icon: LineChart,
    color: "text-amber-600",
    bgColor: "bg-amber-50",
  },
  {
    step: 5,
    title: "Lifecycle Ops",
    subtitle: "Recovery & Second Life",
    description:
      "End-of-life batteries routed to certified recyclers or second-life applications. Remote immobilisation available for defaults. Full EPR compliance reporting.",
    icon: RefreshCcw,
    color: "text-pink-600",
    bgColor: "bg-pink-50",
  },
];

export default function WorkflowAnimation() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.1 });

  return (
    <section className="py-16 md:py-24 bg-gray-50">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="Operational Workflow"
          title="From Origination to End-of-Life"
          subtitle="A seamless, data-driven pipeline that makes every battery a trackable, financeable, recoverable asset."
        />

        <div ref={ref} className="mt-14">
          {/* Desktop: horizontal workflow */}
          <div className="hidden lg:block">
            {/* Step icons row */}
            <div className="flex items-start justify-between">
              {steps.map((s, i) => (
                <div key={s.step} className="flex items-start flex-1">
                  <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={inView ? { opacity: 1, y: 0 } : {}}
                    transition={{ duration: 0.5, delay: i * 0.15 }}
                    className="flex flex-col items-center text-center flex-1"
                  >
                    {/* Circle */}
                    <div className="relative">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={inView ? { scale: 1 } : {}}
                        transition={{
                          type: "spring",
                          delay: i * 0.15 + 0.1,
                          stiffness: 200,
                        }}
                        className={cn(
                          "flex h-16 w-16 items-center justify-center rounded-full border-2 border-gray-200",
                          s.bgColor
                        )}
                      >
                        <s.icon className={cn("h-7 w-7", s.color)} />
                      </motion.div>
                      <span className="absolute -top-1 -right-1 flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-xs font-bold text-white shadow-sm">
                        {s.step}
                      </span>
                    </div>

                    <h4 className="mt-4 text-sm font-bold text-gray-900">
                      {s.title}
                    </h4>
                    <p className="mt-0.5 text-xs font-medium text-brand-500">
                      {s.subtitle}
                    </p>
                    <p className="mt-2 text-xs text-gray-500 max-w-[180px] leading-relaxed">
                      {s.description}
                    </p>
                  </motion.div>

                  {/* Arrow connector */}
                  {i < steps.length - 1 && (
                    <motion.div
                      initial={{ opacity: 0, scaleX: 0 }}
                      animate={inView ? { opacity: 1, scaleX: 1 } : {}}
                      transition={{ duration: 0.4, delay: i * 0.15 + 0.2 }}
                      className="flex items-center pt-7 px-1"
                    >
                      <div className="flex items-center gap-0.5">
                        <div className="h-px w-6 bg-brand-300" />
                        <ChevronRight className="h-4 w-4 text-brand-400" />
                      </div>
                    </motion.div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Tablet/Mobile: vertical workflow */}
          <div className="lg:hidden space-y-0">
            {steps.map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, x: -20 }}
                animate={inView ? { opacity: 1, x: 0 } : {}}
                transition={{ duration: 0.5, delay: i * 0.1 }}
                className="relative flex gap-5"
              >
                {/* Vertical line */}
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 border-gray-200 z-10",
                      s.bgColor
                    )}
                  >
                    <s.icon className={cn("h-5 w-5", s.color)} />
                    <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
                      {s.step}
                    </span>
                  </div>
                  {i < steps.length - 1 && (
                    <div className="w-px flex-1 bg-gray-200 min-h-[24px]" />
                  )}
                </div>

                {/* Content */}
                <div className="pb-8">
                  <h4 className="text-base font-bold text-gray-900">
                    {s.title}
                  </h4>
                  <p className="text-xs font-medium text-brand-500">
                    {s.subtitle}
                  </p>
                  <p className="mt-1.5 text-sm text-gray-600 leading-relaxed">
                    {s.description}
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
