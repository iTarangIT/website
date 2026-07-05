// Server-only 2Factor.in SMS OTP layer for the public Loan Calculator gate.
//
// Replaces the earlier WhatsApp/Meta OTP delivery. With 2Factor AUTOGEN, the
// PROVIDER generates, sends, and stores the 6-digit code; we never see it. We
// only keep 2Factor's opaque session id ("Details") and verify the entered code
// against it.
//
// We still keep a small in-memory session, keyed by a random sessionId carried
// in an httpOnly cookie, to (a) bind the OTP session to the phone/name so the
// verify route can mint the signed calculator cookie, and (b) apply the same
// send/attempt rate-limiting UX the WhatsApp flow had.
//
// ⚠️ In-memory = per-process. On a single VPS/PM2 instance this is fine. Across
// multiple serverless instances or after a redeploy, sessions reset (the user
// just re-requests an OTP). The signed calc-gate cookie is the cross-instance
// backstop. For multi-instance you'd back this with Redis/DB.

import crypto from "crypto";

const TWOFACTOR_BASE = "https://2factor.in/API/V1";

const OTP_LIFETIME_MS = 10 * 60 * 1000; // 10 minutes (mirror WhatsApp flow copy)
const MAX_SENDS = 3; // sends per session before cooldown
const COOLDOWN_MS = 30 * 60 * 1000; // 30-min cooldown after MAX_SENDS
const MAX_ATTEMPTS = 3; // wrong-code attempts before lockout
const LOCK_MS = 5 * 60 * 1000; // 5-min lockout

export const OTP_SESSION_COOKIE = "itarang_sms_otp_session";

/** Fixed dev OTP used in mock mode (no SMS sent, no 2Factor credits spent). */
export const DEV_OTP_CODE = "123456";

interface Session {
  phone: string; // E.164 with '+' e.g. +91XXXXXXXXXX
  customerName: string;
  providerSessionId: string; // 2Factor "Details" session id, or "mock"
  expiresAt: number;
  createdAt: number;
  sendCount: number;
  attemptCount: number;
  lockedUntil: number | null;
  verified: boolean;
}

const sessions = new Map<string, Session>();

function sweep() {
  const now = Date.now();
  for (const [id, s] of sessions) {
    if (now - s.createdAt > COOLDOWN_MS + OTP_LIFETIME_MS) sessions.delete(id);
  }
}

/**
 * Mock mode when 2Factor is not configured outside production, or when
 * TWOFACTOR_MOCK=1 is set. In mock mode no SMS is sent and the code is
 * DEV_OTP_CODE ("123456").
 */
export function isMockMode(): boolean {
  if (process.env.TWOFACTOR_MOCK === "1") return true;
  return !process.env.TWOFACTOR_API_KEY?.trim() && process.env.NODE_ENV !== "production";
}

export function maskPhone(e164: string): string {
  const digits = e164.replace(/\D/g, "");
  return `XXXXXX${digits.slice(-4)}`;
}

// ── 2Factor HTTP client ─────────────────────────────────────────────────────

interface TwoFactorResponse {
  Status?: string;
  Details?: string;
}

async function callTwoFactor(url: string): Promise<TwoFactorResponse | null> {
  try {
    const res = await fetch(url, { cache: "no-store" });
    return (await res.json().catch(() => null)) as TwoFactorResponse | null;
  } catch {
    return null;
  }
}

/** AUTOGEN: 2Factor generates + sends the OTP, returns its session id in Details. */
async function twoFactorSend(
  e164Phone: string,
): Promise<{ ok: true; providerSessionId: string } | { ok: false }> {
  const key = process.env.TWOFACTOR_API_KEY?.trim();
  if (!key) return { ok: false };
  const template = process.env.TWOFACTOR_TEMPLATE_NAME?.trim();
  const url = `${TWOFACTOR_BASE}/${key}/SMS/${encodeURIComponent(e164Phone)}/AUTOGEN${
    template ? `/${encodeURIComponent(template)}` : ""
  }`;
  const data = await callTwoFactor(url);
  if (data?.Status === "Success" && data.Details) {
    return { ok: true, providerSessionId: data.Details };
  }
  console.error(
    `[sms-otp] 2Factor send failed for ${maskPhone(e164Phone)}:`,
    data?.Details ?? "network/parse error",
  );
  return { ok: false };
}

/** VERIFY: check the entered code against a 2Factor session id. */
async function twoFactorVerify(
  providerSessionId: string,
  code: string,
): Promise<{ status: "matched" | "mismatch" | "expired" | "error" }> {
  const key = process.env.TWOFACTOR_API_KEY?.trim();
  if (!key) return { status: "error" };
  const url = `${TWOFACTOR_BASE}/${key}/SMS/VERIFY/${encodeURIComponent(
    providerSessionId,
  )}/${encodeURIComponent(code)}`;
  const data = await callTwoFactor(url);
  const details = data?.Details ?? "";
  // 2Factor signals the outcome via Details (HTTP status varies) — branch on it.
  if (data?.Status === "Success" && /matched/i.test(details)) return { status: "matched" };
  if (/mismatch/i.test(details)) return { status: "mismatch" };
  if (/expired/i.test(details)) return { status: "expired" };
  console.error(`[sms-otp] 2Factor verify failed:`, details || "network/parse error");
  return { status: "error" };
}

// ── Session store + rate limiting ───────────────────────────────────────────

export type SendOutcome =
  | {
      ok: true;
      sessionId: string;
      sendCount: number;
      maxSends: number;
      expiresInSeconds: number;
      mock: boolean;
    }
  | { ok: false; code: "cooldown" | "provider_error"; message: string; status: number };

/**
 * Send (or resend) an SMS OTP via 2Factor and create/advance the session.
 * Reuses the existing session (bumping sendCount) when a valid cookie is passed
 * for the same phone.
 */
export async function issueSmsOtp(
  existingSessionId: string | undefined,
  phone: string,
  customerName: string,
): Promise<SendOutcome> {
  sweep();
  const now = Date.now();

  let sessionId = existingSessionId;
  let session = sessionId ? sessions.get(sessionId) : undefined;

  // A cookie for a different phone starts a fresh session.
  if (session && session.phone !== phone) {
    session = undefined;
    sessionId = undefined;
  }

  if (session && session.sendCount >= MAX_SENDS) {
    const cutoff = session.createdAt + COOLDOWN_MS;
    if (now < cutoff) {
      const waitMins = Math.ceil((cutoff - now) / 60000);
      return {
        ok: false,
        code: "cooldown",
        message: `Too many OTP requests. Please wait ${waitMins} min before trying again.`,
        status: 429,
      };
    }
    // Cooldown elapsed — start fresh.
    if (sessionId) sessions.delete(sessionId);
    session = undefined;
    sessionId = undefined;
  }

  // Deliver the code (mock or real 2Factor).
  const mock = isMockMode();
  let providerSessionId: string;
  if (mock) {
    providerSessionId = "mock";
    console.log(`[sms-otp] MOCK send to ${maskPhone(phone)} — code ${DEV_OTP_CODE}`);
  } else {
    const sent = await twoFactorSend(phone);
    if (!sent.ok) {
      return {
        ok: false,
        code: "provider_error",
        message: "Couldn't send the code. Please try again.",
        status: 502,
      };
    }
    providerSessionId = sent.providerSessionId;
  }

  const expiresAt = now + OTP_LIFETIME_MS;
  if (session && sessionId) {
    session.providerSessionId = providerSessionId;
    session.expiresAt = expiresAt;
    session.customerName = customerName;
    session.sendCount += 1;
    session.attemptCount = 0;
    session.lockedUntil = null;
  } else {
    sessionId = crypto.randomUUID();
    session = {
      phone,
      customerName,
      providerSessionId,
      expiresAt,
      createdAt: now,
      sendCount: 1,
      attemptCount: 0,
      lockedUntil: null,
      verified: false,
    };
    sessions.set(sessionId, session);
  }

  return {
    ok: true,
    sessionId,
    sendCount: session.sendCount,
    maxSends: MAX_SENDS,
    expiresInSeconds: Math.floor(OTP_LIFETIME_MS / 1000),
    mock,
  };
}

export type VerifyOutcome =
  | { ok: true; phone: string }
  | {
      ok: false;
      code: "no_active_otp" | "locked" | "expired" | "wrong_otp";
      message: string;
      status: number;
    };

/** Verify the entered code against the session's 2Factor session id. */
export async function verifySmsOtp(
  sessionId: string | undefined,
  code: string,
): Promise<VerifyOutcome> {
  const session = sessionId ? sessions.get(sessionId) : undefined;
  if (!session) {
    return { ok: false, code: "no_active_otp", message: "No active OTP. Please request a new one.", status: 400 };
  }

  const now = Date.now();
  if (session.lockedUntil && now < session.lockedUntil) {
    const mins = Math.ceil((session.lockedUntil - now) / 60000);
    return { ok: false, code: "locked", message: `Too many attempts. Locked for ${mins} more minute(s).`, status: 429 };
  }
  if (now >= session.expiresAt) {
    return { ok: false, code: "expired", message: "OTP expired. Please resend.", status: 400 };
  }

  // Resolve the code: mock compares locally; real uses 2Factor VERIFY.
  let matched: boolean;
  if (session.providerSessionId === "mock" && isMockMode()) {
    matched = code === DEV_OTP_CODE;
  } else {
    const res = await twoFactorVerify(session.providerSessionId, code);
    if (res.status === "expired") {
      return { ok: false, code: "expired", message: "That code expired. Please resend.", status: 400 };
    }
    matched = res.status === "matched";
  }

  if (!matched) {
    session.attemptCount += 1;
    if (session.attemptCount >= MAX_ATTEMPTS) {
      session.lockedUntil = now + LOCK_MS;
      return { ok: false, code: "wrong_otp", message: "Incorrect OTP. Too many attempts — locked for 5 minutes.", status: 400 };
    }
    return {
      ok: false,
      code: "wrong_otp",
      message: `Incorrect OTP. ${MAX_ATTEMPTS - session.attemptCount} attempt(s) remaining.`,
      status: 400,
    };
  }

  session.verified = true;
  return { ok: true, phone: session.phone };
}
