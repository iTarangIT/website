// Shared phone helpers used by the server-side calculator route and the
// calculator UI. The OTP send/verify client now lives in @/lib/whatsapp-otp
// (WhatsApp Cloud API); these pure helpers are kept here because
// /api/calculator/calculate and LoanCalculator import them.

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
