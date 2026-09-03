"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent as ReactKeyboardEvent,
  type MouseEvent as ReactMouseEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

/**
 * Zoom/pan state for the dealer map.
 *
 * `k` is the zoom factor. `x` and `y` are the stage offset as fractions of the
 * frame size (0 at rest, down to `1 - k` when panned fully), so the same
 * numbers drive the SVG transform and every pin's `left`/`top` through CSS
 * custom properties, and nothing depends on the frame's pixel size.
 */
export interface MapView {
  k: number;
  x: number;
  y: number;
}

export const MIN_ZOOM = 1;
export const MAX_ZOOM = 8;
const STEP = 1.6;
const KEY_PAN = 0.12;
const DRAG_THRESHOLD_PX = 3;
const HINT_MS = 1800;

const REST: MapView = { k: 1, x: 0, y: 0 };

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/** Keep the stage covering the frame: no blank strips at any zoom. */
export function clampView(v: MapView): MapView {
  const k = clamp(v.k, MIN_ZOOM, MAX_ZOOM);
  return { k, x: clamp(v.x, 1 - k, 0), y: clamp(v.y, 1 - k, 0) };
}

/** Multiply the zoom by `factor` while the frame point (px, py) stays put. */
export function zoomAt(v: MapView, factor: number, px: number, py: number): MapView {
  const k = clamp(v.k * factor, MIN_ZOOM, MAX_ZOOM);
  const r = k / v.k;
  return clampView({ k, x: px - (px - v.x) * r, y: py - (py - v.y) * r });
}

interface Point {
  x: number;
  y: number;
}

interface Gesture {
  /** Last position of the single active pointer, as frame fractions. */
  last: Point;
  /** Set once movement passes the drag threshold; a tap is not a drag. */
  moved: boolean;
  pinch?: { startDist: number; startMid: Point; startView: MapView };
}

export function useMapViewport() {
  const frameRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<MapView>(REST);
  const [view, setViewState] = useState<MapView>(REST);
  const [animating, setAnimating] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [hint, setHint] = useState<string | null>(null);

  const pointers = useRef(new Map<number, { clientX: number; clientY: number }>());
  const gesture = useRef<Gesture | null>(null);
  const hintTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const setView = useCallback((next: MapView, animate: boolean) => {
    const v = clampView(next);
    viewRef.current = v;
    setAnimating(animate);
    setViewState(v);
  }, []);

  /** Frame-relative fractions for a client position. */
  const toFraction = useCallback((clientX: number, clientY: number): Point => {
    const rect = frameRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0 || rect.height === 0) return { x: 0.5, y: 0.5 };
    return { x: (clientX - rect.left) / rect.width, y: (clientY - rect.top) / rect.height };
  }, []);

  const showHint = useCallback((text: string) => {
    setHint(text);
    if (hintTimer.current) clearTimeout(hintTimer.current);
    hintTimer.current = setTimeout(() => setHint(null), HINT_MS);
  }, []);

  const zoomIn = useCallback(() => setView(zoomAt(viewRef.current, STEP, 0.5, 0.5), true), [setView]);
  const zoomOut = useCallback(() => setView(zoomAt(viewRef.current, 1 / STEP, 0.5, 0.5), true), [setView]);
  const reset = useCallback(() => setView(REST, true), [setView]);

  // Ctrl/⌘ + wheel (and trackpad pinch, which browsers report the same way)
  // zooms around the cursor. A plain wheel keeps scrolling the page: the map
  // must never trap the scroll. Registered natively because React marks wheel
  // listeners passive, and passive listeners cannot cancel the browser zoom.
  useEffect(() => {
    const el = frameRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
        const p = toFraction(e.clientX, e.clientY);
        setView(zoomAt(viewRef.current, Math.exp(-delta * 0.0018), p.x, p.y), false);
      } else if (viewRef.current.k > 1) {
        showHint("Ctrl + scroll to zoom · drag to pan");
      }
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [setView, showHint, toFraction]);

  useEffect(
    () => () => {
      if (hintTimer.current) clearTimeout(hintTimer.current);
    },
    [],
  );

  const endGesture = useCallback(() => {
    gesture.current = null;
    setDragging(false);
    window.removeEventListener("pointermove", onWindowMove);
    window.removeEventListener("pointerup", onWindowUp);
    window.removeEventListener("pointercancel", onWindowUp);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const onWindowMove = useCallback(
    (e: PointerEvent) => {
      const known = pointers.current.get(e.pointerId);
      const g = gesture.current;
      if (!known || !g) return;
      pointers.current.set(e.pointerId, { clientX: e.clientX, clientY: e.clientY });
      const rect = frameRef.current?.getBoundingClientRect();
      if (!rect) return;

      if (pointers.current.size >= 2 && g.pinch) {
        const [a, b] = Array.from(pointers.current.values());
        const dist = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY) || 1;
        const mid = toFraction((a.clientX + b.clientX) / 2, (a.clientY + b.clientY) / 2);
        const zoomed = zoomAt(g.pinch.startView, dist / g.pinch.startDist, g.pinch.startMid.x, g.pinch.startMid.y);
        g.moved = true;
        setView({ k: zoomed.k, x: zoomed.x + (mid.x - g.pinch.startMid.x), y: zoomed.y + (mid.y - g.pinch.startMid.y) }, false);
        return;
      }

      if (viewRef.current.k <= 1) return; // at rest a single finger scrolls the page
      const now = toFraction(e.clientX, e.clientY);
      const dxPx = (now.x - g.last.x) * rect.width;
      const dyPx = (now.y - g.last.y) * rect.height;
      if (!g.moved && Math.hypot(dxPx, dyPx) < DRAG_THRESHOLD_PX) return;
      if (!g.moved) {
        g.moved = true;
        setDragging(true);
      }
      const v = viewRef.current;
      setView({ k: v.k, x: v.x + (now.x - g.last.x), y: v.y + (now.y - g.last.y) }, false);
      g.last = now;
    },
    [setView, toFraction],
  );

  const onWindowUp = useCallback(
    (e: PointerEvent) => {
      pointers.current.delete(e.pointerId);
      const g = gesture.current;
      if (!g) return;
      if (pointers.current.size === 0) {
        endGesture();
        return;
      }
      // One finger lifted after a pinch: continue as a plain drag from the other one.
      const [rest] = Array.from(pointers.current.values());
      g.pinch = undefined;
      g.last = toFraction(rest.clientX, rest.clientY);
    },
    [endGesture, toFraction],
  );

  const onPointerDown = useCallback(
    (e: ReactPointerEvent<HTMLDivElement>) => {
      if (e.pointerType === "mouse" && e.button !== 0) return;
      if ((e.target as Element).closest("[data-map-controls]")) return;
      pointers.current.set(e.pointerId, { clientX: e.clientX, clientY: e.clientY });
      setAnimating(false);

      if (pointers.current.size === 1) {
        gesture.current = { last: toFraction(e.clientX, e.clientY), moved: false };
        window.addEventListener("pointermove", onWindowMove);
        window.addEventListener("pointerup", onWindowUp);
        window.addEventListener("pointercancel", onWindowUp);
      } else if (pointers.current.size === 2 && gesture.current) {
        const [a, b] = Array.from(pointers.current.values());
        gesture.current.pinch = {
          startDist: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY) || 1,
          startMid: toFraction((a.clientX + b.clientX) / 2, (a.clientY + b.clientY) / 2),
          startView: viewRef.current,
        };
      }
    },
    [onWindowMove, onWindowUp, toFraction],
  );

  const onDoubleClick = useCallback(
    (e: ReactMouseEvent<HTMLDivElement>) => {
      if ((e.target as Element).closest("button")) return;
      const p = toFraction(e.clientX, e.clientY);
      setView(zoomAt(viewRef.current, STEP, p.x, p.y), true);
    },
    [setView, toFraction],
  );

  const onKeyDown = useCallback(
    (e: ReactKeyboardEvent<HTMLDivElement>) => {
      if (e.target !== e.currentTarget) return; // pins and controls handle their own keys
      const v = viewRef.current;
      const pan = (dx: number, dy: number) => setView({ k: v.k, x: v.x + dx, y: v.y + dy }, true);
      switch (e.key) {
        case "+":
        case "=":
          zoomIn();
          break;
        case "-":
        case "_":
          zoomOut();
          break;
        case "0":
          reset();
          break;
        case "ArrowLeft":
          pan(KEY_PAN, 0);
          break;
        case "ArrowRight":
          pan(-KEY_PAN, 0);
          break;
        case "ArrowUp":
          pan(0, KEY_PAN);
          break;
        case "ArrowDown":
          pan(0, -KEY_PAN);
          break;
        default:
          return;
      }
      e.preventDefault();
    },
    [reset, setView, zoomIn, zoomOut],
  );

  useEffect(() => endGesture, [endGesture]);

  return {
    frameRef,
    view,
    animating,
    dragging,
    hint,
    zoomed: view.k > 1 + 1e-6,
    canZoomIn: view.k < MAX_ZOOM - 1e-6,
    canZoomOut: view.k > MIN_ZOOM + 1e-6,
    zoomIn,
    zoomOut,
    reset,
    frameHandlers: { onPointerDown, onDoubleClick, onKeyDown },
  };
}
