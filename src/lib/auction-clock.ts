"use client";

import { useEffect, useState } from "react";

// Live countdown hook — ticks every second. Given minutes-from-now at mount, returns remaining seconds.
export function useCountdown(offsetMinutesFromMount: number, pausedOverride?: boolean): {
  remainingSeconds: number;
  formatted: string;
  expired: boolean;
} {
  const [mountedAt] = useState(() => Date.now());
  const [now, setNow] = useState(mountedAt);

  useEffect(() => {
    if (pausedOverride) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [pausedOverride]);

  const targetMs = mountedAt + offsetMinutesFromMount * 60 * 1000;
  const remainingSeconds = Math.max(0, Math.floor((targetMs - now) / 1000));
  const expired = remainingSeconds === 0;
  const hh = String(Math.floor(remainingSeconds / 3600)).padStart(2, "0");
  const mm = String(Math.floor((remainingSeconds % 3600) / 60)).padStart(2, "0");
  const ss = String(remainingSeconds % 60).padStart(2, "0");
  return { remainingSeconds, formatted: `${hh}:${mm}:${ss}`, expired };
}
