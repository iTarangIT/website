"use client";

import { motion } from "framer-motion";
import { fadeUp } from "@/lib/animations";
import { AlertTriangle, TrendingDown, EyeOff } from "lucide-react";

const stats = [
  { icon: EyeOff, value: "0%", label: "SOH visibility at loan origination" },
  { icon: TrendingDown, value: "8–12%", label: "EV battery NPA rate today" },
  { icon: AlertTriangle, value: "₹0", label: "Recovery value on defaulted batteries" },
];

export default function PainPointsSection() {
  return (
    <section className="relative bg-gray-950 py-20 md:py-28 overflow-hidden">
      {/* Subtle radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-brand-500/5 blur-3xl pointer-events-none" />

      <div className="relative mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* Opening quote */}
        <motion.div {...fadeUp} className="text-center mb-16">
          <div className="inline-block mb-6">
            <span className="text-brand-400 text-6xl leading-none font-serif">&ldquo;</span>
          </div>
          <p className="text-2xl sm:text-3xl md:text-4xl font-bold text-white leading-snug max-w-4xl mx-auto">
            You&apos;re lending against a{" "}
            <span className="text-accent-pink">blind asset</span>. No SOH
            visibility, no usage data, no recovery mechanism.
          </p>
          <p className="mt-6 text-lg md:text-xl text-brand-200 max-w-2xl mx-auto">
            That&apos;s why EV battery NPAs are{" "}
            <span className="font-bold text-accent-pink">8&ndash;12%</span> &mdash;
            and why NBFCs avoid this asset class entirely.
          </p>
        </motion.div>

        {/* Supporting stats */}
        <motion.div
          {...fadeUp}
          transition={{ ...fadeUp.transition, delay: 0.2 }}
          className="grid grid-cols-1 sm:grid-cols-3 gap-6"
        >
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-white/10 bg-white/5 p-6 text-center backdrop-blur-sm"
            >
              <stat.icon className="h-8 w-8 text-accent-pink mx-auto mb-3" />
              <p className="text-3xl font-bold text-white">{stat.value}</p>
              <p className="mt-1 text-sm text-gray-400">{stat.label}</p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
