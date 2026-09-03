"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Maximize2, Minus, Plus, RotateCcw } from "lucide-react";
import { useInView } from "react-intersection-observer";
import { indiaMap } from "@/data/india-map-paths";
import type { DealerLocation } from "@/lib/dealers/types";
import { projectLatLng } from "@/lib/geo/india-projection";
import { cn } from "@/lib/utils";
import { useMapViewport } from "./useMapViewport";

interface IndiaMapProps {
  locations: DealerLocation[];
  activeName: string | null;
  onActivate: (name: string | null) => void;
  /** Shows the expand control; the parent decides what "expand" opens. */
  onExpand?: () => void;
  /** Wrapper around the map frame, e.g. to cap its width in a dialog. */
  className?: string;
  style?: CSSProperties;
}

interface PlacedLocation {
  location: DealerLocation;
  /** Fraction of the canvas, 0–1, so the pin follows the SVG at any width. */
  fx: number;
  fy: number;
}

/**
 * Zoom levels at which pins earn a permanent label. At rest the map names the
 * states instead; one zoom step (STEP is 1.6) brings the towns in. The 1.5 is
 * deliberately just under that step so the comparison is not an equality test
 * against a floating-point product.
 */
const LABEL_LIVE_ZOOM = 1.5;
const LABEL_ONBOARDING_ZOOM = 3.6;

/** Breathing room either side of a state name before it counts as fitting. */
const LABEL_PADDING_PX = 8;
/** Below this screen gap a state name and a dealer pin would print over each other. */
const LABEL_PIN_GAP_PX = 30;

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

/**
 * Position inside the frame for a canvas fraction, following the zoom. Pins
 * and the tooltip live outside the scaled stage, so they keep their size while
 * the outline grows underneath them.
 */
function framePosition(fx: number, fy: number): CSSProperties {
  return {
    left: `calc(var(--map-x) + ${fx * 100}% * var(--map-k))`,
    top: `calc(var(--map-y) + ${fy * 100}% * var(--map-k))`,
  };
}

/**
 * State names, written at each unit's pole of inaccessibility.
 *
 * Whether a name fits cannot be decided when the map data is generated: the
 * same frame renders at roughly 300 px on a phone, 530 px inline and 755 px in
 * the expanded dialog, and the text is a fixed pixel size in all three. So the
 * build ships geometry only — the anchor and the clear radius around it, in
 * canvas units — and the decision is made here against the measured frame.
 */
function StateLabels({ zoom, framePx, pins }: { zoom: number; framePx: number; pins: PlacedLocation[] }) {
  const { width, height, states } = indiaMap;
  const nodes = useRef(new Map<string, HTMLSpanElement>());
  const [widths, setWidths] = useState<Map<string, number>>(new Map());

  // Measured before paint, so nothing flashes on at first render. Webfonts can
  // land later and change every width, hence the second pass.
  useLayoutEffect(() => {
    const measure = () => {
      const next = new Map<string, number>();
      nodes.current.forEach((el, id) => next.set(id, el.offsetWidth));
      setWidths(next);
    };
    measure();
    void document.fonts?.ready.then(measure).catch(() => undefined);
  }, []);

  // Screen pixels per canvas unit: the exchange rate the fit test needs.
  const pxPerUnit = framePx > 0 ? (framePx / width) * zoom : 0;

  return (
    <>
      {states.map((state) => {
        const [lx, ly, clear] = state.label;
        const measured = widths.get(state.id);
        const fits = measured != null && pxPerUnit > 0 && measured + LABEL_PADDING_PX <= 2 * clear * pxPerUnit;
        // A pin on the anchor wins. Delhi's clear radius is 3.3 units and the
        // NCR pin sits 1.8 from it, so without this the name prints through it.
        const clashes =
          fits &&
          pins.some((p) => Math.hypot(p.fx * width - lx, p.fy * height - ly) * pxPerUnit < LABEL_PIN_GAP_PX);

        return (
          <span
            key={state.id}
            ref={(el) => {
              if (el) nodes.current.set(state.id, el);
              else nodes.current.delete(state.id);
            }}
            aria-hidden="true"
            className={cn(
              "dealer-map-pin pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 whitespace-nowrap",
              "text-[10px] font-semibold uppercase tracking-[0.12em] text-brand-800 transition-opacity duration-300",
              fits && !clashes ? "opacity-100" : "opacity-0",
            )}
            style={framePosition(lx / width, ly / height)}
          >
            {state.name}
          </span>
        );
      })}
    </>
  );
}

export default function IndiaMap({ locations, activeName, onActivate, onExpand, className, style }: IndiaMapProps) {
  const { ref: inViewRef, inView } = useInView({ triggerOnce: true, threshold: 0.2 });
  const { width, height, states } = indiaMap;
  const viewport = useMapViewport();
  const { view, zoomed } = viewport;

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

  // The rendered frame width decides which state names fit. Each instance
  // measures its own, so the inline card and the expanded dialog differ freely.
  const [framePx, setFramePx] = useState(0);
  const { frameRef } = viewport;
  useEffect(() => {
    const el = frameRef.current;
    if (!el) return;
    setFramePx(el.getBoundingClientRect().width);
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width;
      if (w) setFramePx(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [frameRef]);

  const frameVars = {
    "--map-k": String(view.k),
    "--map-x": `${view.x * 100}%`,
    "--map-y": `${view.y * 100}%`,
  } as CSSProperties;

  return (
    <div ref={inViewRef} className={cn("relative", className)} style={style}>
      <div
        ref={viewport.frameRef}
        {...viewport.frameHandlers}
        tabIndex={0}
        role="group"
        aria-label="Interactive map of dealer locations. Press plus or minus to zoom, arrow keys to pan, 0 to reset."
        data-animate={viewport.animating ? "true" : "false"}
        className={cn(
          "dealer-map relative w-full select-none rounded-2xl outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2",
          zoomed ? "overflow-hidden" : "overflow-visible",
          zoomed && (viewport.dragging ? "cursor-grabbing" : "cursor-grab"),
        )}
        style={{ aspectRatio: `${width} / ${height}`, touchAction: zoomed ? "none" : "pan-y", ...frameVars }}
      >
        <div
          className="dealer-map-stage absolute inset-0 origin-top-left will-change-transform"
          style={{ transform: "translate(var(--map-x), var(--map-y)) scale(var(--map-k))" }}
        >
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
                strokeLinejoin="round"
                // Keep the hairline one screen pixel wide at every zoom.
                strokeWidth={1 / view.k}
                className={cn(
                  "stroke-white transition-colors duration-300",
                  liveStates.has(state.name) ? "fill-brand-100" : "fill-brand-50 hover:fill-brand-100/70",
                )}
              />
            ))}
          </svg>
        </div>

        {/* Before the pins, so a pin and its town label always paint on top. */}
        <StateLabels zoom={view.k} framePx={framePx} pins={placed} />

        {placed.map((p, i) => (
          <Pin
            key={locationKey(p.location)}
            placed={p}
            index={i}
            revealed={inView}
            zoom={view.k}
            isActive={locationKey(p.location) === activeName}
            onActivate={onActivate}
          />
        ))}

        {active && <Tooltip placed={active} />}

        <ZoomControls viewport={viewport} onExpand={onExpand} />

        <AnimatePresence>
          {viewport.hint && (
            <motion.div
              key="hint"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              transition={{ duration: 0.18 }}
              className="pointer-events-none absolute bottom-3 left-1/2 z-20 -translate-x-1/2 whitespace-nowrap rounded-full bg-gray-900/85 px-3 py-1 text-[11px] font-medium text-white shadow-md"
              role="status"
            >
              {viewport.hint}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ZoomControls({ viewport, onExpand }: { viewport: ReturnType<typeof useMapViewport>; onExpand?: () => void }) {
  const button =
    "flex h-8 w-8 items-center justify-center rounded-lg border border-gray-200 bg-white/95 text-gray-700 shadow-sm transition-colors hover:bg-gray-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-white/95";
  return (
    <div data-map-controls className="absolute right-2 top-2 z-20 flex flex-col gap-1 md:right-3 md:top-3">
      <button type="button" aria-label="Zoom in" className={button} onClick={viewport.zoomIn} disabled={!viewport.canZoomIn}>
        <Plus className="h-4 w-4" />
      </button>
      <button type="button" aria-label="Zoom out" className={button} onClick={viewport.zoomOut} disabled={!viewport.canZoomOut}>
        <Minus className="h-4 w-4" />
      </button>
      <button type="button" aria-label="Reset zoom" className={button} onClick={viewport.reset} disabled={!viewport.zoomed}>
        <RotateCcw className="h-4 w-4" />
      </button>
      {onExpand && (
        <button type="button" aria-label="Expand map" className={cn(button, "mt-1")} onClick={onExpand}>
          <Maximize2 className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

interface PinProps {
  placed: PlacedLocation;
  index: number;
  revealed: boolean;
  zoom: number;
  isActive: boolean;
  onActivate: (name: string | null) => void;
}

function Pin({ placed, index, revealed, zoom, isActive, onActivate }: PinProps) {
  const { location, fx, fy } = placed;
  const key = locationKey(location);
  const live = location.status === "active";
  // At rest the map belongs to the state names; the first zoom step hands it to
  // the towns. A hovered or focused pin always names itself, at any zoom.
  const showLabel =
    isActive || (live && zoom >= LABEL_LIVE_ZOOM) || (!live && zoom >= LABEL_ONBOARDING_ZOOM);

  return (
    <motion.div
      className="dealer-map-pin absolute h-0 w-0"
      style={framePosition(fx, fy)}
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
  const pos = framePosition(fx, fy);

  return (
    <motion.div
      key={locationKey(location)}
      role="tooltip"
      initial={{ opacity: 0, y: below ? -4 : 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className={cn(
        "dealer-map-pin pointer-events-none absolute z-10 rounded-xl bg-gray-900 px-3 py-2 text-xs text-white shadow-lg",
        below ? "translate-y-0" : "-translate-y-full",
        align === "center" && "-translate-x-1/2",
        align === "right" && "-translate-x-full",
      )}
      style={{
        left: pos.left,
        top: below ? `calc(${pos.top} + 14px)` : `calc(${pos.top} - 14px)`,
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
