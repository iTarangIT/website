"use client";

import { motion, type Variants } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { ArrowRight, ChevronDown, CheckCircle2 } from "lucide-react";
import { roadmapPhases } from "@/data/roadmap";

const containerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.25 },
  },
};

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 40, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.6, ease: "easeOut" },
  },
};

export default function PhaseTimeline() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.1 });

  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          ref={ref}
          variants={containerVariants}
          initial="hidden"
          animate={inView ? "visible" : "hidden"}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-0 items-stretch"
        >
          {roadmapPhases.map((phase, idx) => (
            <div key={phase.phase} className="flex flex-col items-center">
              <motion.div
                variants={cardVariants}
                className="relative w-full max-w-sm lg:max-w-none"
              >
                <div
                  className="rounded-2xl border border-gray-100 bg-white shadow-lg overflow-hidden h-full"
                  style={{
                    borderTop: `4px solid ${phase.color}`,
                  }}
                >
                  {/* Phase header */}
                  <div
                    className="px-6 pt-6 pb-4"
                    style={{
                      background: `linear-gradient(135deg, ${phase.color}10, ${phase.color}05)`,
                    }}
                  >
                    <span
                      className="inline-flex items-center justify-center w-10 h-10 rounded-full text-white text-sm font-bold mb-3"
                      style={{ backgroundColor: phase.color }}
                    >
                      {phase.phase}
                    </span>
                    <h3 className="text-xl font-bold text-gray-900">
                      {phase.title}
                    </h3>
                    <p className="text-sm text-gray-500 mt-1 font-medium">
                      {phase.timeline}
                    </p>
                  </div>

                  {/* Key metric */}
                  <div className="px-6 py-5 border-y border-gray-100">
                    <p
                      className="text-3xl md:text-4xl font-extrabold"
                      style={{ color: phase.color }}
                    >
                      {phase.keyMetric}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {phase.metricLabel}
                    </p>
                  </div>

                  {/* Details list */}
                  <ul className="px-6 py-5 space-y-3">
                    {phase.details.map((detail) => (
                      <li
                        key={detail}
                        className="flex items-start gap-2.5 text-sm text-gray-700"
                      >
                        <CheckCircle2
                          className="h-4 w-4 mt-0.5 shrink-0"
                          style={{ color: phase.color }}
                        />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </div>
              </motion.div>

              {/* Connector arrow */}
              {idx < roadmapPhases.length - 1 && (
                <>
                  {/* Desktop: horizontal arrow */}
                  <div className="hidden lg:flex items-center justify-center absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10">
                    <ArrowRight className="h-6 w-6 text-brand-400" />
                  </div>
                  {/* Mobile: vertical arrow */}
                  <div className="lg:hidden flex justify-center my-3">
                    <ChevronDown className="h-6 w-6 text-brand-400" />
                  </div>
                </>
              )}
            </div>
          ))}
        </motion.div>

        {/* Desktop connector lines */}
        <div className="hidden lg:block relative -mt-[1px]">
          <div className="absolute top-1/2 left-[16.67%] right-[16.67%] h-0.5 bg-gradient-to-r from-brand-500 via-brand-400 to-brand-900 -translate-y-[280px] opacity-20" />
        </div>
      </div>
    </section>
  );
}
