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

export default function AICallerSection() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settings = useSyncExternalStore(
    subscribeToElevenLabsSettings,
    readElevenLabsSettings,
    readElevenLabsServerSnapshot,
  );
  const configured = Boolean(settings.agentId && settings.phoneNumberId);
  const [leads, setLeads] = useState<AICallerLead[]>([]);
  const [activeLead, setActiveLead] = useState<CallDialogLead | null>(null);

  const addLead = (payload: NewLeadPayload) => {
    setLeads((prev) => [
      {
        ...payload,
        id: `lead-${Date.now()}`,
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
      city: lead.city,
      businessType: lead.businessType,
      pitchOverride: lead.pitchOverride,
    });
    setLeads((prev) => prev.map((l) => (l.id === lead.id ? { ...l, status: "calling" } : l)));
  };

  const closeCall = (finalStatus?: "connecting" | "in-progress" | "ended" | "failed") => {
    const mapped: AICallerLead["status"] =
      finalStatus === "failed" ? "failed" : finalStatus === "ended" ? "ended" : "ended";
    if (activeLead) {
      setLeads((prev) => prev.map((l) => (l.id === activeLead.id ? { ...l, status: mapped } : l)));
    }
    setActiveLead(null);
  };

  return (
    <section id="ai-caller" className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
      <div className="px-5 py-4 border-b border-white/10 flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h4 className="text-sm font-semibold text-gray-200 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-accent-amber" />
            AI caller · live demo
          </h4>
          <p className="text-[11px] text-gray-500 mt-0.5">
            Add a lead and dial it in real time through your ElevenLabs agent. Transcript streams into the dialog.
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
                Set <span className="font-mono">ELEVENLABS_API_KEY</span> on the server, then click <strong>Agent settings</strong> to paste
                your agent ID + phone-number ID. Use the SIP trunk option for Vobiz-routed numbers.
              </p>
            </div>
          </div>
        )}

        <AddLeadForm onAdd={addLead} />

        {leads.length > 0 ? (
          <div className="space-y-2">
            <p className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">In-session leads</p>
            {leads.map((lead) => (
              <LeadRow key={lead.id} lead={lead} onCall={() => startCall(lead)} />
            ))}
            <p className="text-[10px] text-gray-500 italic pt-1">
              Lead list resets on page reload — this is a live demo workspace, not a CRM.
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
