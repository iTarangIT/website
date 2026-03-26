"use client";

import { cn } from "@/lib/utils";
import AnimatedCounter from "@/components/shared/AnimatedCounter";

interface StatItem {
  readonly value: number;
  readonly prefix?: string;
  readonly suffix?: string;
  readonly label: string;
}

interface StatsStripProps {
  stats: readonly StatItem[];
  className?: string;
}

export default function StatsStrip({ stats, className }: StatsStripProps) {
  return (
    <section
      className={cn(
        "w-full bg-brand-800 py-10 md:py-14",
        className
      )}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8 md:gap-12">
          {stats.map((stat, i) => (
            <div key={i} className="text-white">
              <AnimatedCounter
                value={stat.value}
                prefix={stat.prefix}
                suffix={stat.suffix}
                label={stat.label}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
