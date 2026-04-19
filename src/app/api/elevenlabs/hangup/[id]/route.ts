import { NextRequest, NextResponse } from "next/server";

const EL_BASE = "https://api.elevenlabs.io/v1/convai";

export async function POST(_req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "ELEVENLABS_API_KEY not set on server" }, { status: 500 });
  }

  const { id } = await ctx.params;
  if (!id) return NextResponse.json({ error: "Missing conversation id" }, { status: 400 });

  // ElevenLabs end-call endpoint. If the API rejects, return the upstream status.
  let res: Response;
  try {
    res = await fetch(`${EL_BASE}/conversations/${encodeURIComponent(id)}/cancel`, {
      method: "POST",
      headers: { "xi-api-key": apiKey },
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Network error" },
      { status: 502 },
    );
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    return NextResponse.json({ ok: false, error: data?.message || `HTTP ${res.status}` }, { status: res.status });
  }

  return NextResponse.json({ ok: true });
}
