"use client";

import { useState } from "react";
import type { CityData } from "@/data/cities";
import { deckMetrics } from "@/data/metrics";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { cn } from "@/lib/utils";
import IndiaMap from "./IndiaMap";
import CityList from "./CityList";

interface DealerNetworkMapProps {
  /**
   * Cities to plot. Today this is `cities` from `src/data/cities.ts`; a
   * database-backed source can pass the same shape without touching the map.
   */
  locations: CityData[];
  className?: string;
}

export default function DealerNetworkMap({ locations, className }: DealerNetworkMapProps) {
  const [activeName, setActiveName] = useState<string | null>(null);
  const liveCount = locations.filter((c) => c.status === "active").length;
  const plannedCount = locations.length - liveCount;
  const plural = (n: number) => (n === 1 ? "city" : "cities");

  return (
    <section aria-label="Dealer network" className={cn("bg-surface-warm px-4 pb-16 md:pb-24", className)}>
      <div className="mx-auto max-w-5xl">
        <SectionHeading
          align="left"
          badge="Dealer network"
          title="Where our dealers are"
          subtitle={`${deckMetrics.dealersOnboardedDisplay} dealers onboarded across ${liveCount} live ${plural(liveCount)}, with ${plannedCount} more ${plural(plannedCount)} mapped for the next phase.`}
          className="mb-8 md:mb-10"
        />

        <FadeInOnScroll>
          <div className="grid overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm lg:grid-cols-[1.5fr_1fr]">
            <div className="p-5 md:p-8">
              <IndiaMap locations={locations} activeName={activeName} onActivate={setActiveName} />
              <Legend />
            </div>
            <CityList
              locations={locations}
              activeName={activeName}
              onActivate={setActiveName}
              className="border-t border-gray-100 lg:border-l lg:border-t-0"
            />
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}

function Legend() {
  return (
    <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium text-gray-600">
      <span className="inline-flex items-center gap-2">
        <span aria-hidden="true" className="h-3 w-3 rounded-full bg-brand-500 ring-2 ring-white shadow-sm" />
        Live dealers
      </span>
      <span className="inline-flex items-center gap-2">
        <span aria-hidden="true" className="h-3 w-3 rounded-full border-2 border-dashed border-accent-amber bg-white" />
        Coming next
      </span>
    </div>
  );
}
