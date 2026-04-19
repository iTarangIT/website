import { NextRequest, NextResponse } from "next/server";

// POST /api/intent-score — runs OpenAI (configurable model) over the current transcript
// + previous call history and returns a structured intent score.

const OPENAI_URL = "https://api.openai.com/v1/chat/completions";
// Default to a model that's widely available on standard OpenAI accounts and supports
// json_schema structured outputs. Override via OPENAI_INTENT_MODEL env var — e.g. set it
// to `gpt-4.1-mini`, `gpt-5-mini`, `gpt-5.1-mini` once your account has access.
const DEFAULT_MODEL = process.env.OPENAI_INTENT_MODEL ?? "gpt-4o-mini";

interface TranscriptTurn {
  role: "agent" | "user";
  message: string;
  timeInCallSec?: number;
}

interface PastCall {
  startedAt: number;
  durationSec?: number;
  terminationReason?: string;
  transcript: TranscriptTurn[];
  priorScoreOverall?: number;
}

interface ScoreRequest {
  lead: {
    name: string;
    phone: string;
    shopName?: string;
    city?: string;
    language?: string;
    interest?: string;
    persistentMemory?: string;
  };
  currentCall: {
    conversationId: string;
    durationSec?: number;
    terminationReason?: string;
    transcript: TranscriptTurn[];
  };
  previousCalls?: PastCall[];
}

function formatTranscript(turns: TranscriptTurn[]): string {
  if (!turns?.length) return "(no transcript captured)";
  return turns
    .map((t) => {
      const ts = typeof t.timeInCallSec === "number" ? `${Math.floor(t.timeInCallSec / 60)}:${String(Math.floor(t.timeInCallSec % 60)).padStart(2, "0")}` : "";
      const who = t.role === "user" ? "Lead" : "Agent";
      return `${ts ? `[${ts}] ` : ""}${who}: ${t.message}`;
    })
    .join("\n");
}

function daysAgo(ms: number): string {
  const delta = Date.now() - ms;
  const days = Math.floor(delta / (1000 * 60 * 60 * 24));
  if (days === 0) return "today";
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

const SYSTEM_PROMPT = `You are a sales-ops analyst for iTarang, an Indian company that sells lithium-ion EV batteries and financing to e-rickshaw fleet owners, battery retailers, and finance agents. You evaluate AI-dialer call transcripts and produce a qualification score used by the sales team to decide whether to invest ground time.

Score along five dimensions (each 0-100) and output an overall score (also 0-100). Be calibrated: a lead that clearly wants to buy, knows the product, has budget, and has a timeline should land around 85-95. A cold/confused lead should land below 30. Do not inflate scores.

Dimensions:
- intent: Does the lead show genuine willingness to engage further (meeting, demo, quote)? Signals: affirmative next steps, asking pricing, requesting a callback.
- productKnowledge: How much does the lead already know about lithium batteries / EV financing? Include their vocabulary, specificity (voltage, Ah, range), and any existing suppliers mentioned.
- customerRequirement: How clearly did they articulate what they need — use case, fleet size, existing pain, migration from lead-acid, volume?
- budgetReadiness: Any signal of budget — explicit amount, "within a month", comparison shopping, financing interest?
- timelineClarity: How soon do they plan to move — "today", "next week", "exploring", "year-end"?

Recommended action:
- qualify: overall ≥ 70 AND intent ≥ 65. Hand over to field sales immediately.
- nurture: overall 40-69. Re-dial in 3-7 days with updated context.
- disqualify: overall < 40 OR explicit "do not call". Remove from active pipeline.

Rationale must be 2-3 sentences of plain English calling out the strongest positive + the biggest gap. Include the lead's own words when useful. Write in the same language the lead primarily spoke (if mixed, default to English).

You will be given previous call history for the same lead. Weight the most recent call highest but use history to detect escalation/de-escalation of intent over time.`;

function buildUserPrompt(body: ScoreRequest): string {
  const lead = body.lead;
  const header = [
    `Lead name: ${lead.name}`,
    `Phone: ${lead.phone}`,
    lead.shopName ? `Shop / business: ${lead.shopName}` : null,
    lead.city ? `City: ${lead.city}` : null,
    lead.language ? `Language: ${lead.language}` : null,
    lead.interest ? `Interest: ${lead.interest}` : null,
    lead.persistentMemory ? `Persistent memory (long-lived context): ${lead.persistentMemory}` : null,
  ]
    .filter(Boolean)
    .join("\n");

  const prevCalls = (body.previousCalls ?? []).slice(-3); // last 3 calls max
  const prevBlock = prevCalls.length
    ? prevCalls
        .map(
          (c, i) =>
            `### Previous call ${i + 1} · ${daysAgo(c.startedAt)} · ${c.durationSec ?? "?"}s${c.terminationReason ? ` · ${c.terminationReason}` : ""}${
              typeof c.priorScoreOverall === "number" ? ` · prior overall ${c.priorScoreOverall}` : ""
            }\n${formatTranscript(c.transcript)}`,
        )
        .join("\n\n")
    : "No previous calls.";

  const currentBlock = `### Current call (just ended) · ${body.currentCall.durationSec ?? "?"}s${
    body.currentCall.terminationReason ? ` · ${body.currentCall.terminationReason}` : ""
  }\n${formatTranscript(body.currentCall.transcript)}`;

  return [
    `## Lead profile\n${header}`,
    `## Previous call history (older first)\n${prevBlock}`,
    `## Current call\n${currentBlock}`,
    "Score this lead now. Follow the rubric strictly. Return only the structured JSON object.",
  ].join("\n\n");
}

const JSON_SCHEMA = {
  name: "intent_score",
  strict: true,
  schema: {
    type: "object",
    additionalProperties: false,
    properties: {
      overall: { type: "integer", minimum: 0, maximum: 100 },
      dimensions: {
        type: "object",
        additionalProperties: false,
        properties: {
          intent: { type: "integer", minimum: 0, maximum: 100 },
          productKnowledge: { type: "integer", minimum: 0, maximum: 100 },
          customerRequirement: { type: "integer", minimum: 0, maximum: 100 },
          budgetReadiness: { type: "integer", minimum: 0, maximum: 100 },
          timelineClarity: { type: "integer", minimum: 0, maximum: 100 },
        },
        required: [
          "intent",
          "productKnowledge",
          "customerRequirement",
          "budgetReadiness",
          "timelineClarity",
        ],
      },
      rationale: { type: "string" },
      recommendedAction: {
        type: "string",
        enum: ["qualify", "nurture", "disqualify"],
      },
    },
    required: ["overall", "dimensions", "rationale", "recommendedAction"],
  },
} as const;

export async function POST(req: NextRequest) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "OPENAI_API_KEY not set on server" }, { status: 500 });
  }

  const body = (await req.json().catch(() => null)) as ScoreRequest | null;
  if (!body?.lead?.phone || !body?.currentCall?.conversationId) {
    return NextResponse.json({ error: "lead.phone and currentCall.conversationId are required" }, { status: 400 });
  }

  if (!body.currentCall.transcript || body.currentCall.transcript.length === 0) {
    return NextResponse.json({ error: "Current-call transcript is empty — cannot score." }, { status: 400 });
  }

  const model = DEFAULT_MODEL;
  const userPrompt = buildUserPrompt(body);

  let res: Response;
  try {
    res = await fetch(OPENAI_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: userPrompt },
        ],
        response_format: { type: "json_schema", json_schema: JSON_SCHEMA },
      }),
      cache: "no-store",
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Network error calling OpenAI" },
      { status: 502 },
    );
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return NextResponse.json(
      {
        error: data?.error?.message || `OpenAI HTTP ${res.status}`,
        raw: data,
      },
      { status: res.status },
    );
  }

  const text: string | undefined = data?.choices?.[0]?.message?.content;
  if (!text) {
    return NextResponse.json({ error: "OpenAI returned no content", raw: data }, { status: 502 });
  }

  let parsed: {
    overall: number;
    dimensions: {
      intent: number;
      productKnowledge: number;
      customerRequirement: number;
      budgetReadiness: number;
      timelineClarity: number;
    };
    rationale: string;
    recommendedAction: "qualify" | "nurture" | "disqualify";
  };
  try {
    parsed = JSON.parse(text);
  } catch {
    return NextResponse.json({ error: "OpenAI output was not valid JSON", raw: text }, { status: 502 });
  }

  return NextResponse.json({
    ...parsed,
    scoredAt: Date.now(),
    modelUsed: model,
  });
}
