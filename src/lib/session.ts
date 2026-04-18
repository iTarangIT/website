"use client";

import { useSyncExternalStore } from "react";

export type PortalRole = "nbfc" | "itarang";

const STORAGE_KEY = "itarang:role";

export function getRole(): PortalRole | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(STORAGE_KEY);
  if (v === "nbfc" || v === "itarang") return v;
  return null;
}

export function setRole(role: PortalRole): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, role);
  window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY, newValue: role }));
}

export function clearRole(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new StorageEvent("storage", { key: STORAGE_KEY, newValue: null }));
}

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

export function useRole(): { role: PortalRole | null; ready: boolean } {
  const role = useSyncExternalStore<PortalRole | null>(
    subscribe,
    getRole,
    () => null,
  );
  const ready = typeof window !== "undefined";
  return { role, ready };
}

export const ROLE_HOME: Record<PortalRole, string> = {
  nbfc: "/nbfc",
  itarang: "/itarang",
};

export const DEMO_CREDS: Record<PortalRole, { email: string; password: string; label: string }> = {
  nbfc: { email: "risk@nbfc.demo", password: "demo", label: "NBFC Risk Manager" },
  itarang: { email: "admin@itarang.demo", password: "demo", label: "iTarang Platform Admin" },
};
