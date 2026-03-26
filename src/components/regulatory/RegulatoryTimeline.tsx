"use client";

import { regulatoryTimeline } from "@/data/regulatory";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";

export default function RegulatoryTimeline() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.2 });

  return (
    <div ref={ref}>
      {/* Horizontal timeline - desktop */}
      <div className="hidden md:block">
        <div className="relative">
          {/* Connecting line */}
          <div className="absolute top-6 left-0 right-0 h-0.5 bg-brand-200" />
          <motion.div
            className="absolute top-6 left-0 h-0.5 bg-brand-500"
            initial={{ width: "0%" }}
            animate={inView ? { width: "100%" } : { width: "0%" }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />

          <div className="relative grid grid-cols-4 gap-8">
            {regulatoryTimeline.map((milestone, idx) => (
              <motion.div
                key={milestone.year}
                initial={{ opacity: 0, y: 30 }}
                animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
                transition={{
                  duration: 0.5,
                  delay: 0.3 + idx * 0.2,
                  ease: "easeOut",
                }}
                className="flex flex-col items-center text-center"
              >
                {/* Dot */}
                <div
                  className={cn(
                    "relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-4 border-white shadow-md",
                    idx <= 1
                      ? "bg-brand-500"
                      : "bg-brand-100 border-brand-300"
                  )}
                >
                  <span
                    className={cn(
                      "text-xs font-bold",
                      idx <= 1 ? "text-white" : "text-brand-600"
                    )}
                  >
                    {milestone.year}
                  </span>
                </div>

                {/* Label */}
                <h4 className="mt-4 text-sm font-bold text-brand-700">
                  {milestone.label}
                </h4>

                {/* Description */}
                <p className="mt-2 text-sm text-gray-600 leading-relaxed max-w-[220px]">
                  {milestone.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Vertical timeline - mobile */}
      <div className="md:hidden">
        <div className="relative pl-8">
          {/* Vertical line */}
          <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-brand-200" />
          <motion.div
            className="absolute left-3 top-0 w-0.5 bg-brand-500"
            initial={{ height: "0%" }}
            animate={inView ? { height: "100%" } : { height: "0%" }}
            transition={{ duration: 1.2, ease: "easeOut" }}
          />

          <div className="space-y-10">
            {regulatoryTimeline.map((milestone, idx) => (
              <motion.div
                key={milestone.year}
                initial={{ opacity: 0, x: -20 }}
                animate={
                  inView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }
                }
                transition={{
                  duration: 0.5,
                  delay: 0.2 + idx * 0.15,
                  ease: "easeOut",
                }}
                className="relative"
              >
                {/* Dot */}
                <div
                  className={cn(
                    "absolute -left-8 top-0 flex h-6 w-6 items-center justify-center rounded-full border-2 border-white shadow",
                    idx <= 1 ? "bg-brand-500" : "bg-brand-200"
                  )}
                >
                  <div
                    className={cn(
                      "h-2 w-2 rounded-full",
                      idx <= 1 ? "bg-white" : "bg-brand-400"
                    )}
                  />
                </div>

                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-brand-500">
                    {milestone.year}
                  </span>
                  <h4 className="mt-1 text-base font-bold text-gray-900">
                    {milestone.label}
                  </h4>
                  <p className="mt-1 text-sm text-gray-600 leading-relaxed">
                    {milestone.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
