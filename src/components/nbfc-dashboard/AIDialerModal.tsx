"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  PhoneOff,
  CheckCircle2,
  XCircle,
  Bot,
  User as UserIcon,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Lead } from "@/lib/nbfc-mock-data";

const LINE_INTERVAL_MS = 1800;
const TYPING_MS = 800;

type ToastState = { text: string; tone: "success" | "error" } | null;

function formatElapsed(seconds: number) {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
}

export default function AIDialerModal({
  lead,
  onClose,
}: {
  lead: Lead | null;
  onClose: () => void;
}) {
  const [visibleLines, setVisibleLines] = useState(0);
  const [typing, setTyping] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [toast, setToast] = useState<ToastState>(null);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!lead) return;

    setVisibleLines(0);
    setTyping(true);
    setElapsed(0);
    setToast(null);

    const timeouts: ReturnType<typeof setTimeout>[] = [];

    const total = lead.transcript.length;

    for (let i = 0; i < total; i++) {
      const base = i * LINE_INTERVAL_MS;
      timeouts.push(
        setTimeout(() => setTyping(true), base),
        setTimeout(() => {
          setTyping(false);
          setVisibleLines(i + 1);
        }, base + TYPING_MS)
      );
    }
    // turn off typing indicator after last line
    timeouts.push(setTimeout(() => setTyping(false), total * LINE_INTERVAL_MS));

    const elapsedTimer = setInterval(() => setElapsed((e) => e + 1), 1000);

    return () => {
      timeouts.forEach(clearTimeout);
      clearInterval(elapsedTimer);
    };
  }, [lead]);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [visibleLines, typing]);

  const showToast = (text: string, tone: "success" | "error") => {
    setToast({ text, tone });
    setTimeout(() => {
      setToast(null);
      onClose();
    }, 1400);
  };

  const verdictStyles = lead
    ? lead.finalVerdict === "QUALIFIED"
      ? "bg-green-50 border-green-200 text-green-700"
      : lead.finalVerdict === "REVIEW"
      ? "bg-amber-50 border-amber-200 text-amber-700"
      : "bg-red-50 border-red-200 text-red-700"
    : "";

  const callComplete = lead ? visibleLines >= lead.transcript.length : false;

  return (
    <Dialog
      open={lead !== null}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <DialogContent className="sm:max-w-5xl p-0 overflow-hidden border-0">
        <DialogTitle className="sr-only">
          AI dialer simulation for {lead?.name}
        </DialogTitle>
        <DialogDescription className="sr-only">
          Live transcript of the iTarang AI qualification call, with real-time
          field extraction.
        </DialogDescription>

        {lead && (
          <div className="flex flex-col max-h-[88vh]">
            {/* Header */}
            <div className="flex items-center justify-between gap-4 px-5 sm:px-6 py-4 bg-gradient-to-r from-brand-950 to-brand-800 text-white">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 border border-white/20 shrink-0">
                  <UserIcon className="h-5 w-5" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold truncate">{lead.name}</p>
                  <p className="text-[11px] text-white/60 truncate">
                    {lead.phoneMasked}
                    <span className="mx-1.5 text-white/30">·</span>
                    Language: {lead.language}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/20 border border-red-400/40 px-2.5 py-1 text-[11px] font-semibold text-red-200">
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400/70" />
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-red-400" />
                  </span>
                  Live · {formatElapsed(elapsed)}
                </span>
              </div>
            </div>

            {/* Body — split transcript + extraction */}
            <div className="flex-1 overflow-hidden grid grid-cols-1 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
              {/* Transcript */}
              <div
                ref={transcriptRef}
                className="min-h-[320px] max-h-[56vh] overflow-y-auto bg-gray-50 px-5 sm:px-6 py-5 space-y-3"
              >
                {lead.transcript.slice(0, visibleLines).map((line, idx) => (
                  <TranscriptBubble key={idx} speaker={line.speaker} text={line.text} />
                ))}
                {typing && !callComplete && (
                  <TypingBubble
                    speaker={
                      lead.transcript[visibleLines]?.speaker ?? "AI"
                    }
                  />
                )}
              </div>

              {/* Extraction panel */}
              <div className="border-t lg:border-t-0 lg:border-l border-gray-200 bg-white px-5 sm:px-6 py-5 overflow-y-auto">
                <div className="flex items-center gap-2 mb-4">
                  <Sparkles className="h-4 w-4 text-brand-500" />
                  <h3 className="text-sm font-semibold text-gray-900">
                    Live extraction
                  </h3>
                </div>

                <ul className="space-y-2">
                  {lead.extraction.map((field) => {
                    const revealed = visibleLines > field.revealAfterLineIndex;
                    return (
                      <li
                        key={field.label}
                        className={cn(
                          "flex items-start gap-2.5 rounded-lg border px-3 py-2.5 transition-all",
                          revealed
                            ? "border-green-200 bg-green-50/60"
                            : "border-dashed border-gray-200 bg-gray-50/60"
                        )}
                      >
                        <AnimatePresence mode="wait">
                          {revealed ? (
                            <motion.div
                              key="check"
                              initial={{ scale: 0, opacity: 0 }}
                              animate={{ scale: 1, opacity: 1 }}
                              transition={{ type: "spring", stiffness: 400, damping: 22 }}
                              className="shrink-0 mt-0.5"
                            >
                              <CheckCircle2 className="h-4 w-4 text-accent-green" />
                            </motion.div>
                          ) : (
                            <motion.div
                              key="dot"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              className="mt-1.5 h-1.5 w-1.5 rounded-full bg-gray-300 shrink-0"
                            />
                          )}
                        </AnimatePresence>
                        <div className="min-w-0 flex-1">
                          <p
                            className={cn(
                              "text-[10px] font-semibold uppercase tracking-widest",
                              revealed ? "text-gray-500" : "text-gray-300"
                            )}
                          >
                            {field.label}
                          </p>
                          <motion.p
                            key={revealed ? "on" : "off"}
                            initial={revealed ? { opacity: 0, x: 4 } : false}
                            animate={{ opacity: 1, x: 0 }}
                            className={cn(
                              "text-sm font-medium truncate",
                              revealed ? "text-gray-900" : "text-gray-300"
                            )}
                          >
                            {revealed ? field.value : "Awaiting…"}
                          </motion.p>
                        </div>
                      </li>
                    );
                  })}
                </ul>

                <AnimatePresence>
                  {callComplete && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.2 }}
                      className={cn(
                        "mt-5 rounded-xl border p-4",
                        verdictStyles
                      )}
                    >
                      <p className="text-[10px] font-semibold uppercase tracking-widest opacity-75">
                        Qualification Score
                      </p>
                      <p className="mt-1 text-3xl font-semibold tabular-nums">
                        {lead.finalScore}
                        <span className="text-sm opacity-60"> / 100</span>
                      </p>
                      <p className="mt-1 text-sm font-semibold">{lead.finalVerdict}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 bg-white px-5 sm:px-6 py-4 flex flex-wrap items-center justify-end gap-2">
              <button
                onClick={onClose}
                className="inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100"
              >
                <PhoneOff className="h-4 w-4" />
                End Call
              </button>
              <button
                onClick={() => showToast("Lead rejected", "error")}
                className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-semibold text-red-600 hover:bg-red-50"
              >
                <XCircle className="h-4 w-4" />
                Reject
              </button>
              <button
                onClick={() => showToast("Lead qualified ✓", "success")}
                className="inline-flex items-center gap-1.5 rounded-lg bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-600 shadow-sm"
              >
                <CheckCircle2 className="h-4 w-4" />
                Mark as Qualified
              </button>
            </div>

            {/* Toast */}
            <AnimatePresence>
              {toast && (
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 12 }}
                  className={cn(
                    "absolute bottom-20 left-1/2 -translate-x-1/2 rounded-full px-4 py-2 text-xs font-semibold shadow-lg",
                    toast.tone === "success"
                      ? "bg-green-600 text-white"
                      : "bg-gray-900 text-white"
                  )}
                >
                  {toast.text}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function TranscriptBubble({
  speaker,
  text,
}: {
  speaker: "AI" | "Driver";
  text: string;
}) {
  const isAI = speaker === "AI";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn("flex items-end gap-2", isAI ? "justify-start" : "justify-end")}
    >
      {isAI && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-600">
          <Bot className="h-3.5 w-3.5" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[82%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed",
          isAI
            ? "bg-brand-50 text-brand-900 rounded-bl-sm"
            : "bg-white text-gray-800 border border-gray-200 rounded-br-sm"
        )}
      >
        <p className="text-[10px] font-semibold uppercase tracking-widest mb-0.5 opacity-60">
          {isAI ? "AI · Priya" : "Driver"}
        </p>
        {text}
      </div>
      {!isAI && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-500">
          <UserIcon className="h-3.5 w-3.5" />
        </div>
      )}
    </motion.div>
  );
}

function TypingBubble({ speaker }: { speaker: "AI" | "Driver" }) {
  const isAI = speaker === "AI";
  return (
    <div className={cn("flex items-end gap-2", isAI ? "justify-start" : "justify-end")}>
      {isAI && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-600">
          <Bot className="h-3.5 w-3.5" />
        </div>
      )}
      <div
        className={cn(
          "rounded-2xl px-3.5 py-2.5",
          isAI ? "bg-brand-50" : "bg-white border border-gray-200"
        )}
      >
        <div className="flex items-center gap-1">
          <Dot delay={0} />
          <Dot delay={0.15} />
          <Dot delay={0.3} />
        </div>
      </div>
      {!isAI && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gray-100 text-gray-500">
          <UserIcon className="h-3.5 w-3.5" />
        </div>
      )}
    </div>
  );
}

function Dot({ delay }: { delay: number }) {
  return (
    <motion.span
      className="h-1.5 w-1.5 rounded-full bg-current opacity-60"
      animate={{ y: [0, -3, 0], opacity: [0.4, 1, 0.4] }}
      transition={{ duration: 0.9, repeat: Infinity, delay }}
    />
  );
}

