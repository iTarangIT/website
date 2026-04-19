"use client";

import { useEffect, useRef, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Phone, PhoneOff, Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import TranscriptStream from "./TranscriptStream";
import IntentScorePanel from "./IntentScorePanel";
import {
  startCall,
  pollConversation,
  hangUp,
  readElevenLabsSettings,
  type ElevenLabsTranscriptTurn,
} from "@/lib/elevenlabs";
import { appendAuditEntry } from "@/lib/audit-store";
import {
  appendCall,
  getLeadByPhone,
  updateCallScore,
  type IntentScore,
} from "@/lib/lead-store";
import { scoreCall } from "@/lib/intent-score";

export interface CallDialogLead {
  id: string;
  name: string;
  phone: string;
  shopName: string;
  city: string;
  language: string;
  interest: string;
  callStatus: string;
  totalAttempts: string;
  isFollowup: string;
  lastCallMemory: string;
  persistentMemory: string;
  firstMessage: string;
  pitchOverride?: string;
}

type UIStatus =
  | "connecting"
  | "in-progress"
  | "finalize"
  | "ended"
  | "ended-short"
  | "failed";

interface Props {
  lead: CallDialogLead | null;
  onClose: (finalStatus?: UIStatus) => void;
}

const STATUS_LABEL: Record<UIStatus, string> = {
  connecting: "Connecting…",
  "in-progress": "In progress",
  finalize: "Finalizing…",
  ended: "Ended",
  "ended-short": "Ended (short call)",
  failed: "Failed",
};

const STATUS_COLOR: Record<UIStatus, string> = {
  connecting: "text-accent-amber",
  "in-progress": "text-accent-green",
  finalize: "text-accent-amber",
  ended: "text-accent-green",
  "ended-short": "text-gray-300",
  failed: "text-red-300",
};

const POLL_MS_ACTIVE = 1000;
const POLL_MS_FINALIZE = 2000;
const FINALIZE_POLLS = 5; // ~10 s of settle time after a terminal status from ElevenLabs

export default function CallDialog({ lead, onClose }: Props) {
  const [uiStatus, setUiStatus] = useState<UIStatus>("connecting");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<ElevenLabsTranscriptTurn[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [callSid, setCallSid] = useState<string | null>(null);
  const [durationSec, setDurationSec] = useState(0);
  const [recordingUrl, setRecordingUrl] = useState<string | null>(null);
  const [intentStatus, setIntentStatus] = useState<"idle" | "scoring" | "done" | "error">("idle");
  const [intentScore, setIntentScore] = useState<IntentScore | null>(null);
  const [intentError, setIntentError] = useState<string | null>(null);
  const [rawStatus, setRawStatus] = useState<string | null>(null);
  const [terminationReason, setTerminationReason] = useState<string | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const finalizeCountRef = useRef(0);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const tickTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const runIntentScoring = async (phone: string, convoId: string) => {
    setIntentStatus("scoring");
    setIntentError(null);
    // Pull the freshly-persisted lead + call record so the scorer sees full history.
    const storedLead = getLeadByPhone(phone);
    const call = storedLead?.calls.find((c) => c.conversationId === convoId);
    if (!storedLead || !call) {
      setIntentStatus("error");
      setIntentError("Could not load the call record from the store.");
      return;
    }

    const result = await scoreCall({ lead: storedLead, currentCall: call });
    if (!result.ok || !result.score) {
      setIntentStatus("error");
      setIntentError(result.error ?? "Unknown scoring error");
      return;
    }

    updateCallScore(phone, convoId, result.score);
    setIntentScore(result.score);
    setIntentStatus("done");

    // Log the score to the audit trail alongside the call itself.
    appendAuditEntry({
      actionType: "ai-call-placed",
      actionLabel: `Intent score ${result.score.overall} · ${result.score.recommendedAction}`,
      entity: phone,
      reasonCode: "AI caller scoring",
      requestedBy: "Rohit Jain (Platform Admin)",
      approvedBy: null,
      status: "completed",
      details: result.score.rationale,
    });
  };

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
      setRawStatus(null);
      setTerminationReason(null);
      setIntentStatus("idle");
      setIntentScore(null);
      setIntentError(null);
      finalizeCountRef.current = 0;

      // Only hard-override the agent's entire opener when the user explicitly wrote a
      // pitch override. Otherwise let the agent's own first_message (with {{placeholders}})
      // fire, substituting the dynamic variables we send below.
      const initialMessage = lead.pitchOverride?.trim() || undefined;

      // Dynamic variables — substituted into {{placeholders}} in the agent's prompts.
      // Field names here must exactly match the variable names configured on the agent.
      const dynamicVariables: Record<string, string> = {
        lead_id: lead.id,
        phone_number: lead.phone,
        owner_name: lead.name,
        customer_name: lead.name,
        shop_name: lead.shopName,
        location: lead.city,
        language: lead.language,
        interest: lead.interest,
        status: lead.callStatus,
        total_attempts: lead.totalAttempts,
        is_followup: lead.isFollowup,
        last_call_memory: lead.lastCallMemory,
        persistent_memory: lead.persistentMemory,
        first_message: lead.firstMessage,
      };

      const result = await startCall({
        agentId: settings.agentId,
        phoneNumberId: settings.phoneNumberId,
        toNumber: lead.phone,
        provider: settings.provider,
        initialMessage,
        dynamicVariables,
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
        details: `Lead: ${lead.name}${lead.shopName ? ` (${lead.shopName})` : ""}, ${lead.city} · ${lead.language} · conversation_id ${result.conversationId}`,
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [lead]);

  // Poll for transcript while call is active or finalizing.
  useEffect(() => {
    if (!conversationId) return;
    if (uiStatus === "ended" || uiStatus === "ended-short" || uiStatus === "failed") return;

    const tick = async () => {
      const data = await pollConversation(conversationId);
      if (!data) return;

      setTranscript(data.transcript);
      if (data.recordingUrl) setRecordingUrl(data.recordingUrl);
      if (typeof data.durationSec === "number") setDurationSec(data.durationSec);
      if (data.rawStatus) setRawStatus(data.rawStatus);
      if (data.terminationReason) setTerminationReason(data.terminationReason);

      const isTerminal = data.status === "ended" || data.status === "failed";

      if (!isTerminal) {
        if (uiStatus !== "in-progress") setUiStatus("in-progress");
        return;
      }

      // First terminal poll — enter finalize. Subsequent terminal polls bump the counter.
      if (uiStatus !== "finalize") {
        setUiStatus("finalize");
        finalizeCountRef.current = 1;
        return;
      }

      finalizeCountRef.current += 1;
      if (finalizeCountRef.current < FINALIZE_POLLS) return;

      // Settle window is over — pick the final display state based on reality, not EL's status.
      const turns = data.transcript.length;
      const elDuration = data.durationSec ?? 0;
      const fallbackDuration = startedAtRef.current
        ? Math.floor((Date.now() - startedAtRef.current) / 1000)
        : 0;
      const finalDuration = elDuration > 0 ? elDuration : fallbackDuration;

      let finalUi: UIStatus;
      if (turns >= 1 && finalDuration >= 5) {
        finalUi = "ended";
      } else if (turns >= 1) {
        finalUi = "ended-short";
      } else {
        finalUi = "failed";
        if (!errorMessage) {
          setErrorMessage(
            data.terminationReason ||
              "Call did not connect. Check the phone number, Do-Not-Disturb settings, or the phone-number ID in ElevenLabs.",
          );
        }
      }

      setDurationSec(finalDuration);
      setUiStatus(finalUi);

      // Persist the call to the store + trigger intent scoring. We only score when a
      // productive conversation actually happened — otherwise OpenAI would be burned on
      // empty transcripts.
      if (lead && conversationId) {
        appendCall(lead.phone, {
          conversationId,
          startedAt: startedAtRef.current ?? Date.now(),
          endedAt: Date.now(),
          durationSec: finalDuration,
          rawStatus: data.rawStatus ?? undefined,
          terminationReason: data.terminationReason ?? undefined,
          recordingUrl: data.recordingUrl ?? undefined,
          transcript: data.transcript,
        });

        if (finalUi !== "failed" && turns >= 1 && finalDuration >= 5 && intentStatus === "idle") {
          // Fire-and-forget — side effect below picks up the result.
          runIntentScoring(lead.phone, conversationId);
        }
      }
    };

    tick();
    const interval = uiStatus === "finalize" ? POLL_MS_FINALIZE : POLL_MS_ACTIVE;
    pollTimerRef.current = setInterval(tick, interval);
    return () => {
      if (pollTimerRef.current) clearInterval(pollTimerRef.current);
    };
  }, [conversationId, uiStatus, errorMessage]);

  // Tick the local wall-clock timer while the call is live (stop once the call enters
  // finalize — from then on, the ElevenLabs-reported duration wins).
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
    // Move into finalize — the poll loop will continue fetching until the settle window is up.
    if (uiStatus === "connecting" || uiStatus === "in-progress") {
      setUiStatus("finalize");
      finalizeCountRef.current = 0;
    }
  };

  const close = () => onClose(uiStatus);

  if (!lead) return null;

  const mmss = `${String(Math.floor(durationSec / 60)).padStart(2, "0")}:${String(durationSec % 60).padStart(2, "0")}`;
  const isLive = uiStatus === "connecting" || uiStatus === "in-progress";
  const isSettled = uiStatus === "ended" || uiStatus === "ended-short" || uiStatus === "failed";

  return (
    <Dialog open={!!lead} onOpenChange={(o) => !o && close()}>
      <DialogContent className="sm:max-w-[640px] bg-gray-950 text-white border border-white/10">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center gap-2">
            <Phone className="h-4 w-4 text-brand-300" />
            AI call · {lead.name}
          </DialogTitle>
          <DialogDescription className="text-gray-400 text-xs font-mono">
            {lead.phone} · {lead.city} · {lead.language} · {lead.interest}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          <div className="grid grid-cols-3 gap-3 text-xs">
            <Tile
              label="Status"
              value={STATUS_LABEL[uiStatus]}
              color={STATUS_COLOR[uiStatus]}
              icon={statusIcon(uiStatus)}
              tooltip={rawStatus ? `ElevenLabs raw status: ${rawStatus}` : undefined}
            />
            <Tile label="Duration" value={mmss} mono icon={<Clock className="h-3 w-3 text-gray-500" />} />
            <Tile label="Conversation" value={conversationId ? conversationId.slice(0, 10) + "…" : "—"} mono />
          </div>

          {uiStatus === "failed" && errorMessage && (
            <div role="alert" className="rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-xs text-red-200">
              {errorMessage}
            </div>
          )}

          {(uiStatus === "ended" || uiStatus === "ended-short") && rawStatus === "failed" && (
            <div
              role="status"
              className="rounded-lg bg-accent-amber/10 border border-accent-amber/30 px-3 py-2 text-[11px] text-accent-amber"
              title="ElevenLabs flags calls as 'failed' for abnormal terminations (user hangup, silence timeout, SIP disconnect) even when the conversation itself went well."
            >
              Heads-up — ElevenLabs marked the raw call status as <span className="font-mono">failed</span>
              {terminationReason ? ` (${terminationReason})` : ""}. The transcript below confirms the conversation took place.
            </div>
          )}

          <TranscriptStream transcript={transcript} />

          <IntentScorePanel
            status={intentStatus}
            score={intentScore}
            error={intentError}
            onRetry={
              conversationId
                ? () => runIntentScoring(lead.phone, conversationId)
                : undefined
            }
          />

          {recordingUrl && isSettled && (
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
            <p className="text-[11px] text-gray-500">{footerCopy(uiStatus, errorMessage, terminationReason)}</p>
            <div className="flex items-center gap-2">
              {isLive || uiStatus === "finalize" ? (
                <button
                  onClick={endCall}
                  disabled={uiStatus === "finalize"}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-md bg-red-500/20 border border-red-500/40 text-red-200 hover:bg-red-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PhoneOff className="h-3.5 w-3.5" />
                  {uiStatus === "finalize" ? "Hanging up…" : "Hang up"}
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

function footerCopy(s: UIStatus, err: string | null, terminationReason: string | null): string {
  switch (s) {
    case "connecting":
      return "Dialing your SIP trunk…";
    case "in-progress":
      return "Live transcript updates every second.";
    case "finalize":
      return "Call ended. Finalizing transcript…";
    case "ended":
      return "Call ended. Transcript recorded to the audit log.";
    case "ended-short":
      return "Call ended after a short conversation. Transcript recorded.";
    case "failed":
      return err || terminationReason || "Call did not connect.";
  }
}

function statusIcon(s: UIStatus) {
  if (s === "connecting" || s === "finalize") return <Loader2 className="h-3 w-3 animate-spin" />;
  if (s === "in-progress") return <span className="h-1.5 w-1.5 rounded-full bg-accent-green animate-pulse" />;
  if (s === "ended") return <CheckCircle2 className="h-3 w-3" />;
  if (s === "ended-short") return <CheckCircle2 className="h-3 w-3 opacity-70" />;
  return <XCircle className="h-3 w-3" />;
}

function Tile({
  label,
  value,
  color,
  icon,
  mono,
  tooltip,
}: {
  label: string;
  value: string;
  color?: string;
  icon?: React.ReactNode;
  mono?: boolean;
  tooltip?: string;
}) {
  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3" title={tooltip}>
      <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1 flex items-center gap-1">
        {label}
        {tooltip && (
          <span className="inline-flex items-center px-1 py-0 rounded bg-white/5 text-[9px] text-gray-400 font-normal normal-case">
            hover for raw
          </span>
        )}
      </p>
      <p className={cn("text-sm font-bold flex items-center gap-1.5 truncate", color ?? "text-white", mono && "font-mono")}>
        {icon}
        {value}
      </p>
    </div>
  );
}
