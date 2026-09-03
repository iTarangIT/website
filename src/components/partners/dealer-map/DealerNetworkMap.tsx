"use client";

import { useState } from "react";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import type { DealerLocation } from "@/lib/dealers/types";
import { cn } from "@/lib/utils";
import IndiaMap from "./IndiaMap";
import CityList from "./CityList";

interface DealerNetworkMapProps {
  /** Pins to plot, already aggregated per town. See `src/lib/dealers/locations.ts`. */
  locations: DealerLocation[];
  className?: string;
}

const plural = (n: number, one: string, many: string) => (n === 1 ? one : many);

export default function DealerNetworkMap({ locations, className }: DealerNetworkMapProps) {
  const [activeName, setActiveName] = useState<string | null>(null);

  const live = locations.filter((l) => l.status === "active");
  const dealerTotal = live.reduce((sum, l) => sum + l.dealers, 0);
  const stateCount = new Set(live.map((l) => l.state)).size;
  const onboardingTotal = locations.reduce((sum, l) => sum + l.onboarding, 0);

  const subtitle =
    `${dealerTotal} active dealer ${plural(dealerTotal, "partner", "partners")} across ` +
    `${live.length} ${plural(live.length, "city or town", "cities and towns")} in ` +
    `${stateCount} ${plural(stateCount, "state", "states")}` +
    (onboardingTotal > 0
      ? `, with ${onboardingTotal} more ${plural(onboardingTotal, "dealer", "dealers")} in onboarding.`
      : ".");

  return (
    <section aria-label="Dealer network" className={cn("bg-surface-warm px-4 pb-16 md:pb-24", className)}>
      <div className="mx-auto max-w-5xl">
        <SectionHeading
          align="left"
          badge="Dealer network"
          title="Where our dealers are"
          subtitle={subtitle}
          className="mb-8 md:mb-10"
        />

        <FadeInOnScroll>
          <div className="grid overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm lg:grid-cols-[1.5fr_1fr]">
            <div className="p-5 md:p-8">
              <IndiaMap locations={locations} activeName={activeName} onActivate={setActiveName} />
              <Legend showOnboarding={onboardingTotal > 0} showApproximate={live.some((l) => l.approximate)} />
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

function Legend({ showOnboarding, showApproximate }: { showOnboarding: boolean; showApproximate: boolean }) {
  return (
    <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-medium text-gray-600">
      <span className="inline-flex items-center gap-2">
        <span aria-hidden="true" className="h-3 w-3 rounded-full bg-brand-500 ring-2 ring-white shadow-sm" />
        Live dealers
      </span>
      {showOnboarding && (
        <span className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-3 w-3 rounded-full border-2 border-dashed border-accent-amber bg-white" />
          In onboarding
        </span>
      )}
      {showApproximate && (
        <span className="inline-flex items-center gap-2">
          <span aria-hidden="true" className="h-3 w-3 rounded-full border-2 border-brand-500 bg-brand-100" />
          Town not yet placed, shown at state level
        </span>
      )}
    </div>
  );
}
