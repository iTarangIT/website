"use client";

import type { IntentScore, CallRecord, LeadRecord } from "./lead-store";

export interface ScoreCallInput {
  lead: LeadRecord;
  currentCall: CallRecord;
}

export interface ScoreCallResult {
  ok: boolean;
  score?: IntentScore;
  error?: string;
}

export async function scoreCall({ lead, currentCall }: ScoreCallInput): Promise<ScoreCallResult> {
  // Exclude the current call from "previousCalls" (match by conversationId).
  const previousCalls = lead.calls
    .filter((c) => c.conversationId !== currentCall.conversationId)
    .map((c) => ({
      startedAt: c.startedAt,
      durationSec: c.durationSec,
      terminationReason: c.terminationReason,
      transcript: c.transcript,
      priorScoreOverall: c.score?.overall,
    }));

  const res = await fetch("/api/intent-score", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      lead: {
        name: lead.name,
        phone: lead.phone,
        shopName: lead.shopName,
        city: lead.city,
        language: lead.language,
        interest: lead.interest,
        persistentMemory: lead.persistentMemory,
      },
      currentCall: {
        conversationId: currentCall.conversationId,
        durationSec: currentCall.durationSec,
        terminationReason: currentCall.terminationReason,
        transcript: currentCall.transcript,
      },
      previousCalls,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    return { ok: false, error: err.error || `HTTP ${res.status}` };
  }

  const score = (await res.json()) as IntentScore;
  return { ok: true, score };
}
