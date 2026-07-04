import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { db } from "@/lib/db";
import { calcLeads } from "@/lib/db/schema";
import { resolveEngineContext } from "@/lib/calculator/config-resolver";
import { calculate, ValidationError, rupeesToPaise } from "@/lib/calculator/engine";
import { isValidIndianMobile, normalizePhone } from "@/lib/otp";
import {
  CALC_VERIFIED_COOKIE,
  checkCalcAllowed,
  getClientIp,
  verifyVerifiedCookie,
} from "@/lib/calc-gate";
import { sendCalcResultsWhatsApp, sendOnboardingPrompt } from "@/lib/whatsapp/otp-delivery";

export const dynamic = "force-dynamic";
export const runtime = "nodejs"; // postgres-js cannot run on the edge runtime

// Same contract as the CRM dealer route (kept verbatim so numbers/shapes match).
const bodySchema = z.object({
  customerName: z.string().min(1, "Customer name is required"),
  phone: z.string().min(5, "Phone is required"),
  city: z.string().nullable().optional(),
  modelId: z.number().int().positive(),
  tenure: z.number().int().positive(),
  expectedEmi: z.number().nonnegative().optional(),
  upfrontAbility: z.number().nonnegative().optional(),
});

function fail(status: number, message: string, code?: string, field?: string) {
  return NextResponse.json(
    {
      success: false,
      error: { message, ...(code ? { code } : {}), ...(field ? { field } : {}) },
      timestamp: new Date().toISOString(),
    },
    { status },
  );
}

// Card 1 -> Card 2 for the PUBLIC website: verify the signed OTP cookie, rate
// limit, resolve config, run the verified engine, persist the lead, return cards.
export async function POST(req: NextRequest) {
  let body: z.infer<typeof bodySchema>;
  try {
    body = bodySchema.parse(await req.json());
  } catch (e) {
    const issue = e instanceof z.ZodError ? e.issues[0] : null;
    return fail(400, issue?.message ?? "Invalid request.", "validation_error", issue?.path?.join("."));
  }

  if (!isValidIndianMobile(body.phone)) {
    return fail(400, "Enter a valid 10-digit Indian mobile number.", "invalid_phone");
  }
  const phone = normalizePhone(body.phone);

  // OTP gate: the phone must carry the signed cookie minted by /api/whatsapp-otp/verify.
  const cookie = req.cookies.get(CALC_VERIFIED_COOKIE)?.value;
  if (!verifyVerifiedCookie(cookie, phone)) {
    return fail(403, "Phone not verified. Please verify your number with the OTP first.", "verification_required");
  }

  const gate = checkCalcAllowed(getClientIp(req), phone);
  if (!gate.allowed) {
    return fail(429, gate.error, "rate_limited");
  }

  try {
    const resolved = await resolveEngineContext({ modelId: body.modelId, city: body.city });

    let result;
    try {
      result = calculate(resolved.ctx, {
        model: resolved.model.displayName,
        tenure: body.tenure,
        expectedEmi: body.expectedEmi,
        upfrontAbility: body.upfrontAbility,
        city: body.city ?? undefined,
      });
    } catch (e) {
      // Map the engine's required-filter/negative validation to a structured 400 (not a 500).
      if (e instanceof ValidationError) {
        return fail(400, e.message, undefined, e.field);
      }
      throw e;
    }

    // Persist the quote. dealer_id NULL = website/public lead.
    const [lead] = await db
      .insert(calcLeads)
      .values({
        dealerId: null,
        customerName: body.customerName,
        phone,
        city: body.city ?? null,
        expectedEmiPaise: body.expectedEmi != null ? rupeesToPaise(body.expectedEmi) : null,
        upfrontAbilityPaise: body.upfrontAbility != null ? rupeesToPaise(body.upfrontAbility) : null,
        tenureMonths: body.tenure,
        modelId: body.modelId,
        filterOutcome: result.outcome,
        configVersionId: resolved.configVersionId,
        resultSnapshot: result,
        otpVerificationId: null,
        otpVerifiedAt: null,
      })
      .returning({ id: calcLeads.id });

    // Deliver the schemes to the verified customer's WhatsApp (best-effort).
    const waResults = await sendCalcResultsWhatsApp(
      phone,
      body.customerName,
      result,
      resolved.model.displayName,
    );

    // Follow up with the onboarding ("new lead") button, but only when there
    // was an actual scheme to act on. Tapping it starts the in-chat flow.
    if (waResults === "sent" && result.outcome !== "none") {
      await sendOnboardingPrompt(phone, body.customerName, resolved.model.displayName, lead.id);
    }

    const okRes = NextResponse.json({
      success: true,
      data: {
        ...result,
        model: resolved.model,
        configVersionId: resolved.configVersionId,
        footer: resolved.footer,
        cardDisclaimer: resolved.cardDisclaimer,
        leadId: lead.id,
        waResults,
      },
      timestamp: new Date().toISOString(),
    });
    // Single-use verification: consume the signed cookie so the NEXT search
    // requires a fresh WhatsApp OTP (enforced server-side, not just in the UI).
    okRes.cookies.set(CALC_VERIFIED_COOKIE, "", {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      maxAge: 0,
      path: "/api/calculator",
    });
    return okRes;
  } catch (err) {
    console.error("[calculator/calculate]", err);
    return fail(500, "Calculation failed. Please try again.");
  }
}
