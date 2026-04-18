"use client";

import { useState } from "react";
import { Phone, Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Lead } from "@/data/portal/leads";

const WEBHOOK_KEY = "itarang:n8n-webhook";

interface Props {
  lead: Lead;
  onStart: () => void;
  onQualify: () => void;
  compact?: boolean;
}

export default function AIDialerButton({ lead, onStart, onQualify, compact = false }: Props) {
  const [state, setState] = useState<"idle" | "calling" | "done" | "error">("idle");
  const [msg, setMsg] = useState<string | null>(null);

  const start = async () => {
    if (state !== "idle") return;
    const url = typeof window !== "undefined" ? window.localStorage.getItem(WEBHOOK_KEY) : null;

    setState("calling");
    onStart();

    // Try webhook first
    if (url) {
      try {
        const controller = new AbortController();
        const t = setTimeout(() => controller.abort(), 5000);
        await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            leadId: lead.id,
            phone: lead.phone,
            name: lead.contactName,
            businessName: lead.businessName,
            leadType: lead.leadType,
            city: lead.city,
            area: lead.area,
            source: lead.source,
            script: `Hello ${lead.contactName}, this is iTarang calling about your ${lead.leadType.toLowerCase()} in ${lead.city}. We offer lithium batteries with EMI financing. Do you have two minutes?`,
          }),
          signal: controller.signal,
          mode: "cors",
        });
        clearTimeout(t);
        setMsg("Call triggered via n8n");
      } catch {
        setMsg("Webhook failed — running demo simulation");
      }
    } else {
      setMsg("Demo mode — no webhook configured");
    }

    // Simulated qualification timeline
    setTimeout(() => {
      setState("done");
      onQualify();
      setTimeout(() => {
        setState("idle");
        setMsg(null);
      }, 1500);
    }, 6000);
  };

  if (compact) {
    return (
      <button
        onClick={start}
        disabled={state !== "idle"}
        className={cn(
          "inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold rounded-md transition-colors",
          state === "idle" && "bg-brand-500 text-white hover:bg-brand-600",
          state === "calling" && "bg-accent-amber/20 text-accent-amber",
          state === "done" && "bg-accent-green/20 text-accent-green",
        )}
      >
        {state === "calling" ? (
          <>
            <Loader2 className="h-3 w-3 animate-spin" />
            Calling…
          </>
        ) : state === "done" ? (
          <>
            <CheckCircle2 className="h-3 w-3" />
            Done
          </>
        ) : (
          <>
            <Phone className="h-3 w-3" />
            Call with AI
          </>
        )}
      </button>
    );
  }

  return (
    <div className="space-y-1.5">
      <button
        onClick={start}
        disabled={state !== "idle"}
        className={cn(
          "w-full inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold rounded-lg transition-colors",
          state === "idle" && "bg-brand-500 text-white hover:bg-brand-600",
          state === "calling" && "bg-accent-amber/20 text-accent-amber border border-accent-amber/30",
          state === "done" && "bg-accent-green/20 text-accent-green border border-accent-green/30",
        )}
      >
        {state === "calling" ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            AI dialer calling…
          </>
        ) : state === "done" ? (
          <>
            <CheckCircle2 className="h-3.5 w-3.5" />
            Qualified
          </>
        ) : (
          <>
            <Phone className="h-3.5 w-3.5" />
            Call with AI
          </>
        )}
      </button>
      {msg && <p className="text-[10px] text-gray-500 text-center">{msg}</p>}
    </div>
  );
}
