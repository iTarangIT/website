import { NextRequest, NextResponse } from "next/server";

const EL_BASE = "https://api.elevenlabs.io/v1/convai";

export async function GET(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { ok: false, error: "ELEVENLABS_API_KEY not set on server" },
      { status: 500 },
    );
  }

  const agentId = req.nextUrl.searchParams.get("agentId");
  if (!agentId) return NextResponse.json({ ok: false, error: "Missing agentId" }, { status: 400 });

  let res: Response;
  try {
    res = await fetch(`${EL_BASE}/agents/${encodeURIComponent(agentId)}`, {
      headers: { "xi-api-key": apiKey },
      cache: "no-store",
    });
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: e instanceof Error ? e.message : "Network error" },
      { status: 502 },
    );
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return NextResponse.json(
      { ok: false, error: data?.message || `HTTP ${res.status}` },
      { status: res.status },
    );
  }

  return NextResponse.json({
    ok: true,
    agentName: data.name ?? data.agent_name ?? "Unnamed agent",
  });
}
