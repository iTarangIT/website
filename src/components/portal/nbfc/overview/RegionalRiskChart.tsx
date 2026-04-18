"use client";

import { useState } from "react";
import { Map as MapIcon, BarChart2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { regionalRisk } from "@/data/portal/portfolio";

export default function RegionalRiskChart() {
  const [view, setView] = useState<"bar" | "map">("bar");
  const maxProb = Math.max(...regionalRisk.map((r) => r.defaultProbabilityPct));

  return (
    <section className="rounded-xl bg-white/5 border border-white/10">
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Regional risk</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">Default probability by region · ranked</p>
        </div>
        <div className="flex items-center gap-1 text-[11px]">
          <button
            onClick={() => setView("bar")}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-md",
              view === "bar" ? "bg-brand-500 text-white" : "bg-white/5 text-gray-400 hover:text-white",
            )}
          >
            <BarChart2 className="h-3 w-3" />
            Bar
          </button>
          <button
            onClick={() => setView("map")}
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-md",
              view === "map" ? "bg-brand-500 text-white" : "bg-white/5 text-gray-400 hover:text-white",
            )}
          >
            <MapIcon className="h-3 w-3" />
            Map
          </button>
        </div>
      </div>
      <div className="px-5 py-4">
        {view === "bar" ? (
          <table className="w-full text-xs">
            <caption className="sr-only">Default probability by region, sorted highest to lowest.</caption>
            <thead>
              <tr className="text-left text-[10px] uppercase tracking-wider text-gray-500">
                <th scope="col" className="pb-2 font-semibold">Region</th>
                <th scope="col" className="pb-2 font-semibold text-right">Active Loans</th>
                <th scope="col" className="pb-2 font-semibold w-[40%]">Default Probability</th>
                <th scope="col" className="pb-2 font-semibold text-right">Avg SOH</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {regionalRisk.map((r) => (
                <tr key={r.region}>
                  <td className="py-2 text-white font-medium">{r.region}</td>
                  <td className="py-2 text-gray-300 tabular-nums text-right">{r.activeLoans.toLocaleString("en-IN")}</td>
                  <td className="py-2 pr-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            r.defaultProbabilityPct > 12 ? "bg-red-400" : r.defaultProbabilityPct > 9 ? "bg-accent-amber" : "bg-accent-green",
                          )}
                          style={{ width: `${(r.defaultProbabilityPct / maxProb) * 100}%` }}
                        />
                      </div>
                      <span className="tabular-nums text-gray-300 w-10 text-right">{r.defaultProbabilityPct}%</span>
                    </div>
                  </td>
                  <td className="py-2 text-gray-300 tabular-nums text-right">{r.avgSoh}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="rounded-lg bg-black/30 border border-dashed border-white/10 px-4 py-10 text-center">
            <MapIcon className="h-6 w-6 mx-auto text-gray-600 mb-2" />
            <p className="text-xs text-gray-500">Map view available in production build.</p>
          </div>
        )}
      </div>
    </section>
  );
}
