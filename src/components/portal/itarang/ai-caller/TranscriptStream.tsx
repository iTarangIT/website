"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { ElevenLabsTranscriptTurn } from "@/lib/elevenlabs";
import { Bot, User } from "lucide-react";

interface Props {
  transcript: ElevenLabsTranscriptTurn[];
  autoScroll?: boolean;
}

export default function TranscriptStream({ transcript, autoScroll = true }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!autoScroll) return;
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [transcript, autoScroll]);

  if (transcript.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-white/10 bg-black/20 p-6 text-center text-xs text-gray-500">
        Waiting for the first line of transcript… the agent typically speaks within 5 seconds of pickup.
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-black/20 border border-white/10 p-3 max-h-80 overflow-y-auto space-y-2">
      {transcript.map((t, i) => (
        <div
          key={i}
          className={cn(
            "flex items-start gap-2 text-xs",
            t.role === "user" ? "flex-row-reverse" : "flex-row",
          )}
        >
          <div
            className={cn(
              "shrink-0 h-7 w-7 rounded-full border flex items-center justify-center",
              t.role === "user"
                ? "bg-accent-green/15 border-accent-green/30 text-accent-green"
                : "bg-brand-500/15 border-brand-500/30 text-brand-200",
            )}
          >
            {t.role === "user" ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
          </div>
          <div
            className={cn(
              "max-w-[80%] rounded-lg px-2.5 py-1.5 text-[12px] leading-relaxed",
              t.role === "user"
                ? "bg-accent-green/10 text-accent-green/90 border border-accent-green/20"
                : "bg-brand-500/10 text-brand-100 border border-brand-500/20",
            )}
          >
            {t.message}
            {typeof t.timeInCallSec === "number" && (
              <span className="block text-[9px] text-gray-500 mt-0.5">
                {Math.floor(t.timeInCallSec / 60)}:{String(Math.floor(t.timeInCallSec % 60)).padStart(2, "0")}
              </span>
            )}
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
