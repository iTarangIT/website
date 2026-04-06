"use client";

import { motion, type Variants } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { Network, Landmark, BarChart3 } from "lucide-react";
import { executionLayers } from "@/data/roadmap";
import { cn } from "@/lib/utils";

const layerConfig = [
  {
    icon: Network,
    gradient: "from-brand-500 to-brand-600",
    bg: "bg-brand-50",
    border: "border-brand-200",
    iconBg: "bg-brand-100",
    iconColor: "text-brand-600",
    accentColor: "text-brand-700",
  },
  {
    icon: Landmark,
    gradient: "from-accent-sky to-pink-600",
    bg: "bg-pink-50",
    border: "border-pink-200",
    iconBg: "bg-pink-100",
    iconColor: "text-pink-600",
    accentColor: "text-pink-700",
  },
  {
    icon: BarChart3,
    gradient: "from-accent-green to-green-600",
    bg: "bg-green-50",
    border: "border-green-200",
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
    accentColor: "text-green-700",
  },
];

const containerVariants: Variants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.15 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, x: -30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, ease: "easeOut" },
  },
};

export default function ExecutionLayers() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.1 });

  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          ref={ref}
          variants={containerVariants}
          initial="hidden"
          animate={inView ? "visible" : "hidden"}
          className="space-y-5"
        >
          {executionLayers.map((layer, idx) => {
            const config = layerConfig[idx];
            const Icon = config.icon;

            return (
              <motion.div
                key={layer.title}
                variants={itemVariants}
                className={cn(
                  "relative rounded-2xl border p-6 md:p-8 transition-shadow hover:shadow-md",
                  config.bg,
                  config.border
                )}
              >
                {/* Left accent bar */}
                <div
                  className={cn(
                    "absolute left-0 top-4 bottom-4 w-1 rounded-full bg-gradient-to-b",
                    config.gradient
                  )}
                />

                <div className="grid grid-cols-1 md:grid-cols-12 gap-4 md:gap-6 items-center pl-4">
                  {/* Icon + Title */}
                  <div className="md:col-span-3 flex items-center gap-3">
                    <div
                      className={cn(
                        "flex items-center justify-center w-10 h-10 rounded-lg shrink-0",
                        config.iconBg
                      )}
                    >
                      <Icon className={cn("h-5 w-5", config.iconColor)} />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900">
                        {layer.title}
                      </h3>
                      <p className="text-xs text-gray-500 font-medium">
                        {layer.timing}
                      </p>
                    </div>
                  </div>

                  {/* Target */}
                  <div className="md:col-span-3">
                    <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">
                      Target
                    </p>
                    <p className="text-sm text-gray-700 font-medium">
                      {layer.target}
                    </p>
                  </div>

                  {/* Offer */}
                  <div className="md:col-span-3">
                    <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">
                      Offer
                    </p>
                    <p className="text-sm text-gray-700 font-medium">
                      {layer.offer}
                    </p>
                  </div>

                  {/* Goal */}
                  <div className="md:col-span-3">
                    <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold mb-1">
                      Goal
                    </p>
                    <p
                      className={cn(
                        "text-sm font-bold",
                        config.accentColor
                      )}
                    >
                      {layer.goal}
                    </p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </motion.div>

        {/* Overlap indicator */}
        <div className="mt-8 flex items-center justify-center gap-2 text-sm text-gray-400">
          <div className="h-px w-12 bg-gray-200" />
          <span>Layers execute in parallel with overlapping timelines</span>
          <div className="h-px w-12 bg-gray-200" />
        </div>
      </div>
    </section>
  );
}
