import { NextRequest, NextResponse } from "next/server";
import { OTP_SESSION_COOKIE, verifyOtp } from "@/lib/whatsapp/otp-store";
import {
  CALC_COOKIE_MAX_AGE_S,
  CALC_VERIFIED_COOKIE,
  signVerifiedCookie,
} from "@/lib/calc-gate";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Public WhatsApp OTP — VERIFY. Hash-compares the entered code against the
// cookie session (3 attempts, 5-min lockout, 10-min expiry — enforced in the
// store). On success the session is marked verified.
export async function POST(req: NextRequest) {
  let body: { code?: unknown; otp?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ success: false, error: "Invalid request." }, { status: 400 });
  }

  // Accept either { code } (matches the site's SMS client) or { otp }.
  const raw = typeof body.code === "string" ? body.code : typeof body.otp === "string" ? body.otp : "";
  const code = raw.trim();
  if (!/^\d{6}$/.test(code)) {
    return NextResponse.json({ success: false, error: "Enter the 6-digit code" }, { status: 400 });
  }

  const sessionId = req.cookies.get(OTP_SESSION_COOKIE)?.value;
  const result = verifyOtp(sessionId, code);
  if (!result.ok) {
    return NextResponse.json({ success: false, error: result.message, code: result.code }, { status: result.status });
  }

  // Clear the session cookie now that it's spent for verification.
  const res = NextResponse.json({ success: true, data: { verified: true } });
  res.cookies.set(OTP_SESSION_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 0,
    path: "/api/whatsapp-otp",
  });

  // Mint the signed cookie the public /api/calculator/calculate route requires.
  // The store returns the phone as "91XXXXXXXXXX"; the calculator gate compares
  // against normalizePhone() output ("+91XXXXXXXXXX"), so prefix the "+".
  const e164 = result.phone.startsWith("+") ? result.phone : `+${result.phone}`;
  const signed = signVerifiedCookie(e164);
  if (signed) {
    res.cookies.set(CALC_VERIFIED_COOKIE, signed, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      maxAge: CALC_COOKIE_MAX_AGE_S,
      path: "/api/calculator",
    });
  }
  return res;
}
