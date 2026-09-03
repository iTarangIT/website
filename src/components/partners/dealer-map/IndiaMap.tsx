"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useInView } from "react-intersection-observer";
import type { CityData } from "@/data/cities";
import { indiaMap } from "@/data/india-map-paths";
import { projectLatLng } from "@/lib/geo/india-projection";
import { cn } from "@/lib/utils";

interface IndiaMapProps {
  locations: CityData[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
}

interface PlacedCity {
  city: CityData;
  /** Fraction of the canvas, 0–1, so the pin follows the SVG at any width. */
  fx: number;
  fy: number;
}

function describeCity(city: CityData): string {
  return city.status === "active" ? `${city.dealers ?? 0} dealers, live` : "planned";
}

export default function IndiaMap({ locations, activeName, onActivate }: IndiaMapProps) {
  const { ref, inView } = useInView({ triggerOnce: true, threshold: 0.2 });
  const { width, height, states } = indiaMap;

  const liveStates = useMemo(
    () => new Set(locations.filter((c) => c.status === "active").map((c) => c.state)),
    [locations],
  );

  const placed = useMemo<PlacedCity[]>(
    () =>
      locations.map((city) => {
        const [x, y] = projectLatLng(city.lat, city.lng);
        return { city, fx: x / width, fy: y / height };
      }),
    [locations, width, height],
  );

  const active = placed.find((p) => p.city.name === activeName) ?? null;

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
          key={p.city.name}
          placed={p}
          index={i}
          revealed={inView}
          isActive={p.city.name === activeName}
          onActivate={onActivate}
        />
      ))}

      {active && <Tooltip placed={active} />}
    </div>
  );
}

interface PinProps {
  placed: PlacedCity;
  index: number;
  revealed: boolean;
  isActive: boolean;
  onActivate: (name: string | null) => void;
}

function Pin({ placed, index, revealed, isActive, onActivate }: PinProps) {
  const { city, fx, fy } = placed;
  const live = city.status === "active";
  const showLabel = live || isActive;

  return (
    <motion.div
      className="absolute h-0 w-0"
      style={{ left: `${fx * 100}%`, top: `${fy * 100}%` }}
      initial={{ scale: 0, opacity: 0 }}
      animate={revealed ? { scale: 1, opacity: 1 } : { scale: 0, opacity: 0 }}
      transition={{ type: "spring", stiffness: 260, damping: 18, delay: revealed ? index * 0.06 : 0 }}
    >
      <button
        type="button"
        aria-label={`${city.name}, ${city.state} — ${describeCity(city)}`}
        className="absolute left-0 top-0 -translate-x-1/2 -translate-y-1/2 rounded-full p-2 outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        onMouseEnter={() => onActivate(city.name)}
        onMouseLeave={() => onActivate(null)}
        onFocus={() => onActivate(city.name)}
        onBlur={() => onActivate(null)}
        onClick={() => onActivate(isActive ? null : city.name)}
      >
        <span
          className={cn(
            "relative block transition-transform duration-200",
            live ? "h-3 w-3" : "h-2.5 w-2.5",
            isActive && "scale-125",
          )}
        >
          {live && (
            <span
              aria-hidden="true"
              className="absolute inset-0 rounded-full bg-brand-400/40 animate-pin-ping motion-reduce:animate-none"
            />
          )}
          <span
            className={cn(
              "absolute inset-0 rounded-full transition-shadow duration-200",
              live
                ? "bg-brand-500 ring-2 ring-white shadow-md"
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
          {city.name}
        </span>
      )}
    </motion.div>
  );
}

function Tooltip({ placed }: { placed: PlacedCity }) {
  const { city, fx, fy } = placed;
  const below = fy < 0.18;
  const align = fx > 0.78 ? "right" : fx < 0.12 ? "left" : "center";

  return (
    <motion.div
      key={city.name}
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
      <p className="font-semibold">{city.name}</p>
      <p className="mt-0.5 text-gray-300">
        {city.state} · {city.status === "active" ? `${city.dealers ?? 0} dealers` : "Planned"}
      </p>
    </motion.div>
  );
}
