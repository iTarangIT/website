// Server-only OTP session store for the public WhatsApp OTP flow.
//
// The CRM keeps these in a DB table (calc_otp_verifications) keyed by the
// logged-in dealer's user id. A public website has no auth, so this port keeps
// the SAME security mechanics but stores sessions in-memory keyed by a random
// sessionId carried in an httpOnly cookie (same shape as the site's existing
// 2Factor SMS flow in src/lib/otp-server.ts).
//
// The OTP is stored ONLY as a SHA-256 hash and NEVER leaves the server — a
// 6-digit code is trivially brute-forced from its hash, so it must not be put
// in a cookie or response body (except the explicit dev shortcut below).
//
// ⚠️ In-memory = per-process. On a single VPS/PM2 instance this is fine. Across
// multiple serverless instances or after a redeploy, sessions reset (the user
// just re-requests an OTP). For multi-instance you'd back this with Redis/DB.

import crypto from "crypto";

const OTP_LIFETIME_MS = 10 * 60 * 1000; // 10 minutes
const MAX_SENDS = 3; // sends per session before cooldown
const COOLDOWN_MS = 30 * 60 * 1000; // 30-min cooldown after MAX_SENDS
const MAX_ATTEMPTS = 3; // wrong-code attempts before lockout
const LOCK_MS = 5 * 60 * 1000; // 5-min lockout

export const OTP_SESSION_COOKIE = "itarang_wa_otp_session";

interface Session {
  phone: string; // normalized 91XXXXXXXXXX
  customerName: string;
  otpHash: string;
  expiresAt: number;
  createdAt: number;
  sendCount: number;
  attemptCount: number;
  lockedUntil: number | null;
  verified: boolean;
}

const sessions = new Map<string, Session>();

function hashOtp(otp: string): string {
  return crypto.createHash("sha256").update(otp).digest("hex");
}

function sweep() {
  const now = Date.now();
  for (const [id, s] of sessions) {
    // Drop sessions well past any cooldown/expiry to bound memory.
    if (now - s.createdAt > COOLDOWN_MS + OTP_LIFETIME_MS) sessions.delete(id);
  }
}

export type SendOutcome =
  | { ok: true; sessionId: string; otp: string; sendCount: number; maxSends: number; expiresInSeconds: number }
  | { ok: false; code: "cooldown"; message: string };

/**
 * Create or advance an OTP session and return the freshly generated OTP for the
 * caller to deliver over WhatsApp. Reuses the existing session (bumping
 * sendCount) when a valid sessionId cookie is passed for the same phone.
 */
export function issueOtp(
  existingSessionId: string | undefined,
  phone: string,
  customerName: string,
  otp: string,
): SendOutcome {
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
      };
    }
    // Cooldown elapsed — start fresh.
    if (sessionId) sessions.delete(sessionId);
    session = undefined;
    sessionId = undefined;
  }

  const expiresAt = now + OTP_LIFETIME_MS;
  if (session && sessionId) {
    session.otpHash = hashOtp(otp);
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
      otpHash: hashOtp(otp),
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
    otp,
    sendCount: session.sendCount,
    maxSends: MAX_SENDS,
    expiresInSeconds: Math.floor(OTP_LIFETIME_MS / 1000),
  };
}

export type VerifyOutcome =
  | { ok: true; phone: string }
  | { ok: false; code: "no_active_otp" | "locked" | "expired" | "wrong_otp"; message: string; status: number };

/** Hash-compare the entered OTP against the cookie session. */
export function verifyOtp(sessionId: string | undefined, otp: string): VerifyOutcome {
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

  if (session.otpHash !== hashOtp(otp)) {
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

/** True iff this session exists and has been verified (for downstream gating). */
export function isSessionVerified(sessionId: string | undefined): boolean {
  const s = sessionId ? sessions.get(sessionId) : undefined;
  return !!s?.verified;
}
