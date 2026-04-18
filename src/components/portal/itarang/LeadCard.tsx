"use client";

import { MapPin, Phone as PhoneIcon, Info, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import IntentScoreRing from "./IntentScoreRing";
import AIDialerButton from "./AIDialerButton";
import { SOURCE_LABEL, type Lead } from "@/data/portal/leads";

const SOURCE_STYLES: Record<string, string> = {
  apify: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  gmaps: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  firecrawl: "bg-orange-500/20 text-orange-300 border-orange-500/30",
};

interface Props {
  lead: Lead;
  onStartCall: () => void;
  onQualify: () => void;
  onHandoff: () => void;
}

export default function LeadCard({ lead, onStartCall, onQualify, onHandoff }: Props) {
  const scoreHidden = lead.stage === "scraped" || lead.stage === "calling";

  return (
    <div className={cn(
      "rounded-xl bg-white/5 border border-white/10 p-4 flex flex-col gap-3 transition-all",
      lead.stage === "calling" && "ring-2 ring-accent-amber/50 animate-pulse",
    )}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-white truncate">{lead.businessName}</p>
          <p className="text-[11px] text-gray-500 truncate">{lead.contactName} · {lead.phone}</p>
        </div>
        <IntentScoreRing score={lead.intentScore} hidden={scoreHidden} />
      </div>

      <div className="flex items-center gap-1.5 flex-wrap">
        <span className={cn(
          "inline-flex items-center px-1.5 py-0.5 rounded-md border text-[10px] font-semibold",
          SOURCE_STYLES[lead.source],
        )}>
          {SOURCE_LABEL[lead.source]}
        </span>
        <span className="text-[10px] text-gray-500">{lead.leadType}</span>
      </div>

      <div className="flex items-center gap-1 text-[11px] text-gray-500">
        <MapPin className="h-3 w-3" />
        {lead.area}, {lead.city}
      </div>

      {!scoreHidden && (
        <div className="rounded-md bg-black/20 border border-white/5 p-2 space-y-1">
          <p className="text-[9px] uppercase tracking-wider text-gray-500 flex items-center gap-1">
            <Info className="h-2.5 w-2.5" />
            Intent factors
          </p>
          <div className="grid grid-cols-5 gap-1 text-[9px]">
            <Factor label="Cap" value={lead.factors.capability} />
            <Factor label="Res" value={lead.factors.response} />
            <Factor label="Tim" value={lead.factors.timing} />
            <Factor label="Bud" value={lead.factors.budget} />
            <Factor label="Red" value={lead.factors.readiness} />
          </div>
        </div>
      )}

      {lead.notes && (
        <p className="text-[11px] text-gray-400 italic border-l-2 border-white/10 pl-2 line-clamp-2">
          {lead.notes}
        </p>
      )}

      {/* Stage-specific actions */}
      <div className="mt-auto">
        {lead.stage === "scraped" && (
          <AIDialerButton lead={lead} onStart={onStartCall} onQualify={onQualify} />
        )}
        {lead.stage === "calling" && (
          <div className="flex items-center justify-center gap-2 py-2 text-xs text-accent-amber">
            <PhoneIcon className="h-3.5 w-3.5 animate-pulse" />
            AI dialer in progress…
          </div>
        )}
        {lead.stage === "qualified" && (
          <button
            onClick={onHandoff}
            className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-lg bg-accent-green/20 border border-accent-green/30 text-accent-green hover:bg-accent-green/30"
          >
            Assign to sales
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        )}
        {lead.stage === "handoff" && (
          <div className="text-center text-[11px] text-gray-500 py-2 border-t border-white/5">
            Owned by sales
          </div>
        )}
      </div>
    </div>
  );
}

function Factor({ label, value }: { label: string; value: number }) {
  const color = value >= 80 ? "text-accent-green" : value >= 60 ? "text-brand-300" : "text-accent-amber";
  return (
    <div className="text-center">
      <p className="text-gray-500">{label}</p>
      <p className={cn("font-bold tabular-nums", color)}>{value}</p>
    </div>
  );
}
