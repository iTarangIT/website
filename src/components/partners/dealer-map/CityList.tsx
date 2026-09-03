"use client";

import Badge from "@/components/ui/Badge";
import type { DealerLocation } from "@/lib/dealers/types";
import { cn } from "@/lib/utils";
import { locationKey } from "./IndiaMap";

interface CityListProps {
  locations: DealerLocation[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
  className?: string;
}

export default function CityList({ locations, activeName, onActivate, className }: CityListProps) {
  const live = locations.filter((l) => l.status === "active");
  const planned = locations.filter((l) => l.status === "planned");
  const dealerTotal = live.reduce((sum, l) => sum + l.dealers, 0);
  const onboardingTotal = locations.reduce((sum, l) => sum + l.onboarding, 0);

  return (
    <aside className={cn("flex flex-col", className)} aria-label="Dealer cities">
      <div className={cn("grid gap-3 p-5 pb-3 md:p-6 md:pb-4", onboardingTotal > 0 ? "grid-cols-3" : "grid-cols-2")}>
        <Stat label="Dealer partners" value={dealerTotal} tone="brand" />
        <Stat label="Cities & towns" value={live.length} tone="brand" />
        {onboardingTotal > 0 && <Stat label="In onboarding" value={onboardingTotal} tone="amber" />}
      </div>

      <div className="max-h-72 overflow-y-auto px-3 pb-4 lg:max-h-[34rem] lg:px-4 lg:pb-6">
        <Group title="Live" locations={live} activeName={activeName} onActivate={onActivate} />
        <Group title="Coming next" locations={planned} activeName={activeName} onActivate={onActivate} />
      </div>
    </aside>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: "brand" | "amber" }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-gray-50 px-3 py-3 md:px-4">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">{label}</p>
      <p className={cn("mt-1 text-2xl font-bold tabular-nums", tone === "brand" ? "text-brand-600" : "text-amber-600")}>
        {value}
      </p>
    </div>
  );
}

interface GroupProps {
  title: string;
  locations: DealerLocation[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
}

function Group({ title, locations, activeName, onActivate }: GroupProps) {
  if (locations.length === 0) return null;
  return (
    <section className="mt-2 first:mt-0">
      <h3 className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{title}</h3>
      <ul className="space-y-0.5">
        {locations.map((location) => {
          const key = locationKey(location);
          const isActive = key === activeName;
          const isLive = location.status === "active";
          return (
            <li key={key}>
              <button
                type="button"
                onMouseEnter={() => onActivate(key)}
                onMouseLeave={() => onActivate(null)}
                onFocus={() => onActivate(key)}
                onBlur={() => onActivate(null)}
                onClick={() => onActivate(isActive ? null : key)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left outline-none transition-colors",
                  "focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-500",
                  isActive ? "bg-brand-50" : "hover:bg-gray-50",
                )}
              >
                <span
                  aria-hidden="true"
                  className={cn(
                    "h-2.5 w-2.5 shrink-0 rounded-full",
                    isLive
                      ? location.approximate
                        ? "border-2 border-brand-500 bg-brand-100"
                        : "bg-brand-500 ring-2 ring-brand-100"
                      : "border-2 border-dashed border-accent-amber bg-white",
                  )}
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold text-gray-900">{location.name}</span>
                  <span className="block truncate text-xs text-gray-500">
                    {location.name === location.state
                      ? "Town not identified yet"
                      : location.approximate
                        ? `${location.state} · approx.`
                        : location.state}
                  </span>
                </span>
                <Badge variant={isLive ? "default" : "warning"} className="shrink-0">
                  {isLive ? `${location.dealers} dealer${location.dealers === 1 ? "" : "s"}` : "Onboarding"}
                </Badge>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
