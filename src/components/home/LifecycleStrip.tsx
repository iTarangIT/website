"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Banknote,
  Truck,
  Activity,
  Wrench,
  RotateCcw,
  Recycle,
} from "lucide-react";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const stages = [
  {
    icon: Banknote,
    label: "Finance",
    description:
      "Drivers get a lithium battery on EMI. NBFCs get IoT-backed risk data before they approve.",
    stat: "₹49K avg loan, 18-month tenure",
    gradient: "from-blue-500/20 to-indigo-500/20",
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-600",
  },
  {
    icon: Truck,
    label: "Deploy",
    description:
      "Dealer installs the battery + IoT device. Driver is live in 24 hours.",
    stat: "24-hour activation",
    gradient: "from-blue-500/20 to-cyan-500/20",
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-500",
  },
  {
    icon: Activity,
    label: "Monitor",
    description:
      "Real-time SOH, SOC, location, temperature, charge cycles. Every battery has a heartbeat.",
    stat: "150+ batteries tracked live",
    gradient: "from-cyan-500/20 to-teal-500/20",
    iconBg: "bg-cyan-500/10",
    iconColor: "text-cyan-600",
  },
  {
    icon: Wrench,
    label: "Maintain",
    description:
      "Alerts for anomalies before they become failures. Extend battery life by 20-30%.",
    stat: "20-30% longer lifespan",
    gradient: "from-teal-500/20 to-emerald-500/20",
    iconBg: "bg-teal-500/10",
    iconColor: "text-teal-600",
  },
  {
    icon: RotateCcw,
    label: "Buyback",
    description:
      "When the battery reaches end-of-first-life, we buy it back. Fair price based on actual health data.",
    stat: "98% recovery rate",
    gradient: "from-amber-500/20 to-orange-500/20",
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-600",
  },
  {
    icon: Recycle,
    label: "Recycle",
    description:
      "Partnered recyclers extract cobalt, lithium, and nickel. Full EPR compliance for OEMs.",
    stat: "Full EPR compliance",
    gradient: "from-emerald-500/20 to-green-500/20",
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-600",
  },
];

export default function LifecycleStrip() {
  const [activeStage, setActiveStage] = useState<number | null>(null);

  return (
    <section id="lifecycle" className="py-24 md:py-32 bg-surface-warm relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4">
              The Full Lifecycle
            </span>
            <h2 className="text-4xl sm:text-5xl lg:text-6xl text-gray-900 tracking-tight leading-[1.1]">
              Six stages.{" "}
              <span className="gradient-text">Zero blind spots.</span>
            </h2>
            <p className="mt-6 text-lg text-gray-500 leading-relaxed">
              No competitor covers the entire journey. We do.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Lifecycle grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {stages.map((stage, i) => {
            const Icon = stage.icon;
            const isActive = activeStage === i;

            return (
              <FadeInOnScroll key={stage.label} delay={i * 0.08}>
                <button
                  onClick={() => setActiveStage(isActive ? null : i)}
                  className={`w-full text-left rounded-2xl p-5 transition-all duration-300 border group relative overflow-hidden ${
                    isActive
                      ? "border-brand-300 bg-white shadow-xl shadow-brand-500/10 scale-[1.02]"
                      : "border-gray-200/60 bg-white/60 hover:bg-white hover:border-brand-200 hover:shadow-lg"
                  }`}
                >
                  {/* Gradient background on hover/active */}
                  <div className={`absolute inset-0 bg-gradient-to-br ${stage.gradient} opacity-0 ${isActive ? "opacity-100" : "group-hover:opacity-50"} transition-opacity rounded-2xl`} />

                  <div className="relative z-10">
                    {/* Step number + icon */}
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-[10px] font-bold text-brand-400 font-mono tracking-wider">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                    </div>

                    {/* Icon */}
                    <div className={`${stage.iconBg} w-10 h-10 rounded-xl flex items-center justify-center mb-3 transition-transform ${isActive ? "scale-110" : "group-hover:scale-105"}`}>
                      <Icon className={`h-5 w-5 ${stage.iconColor}`} />
                    </div>

                    {/* Label */}
                    <h3 className="text-base font-semibold text-gray-900 font-sans">
                      {stage.label}
                    </h3>

                    {/* Expanded content */}
                    <AnimatePresence>
                      {isActive && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.25 }}
                          className="overflow-hidden"
                        >
                          <p className="mt-3 text-sm text-gray-600 leading-relaxed font-sans">
                            {stage.description}
                          </p>
                          <p className="mt-3 text-xs font-bold text-brand-600 font-mono">
                            {stage.stat}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </button>
              </FadeInOnScroll>
            );
          })}
        </div>

        {/* Connecting dots */}
        <div className="hidden lg:flex items-center justify-center mt-8 gap-0">
          {stages.map((_, i) => (
            <div key={i} className="flex items-center">
              <div className={`h-2 w-2 rounded-full transition-colors ${activeStage === i ? "bg-brand-500 scale-125" : "bg-brand-300/50"}`} />
              {i < stages.length - 1 && (
                <div className="h-px w-16 bg-gradient-to-r from-brand-300/50 to-brand-300/20" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
