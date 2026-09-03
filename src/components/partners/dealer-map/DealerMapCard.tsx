"use client";

import { useEffect, useState } from "react";
import { indiaMap } from "@/data/india-map-paths";
import type { DealerLocation } from "@/lib/dealers/types";
import type { NearestResult } from "@/lib/dealers/nearest";
import { cn } from "@/lib/utils";
import CityList from "./CityList";
import IndiaMap from "./IndiaMap";
import NearestDealerList from "./NearestDealerList";

interface DealerMapCardProps {
  locations: DealerLocation[];
  /** Full-screen layout: the map takes the height available, the list sits beside it. */
  expanded?: boolean;
  onExpand?: () => void;
  /** A finished search: the side panel shows its results instead of the cities. */
  search?: NearestResult | null;
  radiusKm?: number;
  onClearSearch?: () => void;
  focusRequest?: { lat: number; lng: number; nonce: number } | null;
  className?: string;
}

/** The white card: map, legend and the synced city list. Used inline and in the expanded dialog. */
export default function DealerMapCard({
  locations,
  expanded = false,
  onExpand,
  search = null,
  radiusKm = 150,
  onClearSearch,
  focusRequest = null,
  className,
}: DealerMapCardProps) {
  const [activeName, setActiveName] = useState<string | null>(null);
  const live = locations.filter((l) => l.status === "active");
  const onboardingTotal = locations.reduce((sum, l) => sum + l.onboarding, 0);

  // Highlight the pin the top result sits on. Both sides resolve addresses with
  // the same resolver, so the key a dealer produces is the key the map drew.
  const top = search?.dealers[0];
  const topKey = top ? `${top.state}|${top.town}` : null;
  useEffect(() => {
    if (topKey) setActiveName(topKey);
  }, [topKey]);

  return (
    <div
      className={cn(
        "grid overflow-hidden rounded-3xl border border-gray-100 bg-white shadow-sm",
        expanded ? "lg:grid-cols-[minmax(0,1fr)_19rem]" : "lg:grid-cols-[1.5fr_1fr]",
        className,
      )}
    >
      <div className={cn("min-w-0", expanded ? "p-4 md:p-6" : "p-5 md:p-8")}>
        <IndiaMap
          locations={locations}
          activeName={activeName}
          onActivate={setActiveName}
          onExpand={onExpand}
          focusRequest={focusRequest}
          className="mx-auto w-full"
          // In the dialog the viewport height is the limit: cap the width so the
          // frame keeps its aspect ratio instead of letterboxing the outline.
          style={expanded ? { maxWidth: `calc((100vh - 14rem) * ${indiaMap.width / indiaMap.height})` } : undefined}
        />
        <Legend showOnboarding={onboardingTotal > 0} showApproximate={live.some((l) => l.approximate)} />
      </div>
      {search ? (
        <NearestDealerList
          result={search}
          radiusKm={radiusKm}
          activeName={activeName}
          onActivate={setActiveName}
          onClear={() => onClearSearch?.()}
          className={cn("border-t border-gray-100 lg:border-l lg:border-t-0", expanded && "lg:max-h-[calc(100vh-8rem)] lg:overflow-hidden")}
        />
      ) : (
        <CityList
          locations={locations}
          activeName={activeName}
          onActivate={setActiveName}
          className={cn("border-t border-gray-100 lg:border-l lg:border-t-0", expanded && "lg:max-h-[calc(100vh-8rem)] lg:overflow-hidden")}
        />
      )}
    </div>
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
      <span className="ml-auto hidden text-gray-400 md:inline">Ctrl + scroll or pinch to zoom · drag to pan</span>
    </div>
  );
}
