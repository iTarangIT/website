// Server-only helpers for the OTP routes. Keep this module dependency-free
// (env vars only) so it can be exercised directly with tsx outside Next.

const TWOFACTOR_BASE = "https://2factor.in/API/V1";

const SEND_COOLDOWN_MS = 30_000;
const SEND_WINDOW_MS = 3_600_000;
const SEND_WINDOW_LIMIT = 5;
const MAX_VERIFY_ATTEMPTS = 5;
const ATTEMPT_TTL_MS = 15 * 60_000;

// Per-instance state: resets on redeploy and is not shared across serverless
// instances — an accepted limitation for current traffic (see design spec).
const sendHistory = new Map<string, number[]>();
const verifyAttempts = new Map<string, { count: number; ts: number }>();

export function isMockMode(): boolean {
  if (process.env.TWOFACTOR_MOCK === "1") return true;
  return (
    !process.env.TWOFACTOR_API_KEY && process.env.NODE_ENV !== "production"
  );
}

export function checkSendAllowed(
  phone: string,
  now: number = Date.now(),
): { allowed: boolean; error?: string } {
  const recent = (sendHistory.get(phone) ?? []).filter(
    (t) => t > now - SEND_WINDOW_MS,
  );
  sendHistory.set(phone, recent);
  const last = recent[recent.length - 1];
  if (last !== undefined && now - last < SEND_COOLDOWN_MS) {
    return {
      allowed: false,
      error: "Please wait a moment before requesting another code.",
    };
  }
  if (recent.length >= SEND_WINDOW_LIMIT) {
    return {
      allowed: false,
      error: "Too many attempts. Please try again in a few minutes.",
    };
  }
  return { allowed: true };
}

export function recordSend(phone: string, now: number = Date.now()): void {
  const recent = (sendHistory.get(phone) ?? []).filter(
    (t) => t > now - SEND_WINDOW_MS,
  );
  recent.push(now);
  sendHistory.set(phone, recent);
}

/** Counts an attempt; returns false once the session has used up its 5 tries. */
export function recordVerifyAttempt(
  sessionId: string,
  now: number = Date.now(),
): boolean {
  for (const [key, entry] of verifyAttempts) {
    if (now - entry.ts > ATTEMPT_TTL_MS) verifyAttempts.delete(key);
  }
  const entry = verifyAttempts.get(sessionId) ?? { count: 0, ts: now };
  entry.count += 1;
  entry.ts = now;
  verifyAttempts.set(sessionId, entry);
  return entry.count <= MAX_VERIFY_ATTEMPTS;
}

export function clearVerifyAttempts(sessionId: string): void {
  verifyAttempts.delete(sessionId);
}

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

export async function twoFactorSend(
  e164Phone: string,
): Promise<{
  success: boolean;
  sessionId?: string;
  error?: string;
  status?: number;
}> {
  const key = process.env.TWOFACTOR_API_KEY;
  if (!key) {
    return {
      success: false,
      error: "OTP service is temporarily unavailable.",
      status: 500,
    };
  }
  const template = process.env.TWOFACTOR_TEMPLATE_NAME;
  // 2Factor expects the number without the leading + (e.g. 91XXXXXXXXXX)
  const phoneParam = e164Phone.replace(/^\+/, "");
  const url = `${TWOFACTOR_BASE}/${key}/SMS/${encodeURIComponent(phoneParam)}/AUTOGEN${
    template ? `/${encodeURIComponent(template)}` : ""
  }`;
  const data = await callTwoFactor(url);
  if (data?.Status === "Success" && data.Details) {
    console.info(
      `[otp] 2Factor send OK to ${e164Phone} (template: ${template || "none"})`,
    );
    return { success: true, sessionId: data.Details };
  }
  console.error(
    `[otp] 2Factor send failed for ${e164Phone}:`,
    data?.Details ?? "network/parse error",
  );
  return {
    success: false,
    error: "Couldn't send the code. Please try again.",
    status: 502,
  };
}

export async function twoFactorVerify(
  sessionId: string,
  code: string,
): Promise<{ success: boolean; error?: string; status?: number }> {
  const key = process.env.TWOFACTOR_API_KEY;
  if (!key) {
    return {
      success: false,
      error: "OTP service is temporarily unavailable.",
      status: 500,
    };
  }
  const url = `${TWOFACTOR_BASE}/${key}/SMS/VERIFY/${encodeURIComponent(sessionId)}/${encodeURIComponent(code)}`;
  const data = await callTwoFactor(url);
  const details = data?.Details ?? "";
  // 2Factor signals mismatch/expiry via Details (HTTP status varies) — branch on the string.
  if (data?.Status === "Success" && /matched/i.test(details))
    return { success: true };
  if (/mismatch/i.test(details)) {
    return {
      success: false,
      error: "Incorrect code. Please try again.",
      status: 400,
    };
  }
  if (/expired/i.test(details)) {
    return {
      success: false,
      error: "That code expired. Please resend.",
      status: 400,
    };
  }
  console.error(
    `[otp] 2Factor verify failed:`,
    details || "network/parse error",
  );
  return {
    success: false,
    error: "Verification failed. Please try again.",
    status: 502,
  };
}
