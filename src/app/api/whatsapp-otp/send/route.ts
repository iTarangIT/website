import { NextRequest, NextResponse } from "next/server";
import {
  maskWaPhone,
  metaWhatsAppConfigured,
  normalizeWaPhone,
  sendOtpWhatsApp,
} from "@/lib/whatsapp/otp-delivery";
import { OTP_SESSION_COOKIE, issueOtp } from "@/lib/whatsapp/otp-store";

export const dynamic = "force-dynamic";
export const runtime = "nodejs"; // the Meta adapter uses node crypto + fetch

// Public WhatsApp OTP — SEND. Generates a 6-digit code, stores its hash in a
// cookie-keyed session, and delivers it to the customer's WhatsApp via Meta.
export async function POST(req: NextRequest) {
  let body: { phone?: unknown; customerName?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ success: false, error: "Invalid request." }, { status: 400 });
  }

  const phone = normalizeWaPhone(typeof body.phone === "string" ? body.phone : "");
  if (!phone) {
    return NextResponse.json(
      { success: false, error: "Enter a valid 10-digit Indian mobile number." },
      { status: 400 },
    );
  }
  const customerName = typeof body.customerName === "string" ? body.customerName.trim() : "";

  // Dev shortcut: without live Meta creds, use a fixed OTP so the flow is
  // testable end-to-end. Verification still hash-compares through the same path.
  const waConfigured = metaWhatsAppConfigured();
  const otp = waConfigured ? Math.floor(100000 + Math.random() * 900000).toString() : "123456";

  const existingSessionId = req.cookies.get(OTP_SESSION_COOKIE)?.value;
  const issued = issueOtp(existingSessionId, phone, customerName, otp);
  if (!issued.ok) {
    return NextResponse.json({ success: false, error: issued.message, code: issued.code }, { status: 429 });
  }

  let waStatus: "sent" | "dev_hardcoded" = "dev_hardcoded";
  if (waConfigured) {
    const res = await sendOtpWhatsApp(phone, otp, customerName);
    if (!res.ok) {
      return NextResponse.json(
        {
          success: false,
          error: `WhatsApp delivery failed: ${res.error || "unknown error"}`,
          code: "wa_failed",
        },
        { status: 502 },
      );
    }
    waStatus = "sent";
  } else {
    console.log(`[whatsapp-otp] Meta not configured — dev OTP ${otp} for ${maskWaPhone(phone)}`);
  }

  const isDev = process.env.NODE_ENV !== "production";
  const res = NextResponse.json({
    success: true,
    data: {
      otpSentTo: maskWaPhone(phone),
      sendCount: issued.sendCount,
      maxSends: issued.maxSends,
      expiresInSeconds: issued.expiresInSeconds,
      waStatus,
      // Surface the OTP only when running the dev shortcut so a tester can
      // complete the flow without a real WhatsApp message.
      ...(waStatus === "dev_hardcoded" && isDev ? { _devOtp: otp } : {}),
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
