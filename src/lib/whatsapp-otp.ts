// Client-side OTP wrapper — thin fetch wrappers over /api/whatsapp-otp/send and
// /api/whatsapp-otp/verify. Delivery is now SMS via 2Factor.in (see
// src/lib/otp/two-factor.ts); the route paths keep the historical name. The
// session id travels in an httpOnly cookie, so verify only needs the code.



export const DEV_OTP_CODE = "123456";

export interface OtpResult {
  success: boolean;
  error?: string;
  code?: string;
  data?: {
    otpSentTo?: string;
    sendCount?: number;
    maxSends?: number;
    expiresInSeconds?: number;
    waStatus?: "sent" | "dev_hardcoded";
    _devOtp?: string;
    verified?: boolean;
  };
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

/** Send the WhatsApp OTP. Pass the customer's name so the message can greet them. */
export function sendWhatsappOtp(phone: string, customerName?: string): Promise<OtpResult> {
  return postJson("/api/whatsapp-otp/send", { phone, customerName });
}

/** Verify the 6-digit code the customer received on WhatsApp. */
export function verifyWhatsappOtp(code: string): Promise<OtpResult> {
  return postJson("/api/whatsapp-otp/verify", { code });
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
