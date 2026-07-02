// Client-side OTP service — thin wrappers over /api/otp/send and
// /api/otp/verify (2Factor.in on the server; the session ID travels in an
// httpOnly cookie, so verify only needs the code).

export const DEV_OTP_CODE = "123456";

export interface OtpResult {
  success: boolean;
  error?: string;
  mock?: boolean;
}

async function postJson(path: string, body: object): Promise<OtpResult> {
  try {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = (await res.json().catch(() => null)) as OtpResult | null;
    if (data && typeof data.success === "boolean") return data;
    return { success: false, error: "Something went wrong. Please try again." };
  } catch {
    return { success: false, error: "Couldn't reach the server. Check your connection and try again." };
  }
}

export function sendOtp(phone: string): Promise<OtpResult> {
  return postJson("/api/otp/send", { phone });
}

export function verifyOtp(code: string): Promise<OtpResult> {
  return postJson("/api/otp/verify", { code });
}

export function normalizePhone(raw: string): string {
  const digits = raw.replace(/\D/g, "");
  if (!digits) return "";
  if (digits.startsWith("91") && digits.length >= 12) return `+${digits}`;
  if (digits.length === 10) return `+91${digits}`;
  return `+${digits}`;
}

export function isValidIndianMobile(raw: string): boolean {
  let digits = raw.replace(/\D/g, "");
  if (digits.length === 12 && digits.startsWith("91")) digits = digits.slice(2);
  else if (digits.length === 11 && digits.startsWith("0")) digits = digits.slice(1);
  return /^[6-9]\d{9}$/.test(digits);
}

export function maskPhone(e164: string): string {
  const digits = e164.replace(/\D/g, "");
  const last4 = digits.slice(-4);
  return `+91 •••••• ${last4}`;
}
