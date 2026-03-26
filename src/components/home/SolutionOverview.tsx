"use client";

import { Activity, Brain, RefreshCcw, ArrowRight } from "lucide-react";
import Link from "next/link";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";

interface Pillar {
  icon: React.ElementType;
  title: string;
  points: string[];
  benefit: string;
}

const pillars: Pillar[] = [
  {
    icon: Activity,
    title: "Smart Battery Telemetry",
    points: [
      "Real-time SOH & SOC tracking",
      "Usage pattern analytics",
      "GPS-based asset tracking",
    ],
    benefit: "Eliminates Blind Asset Risk",
  },
  {
    icon: Brain,
    title: "Intelligent Risk Evaluation Engine",
    points: [
      "Behavioral scoring models",
      "API-first integration with lending systems",
      "Financial inclusion via alternative data",
    ],
    benefit: "Unlocks Institutional Capital",
  },
  {
    icon: RefreshCcw,
    title: "Lifecycle Asset Management",
    points: [
      "Remote immobilisation for recovery",
      "Automated second-life routing",
      "Built-in EPR compliance reporting",
    ],
    benefit: "Maximizes Residual Value",
  },
];

export default function SolutionOverview() {
  return (
    <section className="py-20 md:py-28 bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <FadeInOnScroll>
          <SectionHeading
            badge="The Solution"
            title="Three Integrated Pillars"
          />
        </FadeInOnScroll>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {pillars.map((pillar, i) => {
            const Icon = pillar.icon;
            return (
              <FadeInOnScroll key={pillar.title} delay={i * 0.15}>
                <div className="group relative flex flex-col h-full bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:-translate-y-1 hover:shadow-xl transition-all duration-300">
                  {/* Gradient top border */}
                  <div className="h-1 w-full bg-gradient-to-r from-brand-500 via-brand-400 to-brand-600" />

                  <div className="p-8 flex flex-col flex-1">
                    {/* Icon */}
                    <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-brand-50 group-hover:bg-brand-100 transition-colors mb-6">
                      <Icon className="h-7 w-7 text-brand-500" />
                    </div>

                    {/* Title */}
                    <h3 className="text-xl font-bold text-gray-900 mb-4">
                      {pillar.title}
                    </h3>

                    {/* Points */}
                    <ul className="space-y-3 flex-1 mb-6">
                      {pillar.points.map((point, j) => (
                        <li
                          key={j}
                          className="flex items-start gap-2 text-sm text-gray-600"
                        >
                          <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-brand-400 shrink-0" />
                          {point}
                        </li>
                      ))}
                    </ul>

                    {/* Benefit badge */}
                    <div className="mt-auto">
                      <span className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold bg-green-50 text-green-700 border border-green-100">
                        <span className="h-1.5 w-1.5 rounded-full bg-accent-green" />
                        {pillar.benefit}
                      </span>
                    </div>
                  </div>
                </div>
              </FadeInOnScroll>
            );
          })}
        </div>

        {/* Explore link */}
        <FadeInOnScroll delay={0.4}>
          <div className="mt-12 text-center">
            <Link
              href="/solutions"
              className="inline-flex items-center gap-2 text-brand-600 font-semibold hover:text-brand-700 transition-colors group"
            >
              Explore Our Platform
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
