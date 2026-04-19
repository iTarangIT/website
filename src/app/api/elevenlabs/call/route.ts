import { NextRequest, NextResponse } from "next/server";

const EL_BASE = "https://api.elevenlabs.io/v1/convai";

export async function POST(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { success: false, message: "ELEVENLABS_API_KEY not set on server" },
      { status: 500 },
    );
  }

  const body = await req.json().catch(() => null);
  if (!body?.agentId || !body?.phoneNumberId || !body?.toNumber) {
    return NextResponse.json(
      { success: false, message: "agentId, phoneNumberId and toNumber are required" },
      { status: 400 },
    );
  }

  const provider: "sip-trunk" | "twilio" = body.provider === "twilio" ? "twilio" : "sip-trunk";
  const endpoint = `${EL_BASE}/${provider}/outbound-call`;

  const payload: Record<string, unknown> = {
    agent_id: body.agentId,
    agent_phone_number_id: body.phoneNumberId,
    to_number: body.toNumber,
  };

  const clientData: Record<string, unknown> = {};

  // Dynamic variables substitute into {{placeholders}} in your agent's prompt/first_message.
  if (body.dynamicVariables && typeof body.dynamicVariables === "object") {
    // Stringify every value — ElevenLabs expects strings.
    const dv: Record<string, string> = {};
    for (const [k, v] of Object.entries(body.dynamicVariables as Record<string, unknown>)) {
      if (v === null || v === undefined) continue;
      dv[k] = String(v);
    }
    if (Object.keys(dv).length > 0) clientData.dynamic_variables = dv;
  }

  // Hard override of first_message — only used when the caller explicitly wants to replace
  // the agent's configured opener for this one call.
  if (body.initialMessage) {
    clientData.conversation_config_override = {
      agent: { first_message: body.initialMessage },
    };
  }

  if (Object.keys(clientData).length > 0) {
    payload.conversation_initiation_client_data = clientData;
  }

  let res: Response;
  try {
    res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "xi-api-key": apiKey,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
  } catch (e) {
    return NextResponse.json(
      { success: false, message: e instanceof Error ? e.message : "Network error calling ElevenLabs" },
      { status: 502 },
    );
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    return NextResponse.json(
      {
        success: false,
        message: data?.detail?.message || data?.message || `ElevenLabs HTTP ${res.status}`,
        raw: data,
      },
      { status: res.status },
    );
  }

  return NextResponse.json({
    success: Boolean(data.success ?? true),
    conversationId: data.conversation_id ?? data.conversationId ?? null,
    callSid: data.callSid ?? data.call_sid ?? null,
    message: data.message ?? "Call initiated",
  });
}
