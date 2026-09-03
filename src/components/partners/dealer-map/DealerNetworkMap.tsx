"use client";

import { useMemo, useState } from "react";
import SectionHeading from "@/components/shared/SectionHeading";
import FadeInOnScroll from "@/components/shared/FadeInOnScroll";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import type { DealerLocation } from "@/lib/dealers/types";
import { cn } from "@/lib/utils";
import DealerMapCard from "./DealerMapCard";
import DealerSearch, { IDLE_SEARCH, type SearchState } from "./DealerSearch";

interface DealerNetworkMapProps {
  /** Pins to plot, already aggregated per town. See `src/lib/dealers/locations.ts`. */
  locations: DealerLocation[];
  className?: string;
}

const RADIUS_KM = 150;

const plural = (n: number, one: string, many: string) => (n === 1 ? one : many);

export default function DealerNetworkMap({ locations, className }: DealerNetworkMapProps) {
  const [expanded, setExpanded] = useState(false);
  const [search, setSearch] = useState<SearchState>(IDLE_SEARCH);

  const live = locations.filter((l) => l.status === "active");
  const dealerTotal = live.reduce((sum, l) => sum + l.dealers, 0);
  const stateCount = new Set(live.map((l) => l.state)).size;
  const onboardingTotal = locations.reduce((sum, l) => sum + l.onboarding, 0);
  const hasMap = locations.length > 0;

  const subtitle = hasMap
    ? `${dealerTotal} active dealer ${plural(dealerTotal, "partner", "partners")} across ` +
      `${live.length} ${plural(live.length, "city or town", "cities and towns")} in ` +
      `${stateCount} ${plural(stateCount, "state", "states")}` +
      (onboardingTotal > 0
        ? `, with ${onboardingTotal} more ${plural(onboardingTotal, "dealer", "dealers")} in onboarding.`
        : ".")
    : "Search for the dealer nearest you by pin code, town or address.";

  const result = search.status === "done" ? search.result : null;

  // A new nonce per completed search is what makes searching the same place
  // twice move the map again; useMemo keeps it stable between renders.
  const focusRequest = useMemo(() => {
    const target = result?.dealers[0] ?? result?.resolved;
    if (!target) return null;
    return { lat: target.lat, lng: target.lng, nonce: Date.now() };
  }, [result]);

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

        {/* Outside the map's own guard on purpose: if the CRM is unreachable the
            map has nothing to draw, but the search still answers. */}
        <DealerSearch state={search} onChange={setSearch} />

        {search.status === "error" && search.message && (
          <p role="alert" className="mb-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800">
            {search.message}
          </p>
        )}

        {hasMap && (
          <FadeInOnScroll>
            <DealerMapCard
              locations={locations}
              onExpand={() => setExpanded(true)}
              search={result}
              radiusKm={RADIUS_KM}
              onClearSearch={() => setSearch(IDLE_SEARCH)}
              focusRequest={focusRequest}
            />
          </FadeInOnScroll>
        )}
      </div>

      {/* The expanded view is a fresh card instance: its own zoom starts at rest
          and the page copy behind it stays exactly where it was. */}
      <Dialog open={expanded} onOpenChange={setExpanded}>
        <DialogContent className="w-[calc(100%-1.5rem)] gap-3 bg-white p-4 sm:max-w-[min(96vw,80rem)] sm:p-6">
          <DialogTitle className="pr-10 text-base font-semibold text-gray-900">Dealer network map</DialogTitle>
          <DialogDescription className="sr-only">{subtitle}</DialogDescription>
          <DealerMapCard
            locations={locations}
            expanded
            search={result}
            radiusKm={RADIUS_KM}
            onClearSearch={() => setSearch(IDLE_SEARCH)}
            focusRequest={focusRequest}
            className="shadow-none"
          />
        </DialogContent>
      </Dialog>
    </section>
  );
}
