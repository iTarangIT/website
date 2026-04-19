"use client";

import { useState, useSyncExternalStore } from "react";
import { Sparkles, Settings2, AlertCircle } from "lucide-react";
import AICallerSettings from "./AICallerSettings";
import AddLeadForm, { type NewLeadPayload } from "./AddLeadForm";
import LeadRow, { type AICallerLead } from "./LeadRow";
import CallDialog, { type CallDialogLead } from "./CallDialog";
import {
  readElevenLabsSettings,
  readElevenLabsServerSnapshot,
  subscribeToElevenLabsSettings,
} from "@/lib/elevenlabs";
import {
  upsertLead,
  subscribeToLeads,
  listLeads,
  summarizeHistory,
  type LeadRecord,
} from "@/lib/lead-store";

const EMPTY_LEADS: LeadRecord[] = [];

export default function AICallerSection() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settings = useSyncExternalStore(
    subscribeToElevenLabsSettings,
    readElevenLabsSettings,
    readElevenLabsServerSnapshot,
  );
  const configured = Boolean(settings.agentId && settings.phoneNumberId);

  // Persistent leads (localStorage). Subscribed via useSyncExternalStore so any call
  // appending to history re-renders the list (and the score badges).
  const stored = useSyncExternalStore(subscribeToLeads, listLeads, () => EMPTY_LEADS);

  // In-session queue for the current add/dial loop.
  const [leads, setLeads] = useState<AICallerLead[]>([]);
  const [activeLead, setActiveLead] = useState<CallDialogLead | null>(null);

  const addLead = (payload: NewLeadPayload) => {
    const leadId = `lead-${Date.now()}`;

    // Persist to the store (upsert by phone).
    upsertLead({
      phone: payload.phone,
      name: payload.name,
      shopName: payload.shopName,
      city: payload.city,
      language: payload.language,
      interest: payload.interest,
      callStatus: payload.status,
      totalAttempts: payload.totalAttempts,
      isFollowup: payload.isFollowup,
      lastCallMemory: payload.lastCallMemory,
      persistentMemory: payload.persistentMemory,
      firstMessage: payload.firstMessage,
      pitchOverride: payload.pitchOverride,
    });

    setLeads((prev) => [
      {
        id: leadId,
        name: payload.name,
        phone: payload.phone,
        shopName: payload.shopName,
        city: payload.city,
        language: payload.language,
        interest: payload.interest,
        callStatus: payload.status,
        totalAttempts: payload.totalAttempts,
        isFollowup: payload.isFollowup,
        lastCallMemory: payload.lastCallMemory,
        persistentMemory: payload.persistentMemory,
        firstMessage: payload.firstMessage,
        pitchOverride: payload.pitchOverride,
        status: "queued",
        addedAt: Date.now(),
      },
      ...prev,
    ]);
  };

  const startCall = (lead: AICallerLead) => {
    if (!configured) {
      setSettingsOpen(true);
      return;
    }
    setActiveLead({
      id: lead.id,
      name: lead.name,
      phone: lead.phone,
      shopName: lead.shopName,
      city: lead.city,
      language: lead.language,
      interest: lead.interest,
      callStatus: lead.callStatus,
      totalAttempts: lead.totalAttempts,
      isFollowup: lead.isFollowup,
      lastCallMemory: lead.lastCallMemory,
      persistentMemory: lead.persistentMemory,
      firstMessage: lead.firstMessage,
      pitchOverride: lead.pitchOverride,
    });
    setLeads((prev) => prev.map((l) => (l.id === lead.id ? { ...l, status: "calling" } : l)));
  };

  const closeCall = (
    finalStatus?: "connecting" | "in-progress" | "finalize" | "ended" | "ended-short" | "failed",
  ) => {
    const mapped: AICallerLead["status"] = finalStatus === "failed" ? "failed" : "ended";
    if (activeLead) {
      setLeads((prev) => prev.map((l) => (l.id === activeLead.id ? { ...l, status: mapped } : l)));
    }
    setActiveLead(null);
  };

  // Decorate in-session rows with history from the persistent store.
  const decorated = leads.map((l) => {
    const record = stored.find((r) => r.phone === l.phone);
    if (!record) return l;
    const summary = summarizeHistory(record);
    return {
      ...l,
      totalCallsInStore: summary.totalAttempts,
      latestScore: summary.latestScore ?? null,
    };
  });

  return (
    <section id="ai-caller" className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/10 flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h4 className="text-sm font-semibold text-gray-200 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-accent-amber" />
            AI caller · live demo
          </h4>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Add a lead and dial it in real time through your ElevenLabs agent. Transcript streams into the dialog, then GPT scores the call.
          </p>
        </div>
        <button
          onClick={() => setSettingsOpen(true)}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium rounded-md bg-white/5 border border-white/10 text-gray-200 hover:bg-white/10"
        >
          <Settings2 className="h-3 w-3" />
          Agent settings
          {configured && <span className="h-1.5 w-1.5 rounded-full bg-accent-green ml-0.5" />}
        </button>
      </div>

      <div className="p-5 space-y-4">
        {!configured && (
          <div role="alert" className="rounded-lg bg-accent-amber/10 border border-accent-amber/30 px-3 py-2.5 flex items-start gap-2 text-[11px] text-accent-amber">
            <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <div className="min-w-0">
              <p className="font-semibold">Connect your ElevenLabs agent</p>
              <p className="text-[10px] text-accent-amber/80 mt-0.5 leading-relaxed">
                Set <span className="font-mono">ELEVENLABS_API_KEY</span> and <span className="font-mono">OPENAI_API_KEY</span> on the server, then click
                <strong> Agent settings</strong> to paste your agent ID + phone-number ID.
              </p>
            </div>
          </div>
        )}

        <AddLeadForm onAdd={addLead} />

        {decorated.length > 0 ? (
          <div className="space-y-2">
            <p className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">In-session leads</p>
            {decorated.map((lead) => (
              <LeadRow key={lead.id} lead={lead} onCall={() => startCall(lead)} />
            ))}
            <p className="text-[10px] text-gray-500 italic pt-1">
              Lead list resets on page reload. Call history &amp; intent scores persist across reloads (localStorage).
            </p>
          </div>
        ) : (
          <div className="rounded-lg border border-dashed border-white/10 bg-black/20 px-4 py-6 text-center text-xs text-gray-500">
            Added leads will appear here with a Call button.
          </div>
        )}
      </div>

      <AICallerSettings open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <CallDialog lead={activeLead} onClose={closeCall} />
    </section>
  );
}
