"use client";

import { cn } from "@/lib/utils";
import { Phone, User, MapPin } from "lucide-react";

export type AICallerLeadStatus = "queued" | "calling" | "ended" | "failed";

export interface AICallerLead {
  id: string;
  // Core fields
  name: string;
  phone: string;
  shopName: string;
  city: string;
  language: string;
  interest: string;
  // Call context (dynamic variables)
  callStatus: string;
  totalAttempts: string;
  isFollowup: string;
  lastCallMemory: string;
  persistentMemory: string;
  firstMessage: string;
  // Optional hard override of agent's opener
  pitchOverride?: string;
  // UI-only status
  status: AICallerLeadStatus;
  addedAt: number;
}

const STATUS_STYLES: Record<AICallerLeadStatus, string> = {
  queued: "bg-brand-500/15 text-brand-200 border-brand-500/30",
  calling: "bg-accent-amber/20 text-accent-amber border-accent-amber/40 animate-pulse",
  ended: "bg-accent-green/15 text-accent-green border-accent-green/30",
  failed: "bg-red-500/15 text-red-300 border-red-500/30",
};

interface Props {
  lead: AICallerLead;
  onCall: () => void;
}

export default function LeadRow({ lead, onCall }: Props) {
  const disabled = lead.status === "calling";
  return (
    <article className="flex flex-wrap items-center gap-3 px-4 py-3 rounded-lg bg-white/5 border border-white/10">
      <div className="h-8 w-8 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center shrink-0">
        <User className="h-3.5 w-3.5 text-brand-300" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-white truncate">
          {lead.name}
          {lead.shopName && <span className="text-gray-500 font-normal"> · {lead.shopName}</span>}
        </p>
        <p className="text-[11px] text-gray-500 truncate flex items-center gap-1.5">
          <span className="font-mono">{lead.phone}</span>
          <span className="text-gray-600">·</span>
          <MapPin className="h-2.5 w-2.5" />
          {lead.city}
          <span className="text-gray-600">·</span>
          {lead.language} · {lead.interest}
        </p>
      </div>
      <span className={cn("inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-bold uppercase tracking-wider", STATUS_STYLES[lead.status])}>
        {lead.status}
      </span>
      <button
        type="button"
        onClick={onCall}
        disabled={disabled}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-md bg-brand-500 text-white hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <Phone className="h-3 w-3" />
        {lead.status === "calling" ? "Calling…" : "Call with AI"}
      </button>
    </article>
  );
}
