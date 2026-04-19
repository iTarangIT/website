"use client";

// localStorage-backed store for AI caller leads keyed by phone number.
// Persists call history + intent scores across sessions so the agent gets real context
// and the intent-scoring model can reason over prior conversations.

import type { ElevenLabsTranscriptTurn } from "./elevenlabs";

const STORAGE_KEY = "itarang:ai-caller-leads";
const EVENT = "itarang:ai-caller-leads-updated";

export interface IntentScore {
  overall: number;              // 0-100
  dimensions: {
    intent: number;             // readiness to move forward
    productKnowledge: number;   // agent gauged how much they already know
    customerRequirement: number;// clarity of what they actually need
    budgetReadiness: number;
    timelineClarity: number;
  };
  rationale: string;
  recommendedAction: "qualify" | "nurture" | "disqualify";
  scoredAt: number;             // unix ms
  modelUsed?: string;
}

export interface CallRecord {
  conversationId: string;
  startedAt: number;
  endedAt?: number;
  durationSec?: number;
  rawStatus?: string;
  terminationReason?: string;
  recordingUrl?: string;
  transcript: ElevenLabsTranscriptTurn[];
  score?: IntentScore;
}

export interface LeadRecord {
  // Core fields — phone is the unique key
  phone: string;                 // E.164
  name: string;
  shopName: string;
  city: string;
  language: string;
  interest: string;
  // Dynamic variables (mirror the form)
  callStatus: string;
  totalAttempts: string;
  isFollowup: string;
  lastCallMemory: string;
  persistentMemory: string;
  firstMessage: string;
  pitchOverride?: string;
  // History
  calls: CallRecord[];
  firstSeenAt: number;
  lastUpdatedAt: number;
}

function dispatch() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(EVENT));
}

// Cached snapshots for useSyncExternalStore consumers.
// Without caching, every read creates a fresh object/array reference, which makes React
// think the external state changed on every render → infinite re-render → tab crash.
const EMPTY_LIST: LeadRecord[] = Object.freeze([]) as unknown as LeadRecord[];
let cachedRaw: string | null = null;
let cachedMap: Record<string, LeadRecord> = {};
let cachedList: LeadRecord[] = EMPTY_LIST;

function refreshCache(): void {
  if (typeof window === "undefined") {
    cachedRaw = "";
    cachedMap = {};
    cachedList = EMPTY_LIST;
    return;
  }
  const raw = window.localStorage.getItem(STORAGE_KEY) ?? "";
  if (raw === cachedRaw) return;
  cachedRaw = raw;
  try {
    const parsed = raw ? JSON.parse(raw) : {};
    if (parsed && typeof parsed === "object") {
      cachedMap = parsed as Record<string, LeadRecord>;
      cachedList = Object.values(cachedMap).sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt);
    } else {
      cachedMap = {};
      cachedList = EMPTY_LIST;
    }
  } catch {
    cachedMap = {};
    cachedList = EMPTY_LIST;
  }
}

function readAll(): Record<string, LeadRecord> {
  refreshCache();
  return cachedMap;
}

function writeAll(data: Record<string, LeadRecord>): void {
  if (typeof window === "undefined") return;
  const serialized = JSON.stringify(data);
  window.localStorage.setItem(STORAGE_KEY, serialized);
  // Update the cache directly so consumers see the new reference immediately on the next
  // useSyncExternalStore snapshot read.
  cachedRaw = serialized;
  cachedMap = data;
  cachedList = Object.values(data).sort((a, b) => b.lastUpdatedAt - a.lastUpdatedAt);
  dispatch();
}

export function getLeadByPhone(phone: string): LeadRecord | null {
  const all = readAll();
  return all[phone] ?? null;
}

export function listLeads(): LeadRecord[] {
  refreshCache();
  return cachedList;
}

export function upsertLead(input: Omit<LeadRecord, "calls" | "firstSeenAt" | "lastUpdatedAt">): LeadRecord {
  const all = readAll();
  const existing = all[input.phone];
  const now = Date.now();
  const merged: LeadRecord = existing
    ? {
        ...existing,
        ...input,
        calls: existing.calls,
        firstSeenAt: existing.firstSeenAt,
        lastUpdatedAt: now,
      }
    : {
        ...input,
        calls: [],
        firstSeenAt: now,
        lastUpdatedAt: now,
      };
  all[input.phone] = merged;
  writeAll(all);
  return merged;
}

export function appendCall(phone: string, call: CallRecord): LeadRecord | null {
  const all = readAll();
  const lead = all[phone];
  if (!lead) return null;
  // De-dup by conversationId in case of a re-open
  const idx = lead.calls.findIndex((c) => c.conversationId === call.conversationId);
  if (idx >= 0) lead.calls[idx] = { ...lead.calls[idx], ...call };
  else lead.calls = [...lead.calls, call];
  lead.lastUpdatedAt = Date.now();
  all[phone] = lead;
  writeAll(all);
  return lead;
}

export function updateCallScore(phone: string, conversationId: string, score: IntentScore): LeadRecord | null {
  const all = readAll();
  const lead = all[phone];
  if (!lead) return null;
  const idx = lead.calls.findIndex((c) => c.conversationId === conversationId);
  if (idx < 0) return null;
  lead.calls[idx] = { ...lead.calls[idx], score };
  lead.lastUpdatedAt = Date.now();
  all[phone] = lead;
  writeAll(all);
  return lead;
}

export function clearLead(phone: string): void {
  const all = readAll();
  if (all[phone]) {
    delete all[phone];
    writeAll(all);
  }
}

export function subscribeToLeads(cb: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(EVENT, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(EVENT, cb);
    window.removeEventListener("storage", cb);
  };
}

// Useful summaries for the agent's dynamic variables + the UI.
export function summarizeHistory(lead: LeadRecord): { totalAttempts: number; isFollowup: boolean; latestScore?: IntentScore; lastCallSummary?: string } {
  const totalAttempts = lead.calls.length;
  const latestScore = [...lead.calls]
    .reverse()
    .find((c) => c.score)?.score;
  const lastCall = lead.calls[lead.calls.length - 1];
  const lastCallSummary = lastCall
    ? lastCall.score?.rationale ??
      (lastCall.transcript.length > 0
        ? `${lastCall.transcript.length} turns over ${lastCall.durationSec ?? "?"}s`
        : "Call placed but no transcript captured")
    : undefined;
  return { totalAttempts, isFollowup: totalAttempts > 0, latestScore, lastCallSummary };
}
