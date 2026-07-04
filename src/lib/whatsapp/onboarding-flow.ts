// Customer onboarding ("new lead") conversation, driven entirely inside
// WhatsApp. The customer taps the onboarding button under their EMI schemes;
// this state machine then walks them through a few questions and records a
// lead-ready summary.
//
// The flow is DECLARATIVE: add/remove/reorder a question by editing STEPS. Each
// step validates the reply and stores it under `key`. The engine
// (handleOnboardingInbound) is provider-agnostic — it returns the text to send
// back, and the webhook route delivers it via the WhatsApp adapter.

import {
  type OnboardingSession,
  getOnboarding,
  saveOnboarding,
  seedOnboarding,
} from "./onboarding-store";
import { persistOnboardingLead } from "./onboarding-lead";

/** Interactive-reply id carried on the onboarding button (echoed as text). */
export const ONBOARDING_START_ID = "onboarding_start";

/** Words that let the customer bail out mid-flow. */
const CANCEL_WORDS = new Set(["cancel", "stop", "quit", "exit"]);

type Validation = { ok: true; value: string } | { ok: false; error: string };

interface OnboardingStep {
  key: string;
  /** Question shown to the customer. `s` is the session (for pre-fill/context). */
  prompt: (s: OnboardingSession) => string;
  /** Validate + normalize the raw reply. */
  validate: (raw: string) => Validation;
}

const required =
  (label: string, min = 2) =>
  (raw: string): Validation => {
    const value = raw.trim();
    if (value.length < min) return { ok: false, error: `Please enter a valid ${label}.` };
    return { ok: true, value };
  };

// ── The questions ───────────────────────────────────────────────────────────
// Keep it short: the calculator already captured name, phone, city, model and
// the chosen schemes. This collects only what converting to a lead needs.
const STEPS: OnboardingStep[] = [
  {
    key: "fullName",
    prompt: (s) =>
      s.customerName
        ? `Please confirm your full name (as per your ID). We have *${s.customerName}* — reply with it or send the correct name.`
        : "What is your full name (as per your ID)?",
    validate: required("name"),
  },
  {
    key: "pincode",
    prompt: () => "What is your 6-digit delivery pincode?",
    validate: (raw) => {
      const digits = raw.replace(/\D/g, "");
      if (!/^\d{6}$/.test(digits)) return { ok: false, error: "Please send a valid 6-digit pincode." };
      return { ok: true, value: digits };
    },
  },
  {
    key: "email",
    prompt: () => "What is your email address? (or reply *skip* if you'd rather not share it)",
    validate: (raw) => {
      const value = raw.trim();
      if (/^skip$/i.test(value)) return { ok: true, value: "" };
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
        return { ok: false, error: "That doesn't look like a valid email. Send a valid email or reply *skip*." };
      return { ok: true, value };
    },
  },
];

/** A message the engine wants the webhook to send back to the customer. */
export interface OutboundReply {
  body: string;
}

function reply(body: string): OutboundReply[] {
  return [{ body }];
}

/** Human-readable recap of everything collected, sent at completion. */
function summary(s: OnboardingSession): string {
  const lines = [
    "✅ *Thank you!* We've received your application details:",
    "",
    `• Name: ${s.answers.fullName ?? s.customerName}`,
    `• Phone: +${s.phone}`,
    `• Pincode: ${s.answers.pincode ?? "-"}`,
  ];
  if (s.answers.email) lines.push(`• Email: ${s.answers.email}`);
  if (s.modelName) lines.push(`• Battery: ${s.modelName}`);
  lines.push(
    "",
    "Our iTarang team will contact you shortly to complete your onboarding and finalise your finance option.",
  );
  return lines.join("\n");
}

/** First message once the flow starts (button tapped). */
function greeting(s: OnboardingSession): string {
  return (
    `Great, let's get you started! 🎉\n\n` +
    `We'll ask a few quick questions to create your application. You can reply *cancel* anytime.\n\n` +
    STEPS[0].prompt(s)
  );
}

/**
 * Advance the onboarding conversation for one inbound customer message.
 *
 * @param phone    normalized "91XXXXXXXXXX"
 * @param text     the customer's message body, or the tapped button/list id
 * @param contactName  WhatsApp profile name, used only as a name fallback
 * @returns the reply message(s) to send back (empty = stay silent)
 */
export async function handleOnboardingInbound(
  phone: string,
  text: string,
  contactName?: string,
): Promise<OutboundReply[]> {
  const raw = (text ?? "").trim();
  let session = getOnboarding(phone);

  // ── Start trigger: the onboarding button was tapped ───────────────────────
  if (raw === ONBOARDING_START_ID) {
    // Resilience: if the "prompted" seed expired, start from the profile name.
    if (!session) {
      seedOnboarding(phone, { customerName: contactName ?? "", modelName: null, leadId: null });
      session = getOnboarding(phone)!;
    }
    // Re-tapping a finished flow shouldn't wipe it.
    if (session.status === "completed") {
      return reply("You've already shared your details — our team will reach out soon. 🙏");
    }
    session.status = "active";
    session.stepIndex = 0;
    session.answers = {};
    saveOnboarding(session);
    return reply(greeting(session));
  }

  // Only engage further when a conversation is actually in progress.
  if (!session || session.status !== "active") return [];

  // ── Cancel ────────────────────────────────────────────────────────────────
  if (CANCEL_WORDS.has(raw.toLowerCase())) {
    session.status = "prompted"; // back to "can tap again" without losing context
    session.stepIndex = 0;
    session.answers = {};
    saveOnboarding(session);
    return reply("No problem — your application has been cancelled. Tap the onboarding button again whenever you're ready.");
  }

  // ── Validate the current step, then advance ───────────────────────────────
  const step = STEPS[session.stepIndex];
  if (!step) {
    // Shouldn't happen; treat as completed.
    session.status = "completed";
    saveOnboarding(session);
    return reply(summary(session));
  }

  const result = step.validate(raw);
  if (!result.ok) {
    // Re-ask the same question with the validation hint.
    return reply(`${result.error}\n\n${step.prompt(session)}`);
  }

  session.answers[step.key] = result.value;
  session.stepIndex += 1;

  const next = STEPS[session.stepIndex];
  if (next) {
    saveOnboarding(session);
    return reply(next.prompt(session));
  }

  // All steps answered — promote the quote row into a completed lead by writing
  // the collected details back onto calc_leads (see onboarding-lead.ts).
  session.status = "completed";
  saveOnboarding(session);
  const persisted = await persistOnboardingLead(session);
  console.log(
    `[wa-onboarding] completed for +${phone} (lead ${session.leadId ?? "n/a"}, ` +
      `persisted=${persisted}):`,
    JSON.stringify(session.answers),
  );
  return reply(summary(session));
}
