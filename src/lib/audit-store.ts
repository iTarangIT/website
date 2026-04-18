"use client";

// Client-side audit log store — seeded from static data, augmented in-session.
// Uses a custom event so subscribers update when a new entry is appended.

import { seedAuditLog, type AuditEntry } from "@/data/portal/audit-log";

const EVENT_NAME = "itarang:audit-updated";

let runtimeEntries: AuditEntry[] = [];

function currentIstTimestamp(): string {
  try {
    const d = new Date();
    const iso = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(d);
    // iso ≈ "18/04/2026, 10:42"
    const [date, time] = iso.split(", ");
    const [dd, mm, yyyy] = date.split("/");
    return `${yyyy}-${mm}-${dd} ${time} IST`;
  } catch {
    return new Date().toISOString();
  }
}

export function appendAuditEntry(entry: Omit<AuditEntry, "id" | "timestamp">): AuditEntry {
  const id = `aud-${String(Math.floor(Math.random() * 900000) + 100000)}`;
  const full: AuditEntry = { ...entry, id, timestamp: currentIstTimestamp() };
  runtimeEntries = [full, ...runtimeEntries];
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(EVENT_NAME));
  }
  return full;
}

export function getAuditEntries(): AuditEntry[] {
  return [...runtimeEntries, ...seedAuditLog];
}

export function subscribeToAudit(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(EVENT_NAME, callback);
  return () => window.removeEventListener(EVENT_NAME, callback);
}
