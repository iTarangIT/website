"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import { indiaMap } from "@/data/india-map-paths";
import type { DealerLocation } from "@/lib/dealers/types";
import { projectLatLng } from "@/lib/geo/india-projection";
import { cn } from "@/lib/utils";

interface IndiaMapProps {
  locations: DealerLocation[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
}

interface PlacedLocation {
  location: DealerLocation;
  /** Fraction of the canvas, 0–1, so the pin follows the SVG at any width. */
  fx: number;
  fy: number;
}

export function locationKey(l: DealerLocation): string {
  return `${l.state}|${l.name}`;
}

/** "Prayagraj, Uttar Pradesh", or just the state for a state-level pin. */
export function placeLabel(l: DealerLocation): string {
  return l.name === l.state ? l.state : `${l.name}, ${l.state}`;
}

export function describeLocation(l: DealerLocation): string {
  if (l.status === "active") {
    const live = `${l.dealers} dealer${l.dealers === 1 ? "" : "s"}, live`;
    return l.onboarding > 0 ? `${live}, ${l.onboarding} more in onboarding` : live;
  }
  return `${l.onboarding} in onboarding`;
}

export default function IndiaMap({ locations, activeName, onActivate }: IndiaMapProps) {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.2 });
  const { width, height, states } = indiaMap;

  const liveStates = useMemo(
    () => new Set(locations.filter((l) => l.status === "active").map((l) => l.state)),
    [locations],
  );

  const placed = useMemo<PlacedLocation[]>(
    () =>
      locations.map((location) => {
        const [x, y] = projectLatLng(location.lat, location.lng);
        return { location, fx: x / width, fy: y / height };
      }),
    [locations, width, height],
  );

  const active = placed.find((p) => locationKey(p.location) === activeName) ?? null;

  return (
    <div ref={ref} className="relative w-full" style={{ aspectRatio: `${width} / ${height}` }}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="absolute inset-0 h-full w-full"
        aria-hidden="true"
        focusable="false"
      >
        {states.map((state) => (
          <path
            key={state.id}
            d={state.d}
            strokeWidth={1}
            strokeLinejoin="round"
            className={cn(
              "stroke-white transition-colors duration-300",
              liveStates.has(state.name) ? "fill-brand-100" : "fill-brand-50 hover:fill-brand-100/70",
            )}
          />
        ))}
      </svg>

      {placed.map((p, i) => (
        <Pin
          key={locationKey(p.location)}
          placed={p}
          index={i}
          revealed={inView}
          isActive={locationKey(p.location) === activeName}
          onActivate={onActivate}
        />
      ))}

      {active && <Tooltip placed={active} />}
    </div>
  );
}

interface PinProps {
  placed: PlacedLocation;
  index: number;
  revealed: boolean;
  isActive: boolean;
  onActivate: (name: string | null) => void;
}

function Pin({ placed, index, revealed, isActive, onActivate }: PinProps) {
  const { location, fx, fy } = placed;
  const key = locationKey(location);
  const live = location.status === "active";
  // Permanent labels only where they earn their space: multi-dealer towns.
  const showLabel = isActive || (live && location.dealers > 1);

  return (
    <motion.div
      className="absolute h-0 w-0"
      style={{ left: `${fx * 100}%`, top: `${fy * 100}%` }}
      initial={{ scale: 0, opacity: 0 }}
      animate={revealed ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 18, delay: revealed ? index * 0.04 : 0 }}
    >
      <button
        type="button"
        aria-label={`${placeLabel(location)} — ${describeLocation(location)}${location.approximate ? " (shown at state level)" : ""}`}
        className="absolute left-0 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full p-2 outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        onMouseEnter={() => onActivate(key)}
        onMouseLeave={() => onActivate(null)}
        onFocus={() => onActivate(key)}
        onBlur={() => onActivate(null)}
        onClick={() => onActivate(isActive ? null : key)}
      >
        <span
          className={cn(
            "relative block transition-transform duration-200",
            live ? "h-3 w-3" : "h-2.5 w-2.5",
            isActive && "scale-125",
          )}
        >
          {live && !location.approximate && (
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full bg-brand-400/40 animate-pin-ping motion-reduce:animate-none"
            />
          )}
          <span
            className={cn(
              "absolute inset-0 rounded-full transition-shadow duration-200",
              live
                ? location.approximate
                  ? "border-2 border-brand-500 bg-brand-100"
                  : "bg-brand-500 ring-2 ring-white shadow-md"
                : "border-2 border-dashed border-accent-amber bg-white",
              isActive && "shadow-[0_0_0_6px_rgba(19,143,198,0.18)]",
            )}
          />
        </span>
      </button>

      {showLabel && (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute left-2.5 top-0 -translate-y-1/2 whitespace-nowrap rounded-md bg-white/85 px-1.5 py-0.5 text-[11px] font-semibold leading-tight text-gray-800 shadow-sm backdrop-blur-[2px]"
        >
          {location.name}
        </span>
      )}
    </motion.div>
  );
}

function Tooltip({ placed }: { placed: PlacedLocation }) {
  const { location, fx, fy } = placed;
  const below = fy < 0.18;
  const align = fx > 0.78 ? "right" : fx < 0.12 ? "left" : "center";

  return (
    <motion.div
      key={locationKey(location)}
      role="tooltip"
      initial={{ opacity: 0, y: below ? -4 : 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className={cn(
        "pointer-events-none absolute z-10 rounded-xl bg-gray-900 px-3 py-2 text-xs text-white shadow-lg",
        below ? "translate-y-0" : "-translate-y-full",
        align === "center" && "-translate-x-1/2",
        align === "right" && "-translate-x-full",
      )}
      style={{
        left: `${fx * 100}%`,
        top: below ? `calc(${fy * 100}% + 14px)` : `calc(${fy * 100}% - 14px)`,
      }}
    >
      <p className="font-semibold">{location.name}</p>
      <p className="mt-0.5 text-gray-300">
        {location.name === location.state ? describeLocation(location) : `${location.state} · ${describeLocation(location)}`}
      </p>
      {location.approximate && (
        <p className="mt-0.5 text-gray-400">
          {location.name === location.state ? "Town not identified yet, shown at state level" : "Shown at state level"}
        </p>
      )}
    </motion.div>
  );
}
