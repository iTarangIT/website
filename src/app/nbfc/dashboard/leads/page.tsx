"use client";

import { useMemo, useState } from "react";
import LeadCard from "@/components/nbfc-dashboard/LeadCard";
import AIDialerModal from "@/components/nbfc-dashboard/AIDialerModal";
import { leads, type Lead, type LeadStatus } from "@/lib/nbfc-mock-data";
import { cn } from "@/lib/utils";

type Filter = "All" | LeadStatus;

const filters: Filter[] = ["All", "New", "AI-Qualified", "Under Review", "Approved"];

export default function LeadsPage() {
  const [filter, setFilter] = useState<Filter>("All");
  const [activeLead, setActiveLead] = useState<Lead | null>(null);

  const visible = useMemo(
    () => (filter === "All" ? leads : leads.filter((l) => l.status === filter)),
    [filter]
  );

  return (
    <div className="space-y-6 max-w-7xl">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
            Leads pipeline
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Driver applications sourced via the iTarang AI dialer.
          </p>
        </div>
        <span className="text-xs text-gray-500">
          Showing <span className="font-semibold text-gray-900">{visible.length}</span> of{" "}
          {leads.length}
        </span>
      </header>

      <div className="flex flex-wrap gap-2">
        {filters.map((f) => {
          const active = f === filter;
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "rounded-full border px-3.5 py-1.5 text-xs font-semibold transition-colors",
                active
                  ? "border-brand-500 bg-brand-500 text-white"
                  : "border-gray-200 bg-white text-gray-600 hover:border-gray-300 hover:text-gray-900"
              )}
            >
              {f}
            </button>
          );
        })}
      </div>

      {visible.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-gray-200 bg-white p-10 text-center text-sm text-gray-500">
          No leads in this status.
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {visible.map((lead) => (
            <LeadCard key={lead.id} lead={lead} onCall={setActiveLead} />
          ))}
        </div>
      )}

      <AIDialerModal lead={activeLead} onClose={() => setActiveLead(null)} />
    </div>
  );
}
