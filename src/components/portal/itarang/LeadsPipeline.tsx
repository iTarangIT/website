"use client";

import { useState } from "react";
import LeadCard from "./LeadCard";
import { initialLeads, type Lead, type LeadStage } from "@/data/portal/leads";
import { cn } from "@/lib/utils";

const STAGE_META: { id: LeadStage; label: string; sub: string; accent: string }[] = [
  { id: "scraped", label: "Scraped", sub: "Ready for AI dialer", accent: "border-t-brand-500/50" },
  { id: "calling", label: "Calling", sub: "AI dialer in progress", accent: "border-t-accent-amber/50" },
  { id: "qualified", label: "Qualified", sub: "Intent score ≥ 60", accent: "border-t-accent-green/50" },
  { id: "handoff", label: "Handoff", sub: "With sales team", accent: "border-t-pink-400/50" },
];

export default function LeadsPipeline() {
  const [leads, setLeads] = useState<Lead[]>(initialLeads);
  const [toast, setToast] = useState<string | null>(null);

  const fire = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  };

  const setStage = (id: string, stage: LeadStage) => {
    setLeads((prev) => prev.map((l) => (l.id === id ? { ...l, stage } : l)));
  };

  const byStage = (stage: LeadStage) => leads.filter((l) => l.stage === stage);

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {STAGE_META.map((s) => {
          const rows = byStage(s.id);
          return (
            <div key={s.id} className={cn("rounded-xl bg-black/20 border border-white/10 border-t-2 flex flex-col", s.accent)}>
              <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-gray-300">{s.label}</p>
                  <p className="text-[11px] text-gray-500">{s.sub}</p>
                </div>
                <span className="text-xs font-bold text-white bg-white/5 rounded-md px-2 py-0.5 tabular-nums">
                  {rows.length}
                </span>
              </div>
              <div className="flex-1 p-3 space-y-3 min-h-32">
                {rows.map((lead) => (
                  <LeadCard
                    key={lead.id}
                    lead={lead}
                    onStartCall={() => {
                      setStage(lead.id, "calling");
                      fire(`Starting AI call to ${lead.contactName}`);
                    }}
                    onQualify={() => {
                      setStage(lead.id, "qualified");
                      fire(`${lead.contactName} qualified · score ${lead.intentScore}`);
                    }}
                    onHandoff={() => {
                      setStage(lead.id, "handoff");
                      fire(`Assigned ${lead.contactName} to sales`);
                    }}
                  />
                ))}
                {rows.length === 0 && (
                  <div className="rounded-lg border border-dashed border-white/10 px-3 py-6 text-center text-[11px] text-gray-600">
                    No leads in this stage
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 border border-white/10 text-white text-xs px-3.5 py-2 rounded-lg shadow-xl z-50">
          {toast}
        </div>
      )}
    </>
  );
}
