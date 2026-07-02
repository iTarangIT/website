import { NextRequest, NextResponse } from "next/server";
import { DEV_OTP_CODE } from "@/lib/otp";
import { clearVerifyAttempts, isMockMode, recordVerifyAttempt, twoFactorVerify } from "@/lib/otp-server";

const OTP_COOKIE = "itarang_otp_session";

function clearCookie(res: NextResponse) {
  res.cookies.set(OTP_COOKIE, "", {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: 0,
    path: "/api/otp",
  });
  return res;
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const code = typeof body?.code === "string" ? body.code.trim() : "";
  if (!/^\d{6}$/.test(code)) {
    return NextResponse.json(
      { success: false, error: "Enter the 6-digit code" },
      { status: 400 },
    );
  }

  const sessionId = req.cookies.get(OTP_COOKIE)?.value;
  if (!sessionId) {
    return NextResponse.json(
      { success: false, error: "Your session expired. Please resend the code." },
      { status: 400 },
    );
  }

  if (!recordVerifyAttempt(sessionId)) {
    return clearCookie(
      NextResponse.json(
        { success: false, error: "Too many attempts. Please resend the code." },
        { status: 429 },
      ),
    );
  }

  let result: { success: boolean; error?: string; status?: number };
  if (sessionId.startsWith("mock-") && isMockMode()) {
    result =
      code === DEV_OTP_CODE
        ? { success: true }
        : { success: false, error: "Incorrect code. Please try again.", status: 400 };
  } else {
    result = await twoFactorVerify(sessionId, code);
  }

  if (result.success) {
    clearVerifyAttempts(sessionId);
    return clearCookie(NextResponse.json({ success: true }));
  }
  return NextResponse.json(
    { success: false, error: result.error ?? "Verification failed. Please try again." },
    { status: result.status ?? 400 },
  );
}
