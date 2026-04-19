// Thin client-side wrappers around the Next.js API route proxies.
// The actual ELEVENLABS_API_KEY lives on the server — never shipped to the browser.

export interface ElevenLabsCallResult {
  success: boolean;
  conversationId: string | null;
  callSid: string | null;
  message: string;
}

export interface ElevenLabsTranscriptTurn {
  role: "agent" | "user";
  message: string;
  timeInCallSec?: number;
}

export type ElevenLabsCallStatus =
  | "initiated"
  | "processing"
  | "in-progress"
  | "ended"
  | "failed"
  | "unknown";

export interface ElevenLabsConversation {
  conversationId: string;
  status: ElevenLabsCallStatus;
  rawStatus?: string;
  callSuccessful?: boolean | null;
  terminationReason?: string;
  transcript: ElevenLabsTranscriptTurn[];
  durationSec?: number;
  recordingUrl?: string;
}

export interface StartCallParams {
  agentId: string;
  phoneNumberId: string;
  toNumber: string;
  provider?: "sip-trunk" | "twilio";
  initialMessage?: string;
}

export async function startCall(params: StartCallParams): Promise<ElevenLabsCallResult> {
  const res = await fetch("/api/elevenlabs/call", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: "Request failed" }));
    return {
      success: false,
      conversationId: null,
      callSid: null,
      message: err.message || `HTTP ${res.status}`,
    };
  }
  return res.json();
}

export async function pollConversation(id: string): Promise<ElevenLabsConversation | null> {
  const res = await fetch(`/api/elevenlabs/conversation/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function hangUp(id: string): Promise<boolean> {
  const res = await fetch(`/api/elevenlabs/hangup/${encodeURIComponent(id)}`, { method: "POST" });
  return res.ok;
}

export interface TestAgentResult {
  ok: boolean;
  agentName?: string;
  error?: string;
}

export async function testAgent(agentId: string): Promise<TestAgentResult> {
  const res = await fetch(`/api/elevenlabs/test?agentId=${encodeURIComponent(agentId)}`, {
    cache: "no-store",
  });
  return res.json();
}

// localStorage settings
export const EL_KEYS = {
  agentId: "itarang:elevenlabs-agent-id",
  phoneNumberId: "itarang:elevenlabs-phone-number-id",
  fromName: "itarang:elevenlabs-from-name",
  provider: "itarang:elevenlabs-provider",
} as const;

export interface ElevenLabsSettings {
  agentId: string;
  phoneNumberId: string;
  fromName: string;
  provider: "sip-trunk" | "twilio";
}

const EMPTY_SETTINGS: ElevenLabsSettings = Object.freeze({
  agentId: "",
  phoneNumberId: "",
  fromName: "",
  provider: "sip-trunk",
}) as ElevenLabsSettings;

const SETTINGS_EVENT = "itarang:elevenlabs-settings-updated";

// Cache the snapshot so useSyncExternalStore gets a stable reference when values haven't changed.
// Without this, every render returns a new object and React enters an infinite re-render loop.
let cachedSnapshot: ElevenLabsSettings = EMPTY_SETTINGS;

export function readElevenLabsSettings(): ElevenLabsSettings {
  if (typeof window === "undefined") return EMPTY_SETTINGS;
  const next: ElevenLabsSettings = {
    agentId: localStorage.getItem(EL_KEYS.agentId) ?? "",
    phoneNumberId: localStorage.getItem(EL_KEYS.phoneNumberId) ?? "",
    fromName: localStorage.getItem(EL_KEYS.fromName) ?? "",
    provider: (localStorage.getItem(EL_KEYS.provider) as "sip-trunk" | "twilio" | null) ?? "sip-trunk",
  };
  if (
    cachedSnapshot.agentId === next.agentId &&
    cachedSnapshot.phoneNumberId === next.phoneNumberId &&
    cachedSnapshot.fromName === next.fromName &&
    cachedSnapshot.provider === next.provider
  ) {
    return cachedSnapshot;
  }
  cachedSnapshot = next;
  return next;
}

export function readElevenLabsServerSnapshot(): ElevenLabsSettings {
  return EMPTY_SETTINGS;
}

export function writeElevenLabsSettings(s: ElevenLabsSettings): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(EL_KEYS.agentId, s.agentId);
  localStorage.setItem(EL_KEYS.phoneNumberId, s.phoneNumberId);
  localStorage.setItem(EL_KEYS.fromName, s.fromName);
  localStorage.setItem(EL_KEYS.provider, s.provider);
  window.dispatchEvent(new CustomEvent(SETTINGS_EVENT));
}

export function subscribeToElevenLabsSettings(cb: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener(SETTINGS_EVENT, cb);
  window.addEventListener("storage", cb);
  return () => {
    window.removeEventListener(SETTINGS_EVENT, cb);
    window.removeEventListener("storage", cb);
  };
}
