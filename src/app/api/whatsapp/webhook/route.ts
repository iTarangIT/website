import { NextRequest, NextResponse } from "next/server";
import { getAdapter } from "@/lib/whatsapp";
import { handleOnboardingInbound } from "@/lib/whatsapp/onboarding-flow";

export const dynamic = "force-dynamic";
export const runtime = "nodejs"; // Meta adapter uses node crypto + fetch

// Inbound WhatsApp webhook — the ONLY endpoint that receives customer messages
// and button taps. It drives the in-chat customer-onboarding conversation.
//
// Meta setup (once): in the WhatsApp app → Configuration, set the Callback URL
// to  https://<your-domain>/api/whatsapp/webhook  and the Verify Token to
// META_WA_VERIFY_TOKEN, then Subscribe to the "messages" field. Locally, expose
// the dev server (e.g. ngrok) and set WHATSAPP_WEBHOOK_INSECURE=true to skip
// signature checks.

// GET — Meta's subscription handshake. Echo hub.challenge when the verify token
// matches, else 403.
export async function GET(req: NextRequest) {
  const challenge = getAdapter().verifyChallenge(new URL(req.url));
  if (challenge === null) {
    return new NextResponse("Forbidden", { status: 403 });
  }
  return new NextResponse(challenge, {
    status: 200,
    headers: { "Content-Type": "text/plain" },
  });
}

// Dedupe: Meta re-delivers a webhook until it gets a 2xx, so the same
// providerMessageId can arrive several times. Track a bounded ring of ids seen
// this process so we don't answer the same message twice.
const seen = new Set<string>();
const SEEN_MAX = 1000;
function alreadyHandled(id: string): boolean {
  if (seen.has(id)) return true;
  seen.add(id);
  if (seen.size > SEEN_MAX) {
    // Drop the oldest ~10% (insertion order) to bound memory.
    const drop = Math.floor(SEEN_MAX * 0.1);
    let i = 0;
    for (const k of seen) {
      if (i++ >= drop) break;
      seen.delete(k);
    }
  }
  return false;
}

// POST — inbound events. Verify the signature against the RAW body, parse to
// canonical events, and route text/interactive replies into the onboarding
// engine. Always return 200 on authentic payloads (even when we take no action)
// so Meta stops retrying; only a bad signature returns 403.
export async function POST(req: NextRequest) {
  const rawBody = await req.text();
  const adapter = getAdapter();

  if (!adapter.verifyInbound(req.headers, rawBody)) {
    console.error("[wa-webhook] signature verification failed — rejecting");
    return new NextResponse("Forbidden", { status: 403 });
  }

  const events = adapter.parseInbound(rawBody);
  for (const ev of events) {
    // Ignore delivery receipts, unsupported types, and anything without a body.
    if (ev.type !== "text" && ev.type !== "interactive") continue;
    if (!ev.waPhone) continue;
    if (ev.providerMessageId && alreadyHandled(ev.providerMessageId)) continue;

    try {
      const replies = await handleOnboardingInbound(ev.waPhone, ev.text ?? "", ev.contactName);
      for (const r of replies) {
        const res = await adapter.sendText(ev.waPhone, r.body);
        if (!res.ok) {
          console.error(`[wa-webhook] reply send failed: ${res.error ?? "unknown"}`);
        }
      }
    } catch (err) {
      // Never let one message fail the whole batch — Meta would retry all of it.
      console.error("[wa-webhook] handler threw:", err);
    }
  }

  return NextResponse.json({ received: true });
}
