// Server-only helpers protecting the PUBLIC loan-calculator endpoints.
//
// 1) A stateless HMAC-signed "verified" cookie, minted by
//    /api/whatsapp-otp/verify after a successful WhatsApp OTP, and required by
//    /api/calculator/calculate. Being stateless it survives
//    multi-instance/serverless deploys (unlike the in-memory OTP session state
//    in lib/whatsapp/otp-store.ts).
// 2) An in-memory per-IP + per-phone rate limiter. Per-instance only (resets on
//    redeploy) — accepted v1 limitation; the signed cookie is the
//    cross-instance backstop.

import { createHmac, timingSafeEqual } from "crypto";

export const CALC_VERIFIED_COOKIE = "itarang_calc_verified";

const COOKIE_TTL_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
export const CALC_COOKIE_MAX_AGE_S = COOKIE_TTL_MS / 1000;

const DEV_SECRET = "itarang-calc-gate-dev-secret";
let missingSecretWarned = false;

function gateSecret(): string | null {
  const s = process.env.CALC_GATE_SECRET;
  if (s && s.length >= 16) return s;
  if (process.env.NODE_ENV !== "production") return DEV_SECRET;
  if (!missingSecretWarned) {
    console.error(
      "[calc-gate] CALC_GATE_SECRET is not set in production — calculator verification will always fail. Set a long random string in the environment.",
    );
    missingSecretWarned = true;
  }
  return null;
}

function hmac(payload: string, secret: string): string {
  return createHmac("sha256", secret).update(payload).digest("hex");
}

/** Mint the signed cookie value for a verified phone (+91XXXXXXXXXX). */
export function signVerifiedCookie(e164Phone: string): string | null {
  const secret = gateSecret();
  if (!secret) return null;
  const expires = Date.now() + COOKIE_TTL_MS;
  return `v1.${e164Phone}.${expires}.${hmac(`${e164Phone}.${expires}`, secret)}`;
}

/** True iff the cookie is well-formed, unexpired, matches this phone, and the HMAC checks out. */
export function verifyVerifiedCookie(value: string | undefined, e164Phone: string): boolean {
  if (!value) return false;
  const secret = gateSecret();
  if (!secret) return false;
  const parts = value.split(".");
  if (parts.length !== 4 || parts[0] !== "v1") return false;
  const [, phone, expiresStr, sig] = parts;
  const expires = Number(expiresStr);
  if (!Number.isFinite(expires) || Date.now() > expires) return false;
  if (phone !== e164Phone) return false;
  const expected = hmac(`${phone}.${expiresStr}`, secret);
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

// ── Rate limiting (in-memory, per instance) ─────────────────────────────────

const WINDOW_MS = 60 * 60 * 1000; // 1 hour
const PHONE_LIMIT = 10; // calcs per phone per hour
const PHONE_COOLDOWN_MS = 5 * 1000; // min gap between calcs for one phone
const IP_LIMIT = 30; // calcs per IP per hour

const phoneHistory = new Map<string, number[]>();
const ipHistory = new Map<string, number[]>();

function recent(map: Map<string, number[]>, key: string, now: number): number[] {
  const kept = (map.get(key) ?? []).filter((t) => now - t < WINDOW_MS);
  map.set(key, kept);
  return kept;
}

export function getClientIp(req: Request): string {
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) {
    const first = fwd.split(",")[0]?.trim();
    if (first) return first;
  }
  return req.headers.get("x-real-ip") ?? "unknown";
}

export function checkCalcAllowed(
  ip: string,
  e164Phone: string,
): { allowed: true } | { allowed: false; error: string } {
  const now = Date.now();
  const byPhone = recent(phoneHistory, e164Phone, now);
  const byIp = recent(ipHistory, ip, now);

  const last = byPhone[byPhone.length - 1];
  if (last != null && now - last < PHONE_COOLDOWN_MS) {
    return { allowed: false, error: "Please wait a few seconds before calculating again." };
  }
  if (byPhone.length >= PHONE_LIMIT) {
    return { allowed: false, error: "Hourly limit reached for this number. Please try again later." };
  }
  if (byIp.length >= IP_LIMIT) {
    return { allowed: false, error: "Too many requests. Please try again later." };
  }

  byPhone.push(now);
  byIp.push(now);
  return { allowed: true };
}
