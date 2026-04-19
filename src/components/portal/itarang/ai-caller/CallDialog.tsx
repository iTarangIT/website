"use client";

import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Phone, PhoneOff, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import TranscriptStream from "./TranscriptStream";
import {
  startCall,
  pollConversation,
  hangUp,
  readElevenLabsSettings,
  type ElevenLabsCallStatus,
  type ElevenLabsTranscriptTurn,
} from "@/lib/elevenlabs";
import { appendAuditEntry } from "@/lib/audit-store";

export interface CallDialogLead {
  id: string;
  name: string;
  phone: string;
  city: string;
  businessType: string;
  pitchOverride?: string;
}

type UIStatus =
  | "connecting"
  | "in-progress"
  | "ended"
  | "failed";

interface Props {
  lead: CallDialogLead | null;
  onClose: (finalStatus?: UIStatus) => void;
}

const STATUS_LABEL: Record<UIStatus, string> = {
  connecting: "Connecting…",
  "in-progress": "In progress",
  ended: "Ended",
  failed: "Failed",
};

const STATUS_COLOR: Record<UIStatus, string> = {
  connecting: "text-accent-amber",
  "in-progress": "text-accent-green",
  ended: "text-gray-400",
  failed: "text-red-300",
};

export default function CallDialog({ lead, onClose }: Props) {
  const [uiStatus, setUiStatus] = useState<UIStatus>("connecting");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<ElevenLabsTranscriptTurn[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [callSid, setCallSid] = useState<string | null>(null);
  const [durationSec, setDurationSec] = useState(0);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const tickTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Kick off the call when the dialog opens with a lead.
  useEffect(() => {
    if (!lead) return;
    let cancelled = false;

    (async () => {
      const settings = readElevenLabsSettings();
      if (!settings || !settings.agentId || !settings.phoneNumberId) {
        setUiStatus("failed");
        setErrorMessage("Configure agent ID and phone number ID in settings first.");
        return;
      }
      setUiStatus("connecting");
      setTranscript([]);
      setErrorMessage(null);
      setConversationId(null);

      const initialMessage = lead.pitchOverride
        ? lead.pitchOverride
        : `Namaste ${lead.name}, this is ${settings.fromName || "iTarang AI"}. I'm calling about iTarang's lithium-battery financing options for ${lead.businessType.toLowerCase()}s in ${lead.city}. Do you have two minutes?`;

      const result = await startCall({
        agentId: settings.agentId,
        phoneNumberId: settings.phoneNumberId,
        toNumber: lead.phone,
        provider: settings.provider,
        initialMessage,
      });

      if (cancelled) return;

      if (!result.success || !result.conversationId) {
        setUiStatus("failed");
        setErrorMessage(result.message || "Call did not start.");
        return;
      }

      setConversationId(result.conversationId);
      setCallSid(result.callSid);
      startedAtRef.current = Date.now();
      setUiStatus("in-progress");

      appendAuditEntry({
        actionType: "ai-call-placed",
        actionLabel: "AI call placed",
        entity: lead.phone,
        reasonCode: "AI caller demo",
        requestedBy: "Rohit Jain (Platform Admin)",
        approvedBy: null,
        status: "completed",
        details: `Lead: ${lead.name} (${lead.businessType}, ${lead.city}) · conversation_id ${result.conversationId}`,
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [lead]);

  // Poll for transcript while call is active.
  useEffect(() => {
    if (!conversationId || uiStatus === "failed" || uiStatus === "ended") return;

    const tick = async () => {
      const data = await pollConversation(conversationId);
      if (!data) return;
      setTranscript(data.transcript);
      if (data.recordingUrl) setRecordingUrl(data.recordingUrl);
      if (data.durationSec !== undefined) setDurationSec(data.durationSec);

      const mapped: UIStatus =
        data.status === "in-progress" || data.status === "processing" || data.status === "initiated"
          ? "in-progress"
          : data.status === "ended"
          ? "ended"
          : data.status === "failed"
          ? "failed"
          : "in-progress";
      setUiStatus(mapped);
    };

    tick();
    pollTimerRef.current = setInterval(tick, 2000);
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [conversationId, uiStatus]);

  // Tick the local wall-clock timer.
  useEffect(() => {
    if (uiStatus !== "in-progress") return;
    tickTimerRef.current = setInterval(() => {
      if (startedAtRef.current) {
        setDurationSec(Math.floor((Date.now() - startedAtRef.current) / 1000));
      }
    }, 1000);
    return () => {
      if (tickTimerRef.current) clearInterval(tickTimerRef.current);
    };
  }, [uiStatus]);

  const endCall = async () => {
    if (!conversationId) {
      onClose("failed");
      return;
    }
    await hangUp(conversationId);
    setUiStatus("ended");
  };

  const close = () => onClose(uiStatus);

  if (!lead) return null;

  const mmss = `${String(Math.floor(durationSec / 60)).padStart(2, "0")}:${String(durationSec % 60).padStart(2, "0")}`;

  return (
    <Dialog open={!!lead} onOpenChange={(o) => !o && close()}>
      <DialogContent className="sm:max-w-[640px] bg-gray-950 text-white border border-white/10">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Phone className="h-4 w-4 text-brand-300" />
            AI call · {lead.name}
          </DialogTitle>
          <DialogDescription className="text-gray-400 text-xs font-mono">
            {lead.phone} · {lead.city} · {lead.businessType}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          <div className="grid grid-cols-3 gap-3 text-xs">
            <Tile label="Status" value={STATUS_LABEL[uiStatus]} color={STATUS_COLOR[uiStatus]} icon={statusIcon(uiStatus)} />
            <Tile label="Duration" value={mmss} mono />
            <Tile label="Conversation" value={conversationId ? conversationId.slice(0, 10) + "…" : "—"} mono />
          </div>

          {errorMessage && (
            <div role="alert" className="rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-xs text-red-200">
              {errorMessage}
            </div>
          )}

          <TranscriptStream transcript={transcript} />

          {recordingUrl && uiStatus === "ended" && (
            <a
              href={recordingUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-block text-[11px] text-brand-300 hover:text-brand-200 underline"
            >
              Listen to recording →
            </a>
          )}

          <div className="flex items-center justify-between pt-1">
            <p className="text-[11px] text-gray-500">
              {uiStatus === "in-progress" && "Transcript updates every 2 seconds."}
              {uiStatus === "connecting" && "Dialing your SIP trunk…"}
              {uiStatus === "ended" && "Call ended. Full transcript recorded to audit log."}
              {uiStatus === "failed" && "Call failed before connecting."}
            </p>
            <div className="flex items-center gap-2">
              {uiStatus === "in-progress" || uiStatus === "connecting" ? (
                <button
                  onClick={endCall}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-md bg-red-500/20 border border-red-500/40 text-red-200 hover:bg-red-500/30"
                >
                  <PhoneOff className="h-3.5 w-3.5" />
                  Hang up
                </button>
              ) : (
                <button
                  onClick={close}
                  className="px-3 py-2 text-xs font-semibold rounded-md bg-white/5 border border-white/10 text-gray-200 hover:bg-white/10"
                >
                  Close
                </button>
              )}
            </div>
          </div>
          <p className="sr-only">Call Sid: {callSid ?? "unknown"}.</p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function statusIcon(s: UIStatus) {
  if (s === "connecting") return <Loader2 className="h-3 w-3 animate-spin" />;
  if (s === "in-progress") return <span className="h-1.5 w-1.5 rounded-full bg-accent-green animate-pulse" />;
  if (s === "ended") return <CheckCircle2 className="h-3 w-3" />;
  return <XCircle className="h-3 w-3" />;
}

function Tile({
  label,
  value,
  color,
  icon,
  mono,
}: {
  label: string;
  value: string;
  color?: string;
  icon?: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{label}</p>
      <p className={cn("text-sm font-bold flex items-center gap-1.5 truncate", color ?? "text-white", mono && "font-mono")}>
        {icon}
        {value}
      </p>
    </div>
  );
}
