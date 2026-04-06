"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { ArrowRight, Battery, Brain, TrendingDown, Banknote } from "lucide-react";
import Link from "next/link";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

interface FlywheelNode {
  label: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
}

const nodes: FlywheelNode[] = [
  {
    label: "More Batteries",
    icon: Battery,
    color: "text-brand-600",
    bgColor: "bg-brand-100",
  },
  {
    label: "Smarter Risk Engine",
    icon: Brain,
    color: "text-blue-600",
    bgColor: "bg-blue-100",
  },
  {
    label: "Lower NPAs",
    icon: TrendingDown,
    color: "text-green-600",
    bgColor: "bg-green-100",
  },
  {
    label: "More Capital",
    icon: Banknote,
    color: "text-amber-600",
    bgColor: "bg-amber-100",
  },
];

export default function DataFlywheelPreview() {
  const { ref, inView } = useInView({ triggerOnce: false, threshold: 0.3 });
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % nodes.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [inView]);

  // Calculate positions for 4 nodes in a circle
  const radius = 140; // px from center
  const centerX = 200;
  const centerY = 200;

  const getPosition = (index: number) => {
    // Start from top (-90deg) and go clockwise
    const angle = ((index * 360) / nodes.length - 90) * (Math.PI / 180);
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  };

  // SVG arrow paths between consecutive nodes
  const getArrowPath = (fromIdx: number, toIdx: number) => {
    const from = getPosition(fromIdx);
    const to = getPosition(toIdx);
    // Offset slightly toward the next node
    const dx = to.x - from.x;
    const dy = to.y - from.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const offsetFrom = 36; // node radius
    const offsetTo = 36;
    const sx = from.x + (dx / dist) * offsetFrom;
    const sy = from.y + (dy / dist) * offsetFrom;
    const ex = to.x - (dx / dist) * offsetTo;
    const ey = to.y - (dy / dist) * offsetTo;
    // Curved path
    const mx = (sx + ex) / 2 + (sy - ey) * 0.15;
    const my = (sy + ey) / 2 + (ex - sx) * 0.15;
    return `M ${sx} ${sy} Q ${mx} ${my} ${ex} ${ey}`;
  };

  return (
    <section ref={ref} className="py-20 md:py-28 bg-brand-950 overflow-hidden">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="Network Effects"
            title="The Data Flywheel"
            dark
          />
        </FadeInOnScroll>

        <div className="flex flex-col lg:flex-row items-center gap-12 lg:gap-20">
          {/* Flywheel visualization */}
          <FadeInOnScroll className="flex-1 flex justify-center">
            <div className="relative w-[400px] h-[400px]">
              <svg
                viewBox="0 0 400 400"
                className="w-full h-full"
                fill="none"
              >
                {/* Connecting curved arrows */}
                {nodes.map((_, i) => {
                  const nextIdx = (i + 1) % nodes.length;
                  const isActive = i === activeIndex;
                  return (
                    <g key={`arrow-${i}`}>
                      <defs>
                        <marker
                          id={`arrowhead-${i}`}
                          markerWidth="8"
                          markerHeight="6"
                          refX="7"
                          refY="3"
                          orient="auto"
                        >
                          <path
                            d="M0,0 L8,3 L0,6"
                            fill={isActive ? "#5b7bff" : "#041580"}
                          />
                        </marker>
                      </defs>
                      <motion.path
                        d={getArrowPath(i, nextIdx)}
                        stroke={isActive ? "#5b7bff" : "#041580"}
                        strokeWidth={isActive ? 2.5 : 1.5}
                        strokeDasharray="6 4"
                        markerEnd={`url(#arrowhead-${i})`}
                        animate={{
                          stroke: isActive ? "#5b7bff" : "#041580",
                          strokeWidth: isActive ? 2.5 : 1.5,
                        }}
                        transition={{ duration: 0.5 }}
                      />
                    </g>
                  );
                })}
              </svg>

              {/* Node circles positioned absolutely on top of SVG */}
              {nodes.map((node, i) => {
                const pos = getPosition(i);
                const Icon = node.icon;
                const isActive = i === activeIndex;

                return (
                  <motion.div
                    key={node.label}
                    className="absolute flex flex-col items-center"
                    style={{
                      left: pos.x,
                      top: pos.y,
                      transform: "translate(-50%, -50%)",
                    }}
                    animate={{
                      scale: isActive ? 1.15 : 1,
                    }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                  >
                    <div
                      className={`flex h-16 w-16 items-center justify-center rounded-full transition-all duration-500 ${
                        isActive
                          ? "bg-brand-500 shadow-lg shadow-brand-500/40"
                          : "bg-brand-800 border border-brand-600/30"
                      }`}
                    >
                      <Icon
                        className={`h-7 w-7 ${
                          isActive ? "text-white" : "text-brand-300"
                        }`}
                      />
                    </div>
                    <span
                      className={`mt-2 text-xs font-semibold text-center whitespace-nowrap transition-colors duration-500 ${
                        isActive ? "text-white" : "text-brand-400"
                      }`}
                    >
                      {node.label}
                    </span>
                  </motion.div>
                );
              })}

              {/* Center label */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-xs uppercase tracking-widest text-brand-400 font-semibold">
                    Flywheel
                  </div>
                </div>
              </div>
            </div>
          </FadeInOnScroll>

          {/* Description */}
          <FadeInOnScroll delay={0.2} className="flex-1 max-w-lg">
            <h3 className="text-2xl font-bold text-white mb-4">
              Every Battery Makes the System Smarter
            </h3>
            <p className="text-brand-200 leading-relaxed mb-4">
              Each new battery onboarded adds telemetry data that sharpens our
              risk engine. Better risk scoring attracts more institutional
              capital. More capital means more drivers get financing. More
              drivers mean more batteries on the platform.
            </p>
            <p className="text-brand-300 text-sm leading-relaxed mb-8">
              This compounding data flywheel creates a durable competitive moat
              and drives down NPAs with every cycle, making iTarang the
              intelligence backbone of the EV battery economy.
            </p>
            <Link
              href="/for-nbfcs"
              className="inline-flex items-center gap-2 text-brand-300 font-semibold hover:text-white transition-colors group"
            >
              See How It Works
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </FadeInOnScroll>
        </div>
      </div>
    </section>
  );
}
