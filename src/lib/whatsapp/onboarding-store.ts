// Server-only conversation state for the WhatsApp customer-onboarding ("new
// lead") flow that starts when a customer taps the onboarding button after
// receiving their EMI schemes.
//
// ⚠️ This repo is a READ MODEL of the CRM's DB (see src/lib/db/schema.ts): the
// website only READS calc_* config and INSERTS calc_leads — it does NOT own a
// migrations chain, so we cannot add an "onboarding_sessions" table here.
// Conversation state therefore lives in-memory, exactly like the OTP store
// (src/lib/whatsapp/otp-store.ts).
//
// In-memory = per-process. On the single VPS/PM2 instance this is fine. Across
// multiple instances or a redeploy, an in-flight onboarding resets (the customer
// re-taps the button). For multi-instance you'd back this with Redis/DB.

const SESSION_TTL_MS = 24 * 60 * 60 * 1000; // 24h — matches the WhatsApp session window

/** Where the customer is in the onboarding conversation. */
export type OnboardingStatus =
  | "prompted" // button sent, waiting for the tap
  | "active" // conversation in progress
  | "completed"; // all steps answered

export interface OnboardingSession {
  /** Normalized "91XXXXXXXXXX". */
  phone: string;
  /** Name captured on the calculator (pre-fills the first question). */
  customerName: string;
  /** Battery model the schemes were for, for context. */
  modelName: string | null;
  /** calc_leads.id of the quote that led here, for CRM hand-off. */
  leadId: string | null;
  status: OnboardingStatus;
  /** Index into the onboarding step list (only meaningful while "active"). */
  stepIndex: number;
  /** Collected answers keyed by step.key. */
  answers: Record<string, string>;
  createdAt: number;
  updatedAt: number;
}

const sessions = new Map<string, OnboardingSession>();

function sweep() {
  const now = Date.now();
  for (const [phone, s] of sessions) {
    if (now - s.updatedAt > SESSION_TTL_MS) sessions.delete(phone);
  }
}

/**
 * Seed (or reset) a "prompted" session when the onboarding button is sent, so
 * the webhook knows the customer's name / model / lead the moment they tap it.
 */
export function seedOnboarding(
  phone: string,
  ctx: { customerName: string; modelName: string | null; leadId: string | null },
): void {
  sweep();
  const now = Date.now();
  sessions.set(phone, {
    phone,
    customerName: ctx.customerName || "",
    modelName: ctx.modelName ?? null,
    leadId: ctx.leadId ?? null,
    status: "prompted",
    stepIndex: 0,
    answers: {},
    createdAt: now,
    updatedAt: now,
  });
}

export function getOnboarding(phone: string): OnboardingSession | undefined {
  return sessions.get(phone);
}

/** Persist mutations back to the map and bump updatedAt. */
export function saveOnboarding(session: OnboardingSession): void {
  session.updatedAt = Date.now();
  sessions.set(session.phone, session);
}

/** Test/maintenance helper — drop a session (e.g. after CRM hand-off). */
export function clearOnboarding(phone: string): void {
  sessions.delete(phone);
}
