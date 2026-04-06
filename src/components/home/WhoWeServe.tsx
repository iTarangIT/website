"use client";

import { Zap, Store, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

const audiences = [
  {
    icon: Zap,
    title: "Drivers",
    description: "Better batteries, daily EMIs you can afford. Earn more, worry less.",
    placeholder: "PHOTO: E-rickshaw driver",
    gradient: "from-amber-400/20 via-orange-300/10 to-transparent",
    iconBg: "bg-amber-500/10",
    accent: "text-amber-600",
    borderHover: "hover:border-amber-300",
  },
  {
    icon: Store,
    title: "Dealers",
    description: "Sell more with ready financing. Zero credit risk, higher margins.",
    placeholder: "PHOTO: Dealer shop",
    gradient: "from-blue-400/20 via-indigo-300/10 to-transparent",
    iconBg: "bg-blue-500/10",
    accent: "text-blue-600",
    borderHover: "hover:border-blue-300",
  },
  {
    icon: BarChart3,
    title: "Lenders",
    description: "See inside every battery you finance. Real-time data, real confidence.",
    placeholder: "PHOTO: Office / Dashboard",
    gradient: "from-emerald-400/20 via-teal-300/10 to-transparent",
    iconBg: "bg-emerald-500/10",
    accent: "text-emerald-600",
    borderHover: "hover:border-emerald-300",
  },
];

export default function WhoWeServe() {
  return (
    <section className="py-24 md:py-32 bg-surface-warm relative overflow-hidden">
      {/* Subtle background pattern */}
      <div className="absolute top-0 right-0 w-1/2 h-full bg-[radial-gradient(ellipse_at_top_right,rgba(103,61,230,0.04),transparent_60%)]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10">
        <FadeInOnScroll>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="inline-block text-sm font-semibold text-brand-500 tracking-widest uppercase mb-4">
              Who We Serve
            </span>
            <h2 className="text-4xl sm:text-5xl text-gray-900 tracking-tight leading-[1.1]">
              Built for the people who{" "}
              <span className="gradient-text">move India</span>
            </h2>
          </div>
        </FadeInOnScroll>

        <div className="grid gap-8 md:grid-cols-3">
          {audiences.map((item, i) => {
            const Icon = item.icon;
            return (
              <FadeInOnScroll key={item.title} delay={i * 0.12}>
                <motion.div
                  whileHover={{ y: -6, transition: { duration: 0.3 } }}
                  className={`group rounded-3xl bg-white border border-gray-200/60 overflow-hidden shadow-sm hover:shadow-xl transition-all duration-500 ${item.borderHover}`}
                >
                  {/* Photo placeholder with gradient overlay */}
                  <div className="relative h-52 overflow-hidden">
                    <div className="absolute inset-0 bg-gray-100" />
                    <div className={`absolute inset-0 bg-gradient-to-b ${item.gradient}`} />
                    <span className="absolute inset-0 flex items-center justify-center text-sm font-medium text-gray-400">
                      {item.placeholder}
                    </span>
                    {/* Floating icon badge */}
                    <div className="absolute bottom-4 left-4">
                      <div className={`${item.iconBg} backdrop-blur-sm w-12 h-12 rounded-2xl flex items-center justify-center border border-white/30 shadow-lg group-hover:scale-110 transition-transform`}>
                        <Icon className={`h-6 w-6 ${item.accent}`} />
                      </div>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-6 pt-5">
                    <h3 className="text-xl text-gray-900 mb-2 font-sans font-bold">
                      {item.title}
                    </h3>
                    <p className="text-gray-500 leading-relaxed text-[15px]">
                      {item.description}
                    </p>
                  </div>
                </motion.div>
              </FadeInOnScroll>
            );
          })}
        </div>
      </div>
    </section>
  );
}
