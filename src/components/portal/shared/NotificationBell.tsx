"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Bell, AlertOctagon, AlertTriangle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { alertCounts, priorityQueue, type AlertSeverity } from "@/data/portal/alerts";
import type { PortalRole } from "@/lib/session";

const ICON: Record<AlertSeverity, typeof AlertOctagon> = {
  critical: AlertOctagon,
  warning: AlertTriangle,
  info: Info,
};

const COLOR: Record<AlertSeverity, string> = {
  critical: "text-red-400",
  warning: "text-accent-amber",
  info: "text-brand-300",
};

export default function NotificationBell({ role }: { role: PortalRole }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const total = alertCounts.critical + alertCounts.warning;

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const topFive = priorityQueue.filter((a) => a.severity !== "info").slice(0, 5);
  const viewAllHref = role === "nbfc" ? "/nbfc/batteries?severity=critical" : "/itarang/auction";

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Notifications · ${total} active`}
        className="relative p-1.5 rounded-md text-gray-400 hover:text-white hover:bg-white/5"
        type="button"
      >
        <Bell className="h-4 w-4" />
        {total > 0 && (
          <span
            className="absolute -top-0.5 -right-1 min-w-[16px] h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center px-1 tabular-nums"
            aria-hidden
          >
            {total > 99 ? "99+" : total}
          </span>
        )}
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-96 rounded-lg bg-gray-950 border border-white/10 shadow-2xl overflow-hidden z-50"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <div>
              <p className="text-xs font-bold text-white">Notifications</p>
              <p className="text-[10px] text-gray-500">
                {alertCounts.critical} critical · {alertCounts.warning} warning · {alertCounts.info} info
              </p>
            </div>
            <Link
              href={viewAllHref}
              onClick={() => setOpen(false)}
              className="text-[10px] font-semibold text-brand-300 hover:text-brand-200 uppercase tracking-wider"
            >
              View all
            </Link>
          </div>
          <ul className="max-h-80 overflow-y-auto divide-y divide-white/5" role="list">
            {topFive.map((a) => {
              const Icon = ICON[a.severity];
              return (
                <li key={a.id}>
                  <Link
                    href={a.actionHref ?? "#"}
                    onClick={() => setOpen(false)}
                    className="flex items-start gap-2 px-4 py-2.5 hover:bg-white/5"
                  >
                    <Icon className={cn("h-3.5 w-3.5 mt-0.5 shrink-0", COLOR[a.severity])} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-white truncate">{a.title}</p>
                      <p className="text-[10px] text-gray-500 truncate">{a.entityLabel} · {a.city}</p>
                    </div>
                    <span className="text-[10px] text-gray-500 shrink-0">{a.timeAgo}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
