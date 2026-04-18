"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { leads, type Lead, type LeadStatus, SOURCE_LABEL } from "@/data/portal/leads";
import ScoreBadge from "@/components/portal/shared/ScoreBadge";
import ScoreExplainer from "@/components/portal/shared/ScoreExplainer";

const STATUS_STYLES: Record<LeadStatus, string> = {
  hot: "bg-accent-green/15 text-accent-green border-accent-green/30",
  warm: "bg-accent-amber/15 text-accent-amber border-accent-amber/30",
  cold: "bg-brand-500/15 text-brand-200 border-brand-500/30",
  converted: "bg-accent-green/25 text-white border-accent-green/50",
  lost: "bg-red-500/15 text-red-300 border-red-500/30",
};

export default function LeadTable() {
  const [status, setStatus] = useState<"all" | LeadStatus>("all");
  const [sort, setSort] = useState<"score" | "name">("score");
  const [explainerLead, setExplainerLead] = useState<Lead | null>(null);

  const rows = useMemo(() => {
    const filtered = leads.filter((l) => (status === "all" ? true : l.status === status));
    return [...filtered].sort((a, b) => (sort === "score" ? b.intentScore - a.intentScore : a.name.localeCompare(b.name)));
  }, [status, sort]);

  return (
    <section className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-5 py-4 border-b border-white/10 flex-wrap">
        <div>
          <h4 className="text-sm font-semibold text-gray-200">Leads</h4>
          <p className="text-[11px] text-gray-500 mt-0.5">{rows.length} of {leads.length} leads · click Intent badge to see inputs</p>
        </div>
        <div className="flex items-center gap-2 text-[11px]">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as "all" | LeadStatus)}
            className="bg-white/5 border border-white/10 text-white rounded-md px-2 py-1 focus:outline-none"
          >
            <option value="all" className="bg-gray-950">Status · All</option>
            <option value="hot" className="bg-gray-950">Hot</option>
            <option value="warm" className="bg-gray-950">Warm</option>
            <option value="cold" className="bg-gray-950">Cold</option>
            <option value="converted" className="bg-gray-950">Converted</option>
          </select>
          <button
            onClick={() => setSort(sort === "score" ? "name" : "score")}
            className="bg-white/5 border border-white/10 text-gray-300 rounded-md px-2 py-1"
          >
            Sort: {sort === "score" ? "Intent score" : "Name"}
          </button>
        </div>
      </div>

      <div className="overflow-x-auto max-h-[560px]">
        <table className="w-full text-[11px]">
          <caption className="sr-only">50 representative leads sorted by intent score.</caption>
          <thead className="bg-black/40 text-gray-500 sticky top-0">
            <tr>
              <th scope="col" aria-sort="none" className="text-left px-4 py-2 font-semibold">Name</th>
              <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Business</th>
              <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Location</th>
              <th scope="col" aria-sort="descending" className="text-left px-3 py-2 font-semibold">Intent</th>
              <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Status</th>
              <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Next action</th>
              <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Source</th>
              <th scope="col" aria-sort="none" className="text-left px-3 py-2 font-semibold">Last contact</th>
              <th scope="col" className="text-right px-4 py-2 font-semibold"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {rows.map((l) => (
              <tr key={l.id} className="hover:bg-white/5">
                <td className="px-4 py-2 text-white font-medium whitespace-nowrap">{l.name}</td>
                <td className="px-3 py-2 text-gray-300">{l.businessType}</td>
                <td className="px-3 py-2 text-gray-400">{l.location}</td>
                <td className="px-3 py-2">
                  <ScoreBadge type="intent" value={l.intentScore} onClick={() => setExplainerLead(l)} />
                </td>
                <td className="px-3 py-2">
                  <span className={cn("inline-flex px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", STATUS_STYLES[l.status])}>
                    {l.status}
                  </span>
                </td>
                <td className="px-3 py-2 text-gray-300">{l.nextAction}</td>
                <td className="px-3 py-2 text-gray-400">{SOURCE_LABEL[l.source]}</td>
                <td className="px-3 py-2 text-gray-500">{l.lastContact}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    className="text-[11px] font-semibold text-brand-300 hover:text-brand-200"
                    onClick={() => setExplainerLead(l)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {explainerLead && (
        <ScoreExplainer
          open={!!explainerLead}
          onClose={() => setExplainerLead(null)}
          type="intent"
          value={explainerLead.intentScore}
          entityLabel={`${explainerLead.name} · ${explainerLead.location}`}
          confidence={explainerLead.confidence}
          intentInputs={explainerLead.inputs}
        />
      )}
    </section>
  );
}
