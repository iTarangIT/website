"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { riskInsights, type InsightSeverity } from "@/data/portal/insights";

const STYLES: Record<InsightSeverity, { icon: string; cls: string; badge: string }> = {
  critical: { icon: "🔴", cls: "border-red-500/30 bg-red-500/5", badge: "bg-red-500/20 text-red-300" },
  warning: { icon: "🟡", cls: "border-accent-amber/30 bg-accent-amber/5", badge: "bg-accent-amber/20 text-accent-amber" },
  info: { icon: "⚠️", cls: "border-brand-500/30 bg-brand-500/5", badge: "bg-brand-500/20 text-brand-200" },
  positive: { icon: "🟢", cls: "border-accent-green/30 bg-accent-green/5", badge: "bg-accent-green/20 text-accent-green" },
};

export default function InsightCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {riskInsights.map((i) => {
        const s = STYLES[i.severity];
        return (
          <section key={i.id} className={cn("rounded-xl border p-5 flex flex-col", s.cls)}>
            <div className="flex items-center justify-between gap-2 mb-3">
              <span className="text-lg leading-none">{s.icon}</span>
              <span className={cn("text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full", s.badge)}>
                {i.accountsAffected.toLocaleString("en-IN")} accounts
              </span>
            </div>
            <p className="text-base font-bold text-white leading-snug mb-2">{i.headline}</p>
            <p className="text-sm text-gray-300 leading-relaxed flex-1">{i.body}</p>
            <div className="flex items-center gap-2 mt-4">
              {i.primaryAction.href ? (
                <Link
                  href={i.primaryAction.href}
                  className="px-3 py-1.5 text-[11px] font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600"
                >
                  {i.primaryAction.label}
                </Link>
              ) : (
                <button className="px-3 py-1.5 text-[11px] font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600">
                  {i.primaryAction.label}
                </button>
              )}
              {i.secondaryAction && (
                i.secondaryAction.href ? (
                  <Link
                    href={i.secondaryAction.href}
                    className="px-3 py-1.5 text-[11px] font-semibold rounded-md bg-white/5 border border-white/10 text-gray-200 hover:bg-white/10"
                  >
                    {i.secondaryAction.label}
                  </Link>
                ) : (
                  <button className="px-3 py-1.5 text-[11px] font-semibold rounded-md bg-white/5 border border-white/10 text-gray-200 hover:bg-white/10">
                    {i.secondaryAction.label}
                  </button>
                )
              )}
            </div>
          </section>
        );
      })}
    </div>
  );
}
