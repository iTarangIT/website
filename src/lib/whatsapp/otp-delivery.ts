// WhatsApp OTP delivery via the Meta Cloud API adapter.
//
// Ported from the CRM's src/lib/calculator/whatsapp.ts, decoupled from the CRM's
// DB message-logging (logOutbound writes to a whatsappMessages table that does
// not exist here — replaced with a console log).
//
// ⚠️ DELIVERY RULE (the usual reason "WhatsApp OTP isn't working"):
// A business-initiated WhatsApp message to someone who has NOT messaged your
// number in the last 24h is ONLY delivered if you send a PRE-APPROVED template.
// Free-form sendText silently fails (or returns error 131047 / 131026) outside
// that 24h window. For OTP you almost always need an approved AUTHENTICATION
// template. Set CALC_OTP_WA_TEMPLATE to its name; leave it unset only for local
// testing against a number that just messaged your test line.

import { getAdapter } from "./index";
import type { SendResult } from "./types";

/**
 * Normalize an Indian mobile to "91XXXXXXXXXX" (Meta wants E.164 without '+').
 * Returns null when it is not a valid 10-digit Indian mobile.
 */
export function normalizeWaPhone(raw: string): string | null {
  const digits = (raw ?? "").replace(/\D/g, "");
  if (digits.length === 10) return `91${digits}`;
  if (digits.length === 11 && digits.startsWith("0")) return `91${digits.slice(1)}`;
  if (digits.length === 12 && digits.startsWith("91")) return digits;
  return null;
}

export function maskWaPhone(normalized: string): string {
  return `XXXXXX${normalized.slice(-4)}`;
}

/** True when the Meta Cloud API credentials are present. */
export function metaWhatsAppConfigured(): boolean {
  return !!(
    process.env.META_WA_ACCESS_TOKEN?.trim() &&
    process.env.META_WA_PHONE_NUMBER_ID?.trim()
  );
}

/**
 * Send a 6-digit OTP to the customer's WhatsApp.
 * Uses the approved template when CALC_OTP_WA_TEMPLATE is set (required outside
 * the 24h window); otherwise falls back to free-form text (dev/test only).
 * Caller surfaces any failure to the user.
 */
export async function sendOtpWhatsApp(
  phone: string,
  otp: string,
  customerName: string,
): Promise<SendResult> {
  const adapter = getAdapter();
  const template = process.env.CALC_OTP_WA_TEMPLATE?.trim();

  let res: SendResult;
  if (template) {
    // Authentication templates take the code as the single body parameter.
    res = await adapter.sendTemplate(
      phone,
      template,
      process.env.CALC_OTP_WA_TEMPLATE_LANG?.trim() || "en",
      [otp],
    );
  } else {
    const body =
      `Hi ${customerName || "there"}, your iTarang verification code is *${otp}*.\n\n` +
      `It is valid for 10 minutes. Do not share it with anyone.`;
    res = await adapter.sendText(phone, body);
  }

  if (!res.ok) {
    console.error(
      `[whatsapp-otp] delivery to ${maskWaPhone(phone)} failed: ${res.error ?? "unknown"}`,
    );
  }
  return res;
}

// ── Scheme results summary ──────────────────────────────────────────────────
// Ported from the CRM's src/lib/calculator/whatsapp.ts (DB message-logging
// dropped). Sent after a verified calculation so the customer keeps the schemes
// on their WhatsApp. Best-effort — never throws.

interface SchemeForSummary {
  nbfc: string;
  schemeCode: string;
  tenure: number;
  remainingMonths: number;
  advance: number;
  priceToDriver: number;
  loanAmount: number;
  emi: number;
  totalUpfront: number;
  estimatedTotalPayable: number;
  tier: "qualified" | "stretch";
  recommended?: boolean;
  recommendationLabel?: string;
  breakdown: {
    downPayment: number;
    advanceInstallmentsTotal: number;
    nbfcFileFee: number;
    processingFee: number;
    interestChargedUpfront: number;
    advanceInterest: number;
  };
}
export interface CalcResultForSummary {
  outcome: "qualified" | "stretch_only" | "none";
  qualified: SchemeForSummary[];
  stretch: SchemeForSummary[];
}

const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

// The same "Other upfront charges" figure the on-screen scheme card shows.
const otherUpfront = (s: SchemeForSummary) =>
  s.breakdown.nbfcFileFee +
  s.breakdown.processingFee +
  s.breakdown.interestChargedUpfront +
  s.breakdown.advanceInterest;

/** One scheme rendered as a WhatsApp text block — mirrors the results card. */
function schemeBlock(s: SchemeForSummary): string {
  const rows = [
    `${s.recommended ? "⭐ " : ""}*${s.nbfc}* (Scheme ${s.schemeCode})${
      s.recommended && s.recommendationLabel ? ` — ${s.recommendationLabel}` : ""
    }`,
    `Tenure: ${s.tenure} months${s.advance > 0 ? ` · ${s.advance} advance EMI` : ""}`,
    `EMI: ${inr(s.emi)}/month × ${s.remainingMonths}`,
    `Asset price: ${inr(s.priceToDriver)}`,
    `Loan amount: ${inr(s.loanAmount)}`,
    `Down payment: ${inr(s.breakdown.downPayment)}`,
  ];
  if (s.breakdown.advanceInstallmentsTotal > 0) {
    rows.push(`Advance instalments (${s.advance}): ${inr(s.breakdown.advanceInstallmentsTotal)}`);
  }
  rows.push(`Other upfront charges: ${inr(otherUpfront(s))}`);
  rows.push(`*Total payable today: ${inr(s.totalUpfront)}*`);
  rows.push(`Est. total payable: ${inr(s.estimatedTotalPayable)} (upfront + EMIs)`);
  rows.push(s.tier === "stretch" ? "_Closest to qualifying_" : "✅ Qualifies for this customer");
  return rows.join("\n");
}

export type ResultsSendStatus = "sent" | "failed" | "skipped";

/**
 * Send the scheme results summary to the customer's WhatsApp. Uses the approved
 * template when CALC_RESULTS_WA_TEMPLATE is set (body params
 * [customerName, modelName, schemesSingleLine]); otherwise free-form text
 * (dev/test, or when the customer has an open 24h WhatsApp session — which they
 * do if the free-form OTP just reached them).
 */
export async function sendCalcResultsWhatsApp(
  phone: string,
  customerName: string,
  result: CalcResultForSummary,
  modelName: string,
): Promise<ResultsSendStatus> {
  try {
    if (!metaWhatsAppConfigured()) return "skipped";

    const adapter = getAdapter();
    const template = process.env.CALC_RESULTS_WA_TEMPLATE?.trim();
    const schemes = (result.qualified.length > 0 ? result.qualified : result.stretch).slice(0, 3);

    const heading =
      result.qualified.length > 0
        ? "here are the EMI schemes you qualify for"
        : result.stretch.length > 0
          ? "here are the schemes closest to your budget"
          : "no schemes matched your filters right now";

    let res: SendResult;
    if (template) {
      // Meta bans newlines in body params — full detail joined on one line.
      const line =
        schemes.length > 0
          ? schemes
              .map(
                (s) =>
                  `${s.nbfc} ${s.schemeCode} (${s.tenure}m): EMI ${inr(s.emi)}/m x ${s.remainingMonths}, ` +
                  `asset ${inr(s.priceToDriver)}, loan ${inr(s.loanAmount)}, ` +
                  `down ${inr(s.breakdown.downPayment)}, other upfront ${inr(otherUpfront(s))}, ` +
                  `pay today ${inr(s.totalUpfront)}, est total ${inr(s.estimatedTotalPayable)}`,
              )
              .join(" | ")
          : "No schemes matched your filters - please contact your dealer";
      res = await adapter.sendTemplate(
        phone,
        template,
        process.env.CALC_RESULTS_WA_TEMPLATE_LANG?.trim() || "en",
        [customerName || "there", modelName, line],
      );
    } else {
      const blocks = schemes.map(schemeBlock);
      const body =
        `Hi ${customerName || "there"}, ${heading} — *${modelName}*:\n\n` +
        (blocks.length > 0 ? `${blocks.join("\n\n————————\n\n")}\n\n` : "") +
        `_Figures are indicative and subject to NBFC approval._\n` +
        `Please contact your iTarang dealer to proceed.`;
      res = await adapter.sendText(phone, body);
    }

    if (!res.ok) {
      console.error(
        `[whatsapp-otp] results send to ${maskWaPhone(phone)} failed: ${res.error ?? "unknown"}`,
      );
    }
    return res.ok ? "sent" : "failed";
  } catch (err) {
    console.error("[whatsapp-otp] results send threw:", err);
    return "failed";
  }
}
