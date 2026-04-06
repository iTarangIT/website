"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useInView } from "react-intersection-observer";
import SectionHeading from "@/components/shared/SectionHeading";

interface FlywheelNode {
  label: string;
  description: string;
  angle: number; // position on circle in degrees
}

const nodes: FlywheelNode[] = [
  {
    label: "More Batteries Onboarded",
    description: "Dealers drive adoption through financing at POS",
    angle: 270, // top
  },
  {
    label: "Smarter Risk Engine",
    description: "Every data point improves underwriting accuracy",
    angle: 0, // right
  },
  {
    label: "Lower NPAs & Higher Trust",
    description: "Better risk assessment means fewer defaults",
    angle: 90, // bottom
  },
  {
    label: "More Institutional Capital",
    description: "Proven performance attracts larger NBFC commitments",
    angle: 180, // left
  },
];

export default function DataFlywheelAnimation() {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.3 });
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % nodes.length);
    }, 2000);
    return () => clearInterval(interval);
  }, [inView]);

  // Responsive radius - smaller on mobile
  const radius = 160;

  return (
    <section className="py-16 md:py-24 bg-brand-950 overflow-hidden">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          badge="Data Flywheel"
          title="The Compounding Advantage"
          subtitle="Every battery onboarded makes the entire ecosystem smarter and more valuable."
          dark
        />

        <div ref={ref} className="relative mt-12 flex justify-center">
          {/* SVG circle and arrows */}
          <div className="relative w-[380px] h-[380px] sm:w-[420px] sm:h-[420px]">
            <svg
              viewBox="0 0 420 420"
              className="w-full h-full"
              fill="none"
            >
              {/* Circular track */}
              <circle
                cx="210"
                cy="210"
                r={radius}
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="2"
                fill="none"
              />

              {/* Animated arc showing progress */}
              {inView && (
                <motion.circle
                  cx="210"
                  cy="210"
                  r={radius}
                  stroke="url(#flywheelGradient)"
                  strokeWidth="3"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={2 * Math.PI * radius}
                  initial={{ strokeDashoffset: 2 * Math.PI * radius }}
                  animate={{ strokeDashoffset: 0 }}
                  transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                />
              )}

              {/* Arrow heads between nodes */}
              {nodes.map((_, i) => {
                const midAngle =
                  ((nodes[i].angle + nodes[(i + 1) % nodes.length].angle) / 2) *
                    (Math.PI / 180) +
                  (i === 3 ? Math.PI : 0);
                const ax = 210 + (radius + 2) * Math.cos(midAngle);
                const ay = 210 + (radius + 2) * Math.sin(midAngle);
                return (
                  <motion.polygon
                    key={`arrow-${i}`}
                    points="-5,-3 5,0 -5,3"
                    fill="rgba(255,255,255,0.3)"
                    initial={{ opacity: 0 }}
                    animate={inView ? { opacity: 1 } : {}}
                    transition={{ delay: 0.5 + i * 0.2 }}
                    transform={`translate(${ax},${ay}) rotate(${nodes[i].angle + 45})`}
                  />
                );
              })}

              <defs>
                <linearGradient
                  id="flywheelGradient"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="100%"
                >
                  <stop offset="0%" stopColor="#051b9a" />
                  <stop offset="50%" stopColor="#38bdf8" />
                  <stop offset="100%" stopColor="#051b9a" />
                </linearGradient>
              </defs>
            </svg>

            {/* Center label */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-sm font-semibold text-brand-300 uppercase tracking-wider">
                  Data
                </p>
                <p className="text-lg font-bold text-white">Flywheel</p>
              </div>
            </div>

            {/* Nodes */}
            {nodes.map((node, i) => {
              const angleRad = (node.angle * Math.PI) / 180;
              const x = 210 + radius * Math.cos(angleRad);
              const y = 210 + radius * Math.sin(angleRad);
              const isActive = activeIndex === i && inView;

              return (
                <motion.div
                  key={node.label}
                  className="absolute"
                  style={{
                    left: `${(x / 420) * 100}%`,
                    top: `${(y / 420) * 100}%`,
                    transform: "translate(-50%, -50%)",
                  }}
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={inView ? { opacity: 1, scale: 1 } : {}}
                  transition={{ delay: 0.3 + i * 0.15, duration: 0.4 }}
                >
                  <motion.div
                    animate={
                      isActive
                        ? { scale: 1.1, boxShadow: "0 0 24px rgba(5,27,154,0.4)" }
                        : { scale: 1, boxShadow: "0 0 0px rgba(5,27,154,0)" }
                    }
                    transition={{ duration: 0.4 }}
                    className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 border-2 border-brand-400"
                  >
                    <span className="text-sm font-bold text-white">{i + 1}</span>
                  </motion.div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Node descriptions below */}
        <div className="mt-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <AnimatePresence>
            {nodes.map((node, i) => (
              <motion.div
                key={node.label}
                initial={{ opacity: 0, y: 20 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: 0.5 + i * 0.1 }}
                className={`rounded-xl border p-5 text-center transition-all duration-300 ${
                  activeIndex === i && inView
                    ? "border-brand-400 bg-brand-900/50"
                    : "border-white/10 bg-white/5"
                }`}
              >
                <div className="flex h-8 w-8 mx-auto items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white mb-3">
                  {i + 1}
                </div>
                <h4 className="text-sm font-semibold text-white">{node.label}</h4>
                <p className="mt-1 text-xs text-gray-400">{node.description}</p>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
