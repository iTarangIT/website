import { NextRequest, NextResponse } from "next/server";
import { OTP_SESSION_COOKIE, verifySmsOtp } from "@/lib/otp/two-factor";
import {
  CALC_COOKIE_MAX_AGE_S,
  CALC_VERIFIED_COOKIE,
  signVerifiedCookie,
} from "@/lib/calc-gate";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

// Public OTP — VERIFY. Checks the entered code against the 2Factor session
// bound to the cookie (attempts/lockout/expiry enforced in two-factor.ts). On
// success it mints the signed calculator cookie required by /api/calculator.
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
  const result = await verifySmsOtp(sessionId, code);
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
  // two-factor.ts stores the phone as "+91XXXXXXXXXX", which is exactly what
  // normalizePhone() (used by the calculator gate) produces.
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
