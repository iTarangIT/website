"use client";

import { EyeOff, Lock, Recycle } from "lucide-react";
import { cn } from "@/lib/utils";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

interface ProblemCard {
  icon: React.ElementType;
  title: string;
  points: string[];
  consequence: string;
}

const problems: ProblemCard[] = [
  {
    icon: EyeOff,
    title: "Lenders Fly Blind",
    points: [
      "No real-time State of Health (SOH) data available",
      "High risk perception deters institutional capital",
      "Weak recovery mechanisms increase NPA exposure",
    ],
    consequence: "High NPAs & Reluctance to Lend",
  },
  {
    icon: Lock,
    title: "Drivers Locked Out",
    points: [
      "Thin credit files make formal lending impossible",
      "Informal financing traps at 30-60% interest rates",
      "Slow, opaque approval processes",
    ],
    consequence: "Financial Exclusion & High Costs",
  },
  {
    icon: Recycle,
    title: "Lifecycle Unmanaged",
    points: [
      "No structured end-of-life pathway for batteries",
      "Growing compliance and EPR regulatory risk",
      "Missed second-life and recycling value capture",
    ],
    consequence: "Lost Value & Regulatory Exposure",
  },
];

export default function ProblemSection() {
  return (
    <section className="py-20 md:py-28 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="The Problem"
            title="Three Systemic Gaps Breaking EV Battery Financing"
          />
        </FadeInOnScroll>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {problems.map((problem, i) => {
            const Icon = problem.icon;
            return (
              <FadeInOnScroll key={problem.title} delay={i * 0.15}>
                <div className="relative flex flex-col h-full bg-white rounded-2xl shadow-sm border border-gray-100 p-8 hover:shadow-lg transition-shadow duration-300">
                  {/* Icon */}
                  <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 mb-6">
                    <Icon className="h-7 w-7 text-brand-500" />
                  </div>

                  {/* Title */}
                  <h3 className="text-xl font-bold text-gray-900 mb-4">
                    {problem.title}
                  </h3>

                  {/* Points */}
                  <ul className="space-y-3 flex-1 mb-6">
                    {problem.points.map((point, j) => (
                      <li
                        key={j}
                        className="flex items-start gap-2 text-sm text-gray-600"
                      >
                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-brand-400 shrink-0" />
                        {point}
                      </li>
                    ))}
                  </ul>

                  {/* Consequence badge */}
                  <div className="mt-auto">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold",
                        "bg-red-50 text-red-700 border border-red-100"
                      )}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
                      {problem.consequence}
                    </span>
                  </div>
                </div>
              </FadeInOnScroll>
            );
          })}
        </div>
      </div>
    </section>
  );
}
