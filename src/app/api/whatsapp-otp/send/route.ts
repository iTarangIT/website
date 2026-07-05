import { NextRequest, NextResponse } from "next/server";
import { isValidIndianMobile, normalizePhone } from "@/lib/otp";
import { OTP_SESSION_COOKIE, issueSmsOtp, maskPhone } from "@/lib/otp/two-factor";

export const dynamic = "force-dynamic";
export const runtime = "nodejs"; // crypto.randomUUID + fetch

// Public OTP — SEND. Delivers a 6-digit code by SMS via 2Factor.in (AUTOGEN:
// the provider generates + sends + stores the code). We keep only 2Factor's
// session id, bound to the phone in an httpOnly cookie session.
export async function POST(req: NextRequest) {
  let body: { phone?: unknown; customerName?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ success: false, error: "Invalid request." }, { status: 400 });
  }

  const rawPhone = typeof body.phone === "string" ? body.phone : "";
  if (!isValidIndianMobile(rawPhone)) {
    return NextResponse.json(
      { success: false, error: "Enter a valid 10-digit Indian mobile number." },
      { status: 400 },
    );
  }
  const phone = normalizePhone(rawPhone); // +91XXXXXXXXXX
  const customerName = typeof body.customerName === "string" ? body.customerName.trim() : "";

  const existingSessionId = req.cookies.get(OTP_SESSION_COOKIE)?.value;
  const issued = await issueSmsOtp(existingSessionId, phone, customerName);
  if (!issued.ok) {
    return NextResponse.json(
      { success: false, error: issued.message, code: issued.code },
      { status: issued.status },
    );
  }

  const res = NextResponse.json({
    success: true,
    data: {
      otpSentTo: maskPhone(phone),
      sendCount: issued.sendCount,
      maxSends: issued.maxSends,
      expiresInSeconds: issued.expiresInSeconds,
      // "dev_hardcoded" keeps the client's mock-hint contract (shows "Dev code").
      waStatus: issued.mock ? "dev_hardcoded" : "sent",
    },
  });
  res.cookies.set(OTP_SESSION_COOKIE, issued.sessionId, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 40 * 60, // 10-min OTP + up to 30-min cooldown
    path: "/api/whatsapp-otp",
  });
  return res;
}
