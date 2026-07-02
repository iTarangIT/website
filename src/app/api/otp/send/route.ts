import { NextRequest, NextResponse } from "next/server";
import { DEV_OTP_CODE, isValidIndianMobile, normalizePhone } from "@/lib/otp";
import { checkSendAllowed, isMockMode, recordSend, twoFactorSend } from "@/lib/otp-server";

const OTP_COOKIE = "itarang_otp_session";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const phone = typeof body?.phone === "string" ? body.phone : "";
  if (!isValidIndianMobile(phone)) {
    return NextResponse.json(
      { success: false, error: "Enter a valid 10-digit Indian mobile number" },
      { status: 400 },
    );
  }
  const e164 = normalizePhone(phone);

  const gate = checkSendAllowed(e164);
  if (!gate.allowed) {
    return NextResponse.json({ success: false, error: gate.error }, { status: 429 });
  }

  let sessionId: string;
  let mock = false;
  if (isMockMode()) {
    sessionId = "mock";
    mock = true;
    console.info(`[otp] MOCK send to ${e164} — code ${DEV_OTP_CODE}`);
  } else {
    const sent = await twoFactorSend(e164);
    if (!sent.success || !sent.sessionId) {
      return NextResponse.json(
        { success: false, error: sent.error ?? "Couldn't send the code. Please try again." },
        { status: sent.status ?? 502 },
      );
    }
    sessionId = sent.sessionId;
  }
  recordSend(e164);

  const res = NextResponse.json(mock ? { success: true, mock: true } : { success: true });
  res.cookies.set(OTP_COOKIE, sessionId, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 600,
    path: "/api/otp",
  });
  return res;
}
