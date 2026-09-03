"use client";

import type { CityData } from "@/data/cities";
import Badge from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

interface CityListProps {
  locations: CityData[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
  className?: string;
}

export default function CityList({ locations, activeName, onActivate, className }: CityListProps) {
  const live = locations.filter((c) => c.status === "active");
  const planned = locations.filter((c) => c.status === "planned");

  return (
    <aside className={cn("flex flex-col", className)} aria-label="Dealer cities">
      <div className="grid grid-cols-2 gap-3 p-5 pb-3 md:p-6 md:pb-4">
        <Stat label="Live cities" value={live.length} tone="brand" />
        <Stat label="Coming next" value={planned.length} tone="amber" />
      </div>

      <div className="max-h-72 overflow-y-auto px-3 pb-4 lg:max-h-none lg:px-4 lg:pb-6">
        <Group title="Live" cities={live} activeName={activeName} onActivate={onActivate} />
        <Group title="Coming next" cities={planned} activeName={activeName} onActivate={onActivate} />
      </div>
    </aside>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone: "brand" | "amber" }) {
  return (
    <div className="rounded-2xl border border-gray-100 bg-gray-50 px-4 py-3">
      <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">{label}</p>
      <p className={cn("mt-1 text-2xl font-bold tabular-nums", tone === "brand" ? "text-brand-600" : "text-amber-600")}>
        {value}
      </p>
    </div>
  );
}

interface GroupProps {
  title: string;
  cities: CityData[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
}

function Group({ title, cities, activeName, onActivate }: GroupProps) {
  if (cities.length === 0) return null;
  return (
    <section className="mt-2 first:mt-0">
      <h3 className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">{title}</h3>
      <ul className="space-y-0.5">
        {cities.map((city) => {
          const isActive = city.name === activeName;
          const isLive = city.status === "active";
          return (
            <li key={city.name}>
              <button
                type="button"
                onMouseEnter={() => onActivate(city.name)}
                onMouseLeave={() => onActivate(null)}
                onFocus={() => onActivate(city.name)}
                onBlur={() => onActivate(null)}
                onClick={() => onActivate(isActive ? null : city.name)}
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
                    isLive ? "bg-brand-500 ring-2 ring-brand-100" : "border-2 border-dashed border-accent-amber bg-white",
                  )}
                />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm font-semibold text-gray-900">{city.name}</span>
                  <span className="block truncate text-xs text-gray-500">{city.state}</span>
                </span>
                <Badge variant={isLive ? "default" : "warning"} className="shrink-0">
                  {isLive ? `${city.dealers ?? 0} dealers` : "Planned"}
                </Badge>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
