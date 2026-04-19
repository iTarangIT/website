import { NextRequest, NextResponse } from "next/server";

const EL_BASE = "https://api.elevenlabs.io/v1/convai";

interface TranscriptTurnRaw {
  role?: string;
  message?: string;
  time_in_call_secs?: number;
}

export async function GET(_req: NextRequest, ctx: { params: Promise<{ id: string }> }) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "ELEVENLABS_API_KEY not set on server" }, { status: 500 });
  }

  const { id } = await ctx.params;
  if (!id) return NextResponse.json({ error: "Missing conversation id" }, { status: 400 });

  let res: Response;
  try {
    res = await fetch(`${EL_BASE}/conversations/${encodeURIComponent(id)}`, {
      headers: { "xi-api-key": apiKey },
      cache: "no-store",
    });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Network error" },
      { status: 502 },
    );
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return NextResponse.json({ error: data?.message || `HTTP ${res.status}`, raw: data }, { status: res.status });
  }

  const rawStatus: string = typeof data.status === "string" ? data.status : "unknown";
  const status =
    rawStatus === "initiated" || rawStatus === "in-progress" || rawStatus === "in_progress"
      ? "in-progress"
      : rawStatus === "processing"
      ? "processing"
      : rawStatus === "done" || rawStatus === "ended" || rawStatus === "completed"
      ? "ended"
      : rawStatus === "failed" || rawStatus === "error"
      ? "failed"
      : "unknown";

  const turns: TranscriptTurnRaw[] = Array.isArray(data.transcript)
    ? data.transcript
    : Array.isArray(data.messages)
    ? data.messages
    : [];

  const transcript = turns
    .map((t) => ({
      role: (t.role === "user" || t.role === "customer" || t.role === "caller" ? "user" : "agent") as
        | "agent"
        | "user",
      message: String(t.message ?? "").trim(),
      timeInCallSec: typeof t.time_in_call_secs === "number" ? t.time_in_call_secs : undefined,
    }))
    .filter((t) => t.message.length > 0);

  const durationSec: number | undefined =
    data.metadata?.call_duration_secs ??
    data.metadata?.duration_secs ??
    data.metadata?.call_duration_seconds ??
    undefined;

  const recordingUrl: string | undefined =
    data.metadata?.recording_url ??
    data.recording_url ??
    undefined;

  // Termination reason — ElevenLabs places this under several possible fields depending on
  // the conversation phase. Check them in order.
  const terminationReason: string | undefined =
    data.metadata?.termination_reason ??
    data.metadata?.call_summary_title ??
    data.analysis?.termination_reason ??
    data.analysis?.call_summary ??
    undefined;

  // `call_successful` — ElevenLabs reports this boolean (sometimes a string like "success" / "failed")
  // once post-call analysis completes.
  const rawCallSuccessful = data.call_successful ?? data.analysis?.call_successful;
  let callSuccessful: boolean | null;
  if (typeof rawCallSuccessful === "boolean") {
    callSuccessful = rawCallSuccessful;
  } else if (typeof rawCallSuccessful === "string") {
    callSuccessful = rawCallSuccessful.toLowerCase() === "success" || rawCallSuccessful.toLowerCase() === "true";
  } else {
    // Fallback heuristic: at least one transcript turn + 5s of duration counts as a real conversation
    callSuccessful =
      transcript.length >= 1 && (typeof durationSec === "number" ? durationSec >= 5 : false)
        ? true
        : null;
  }

  return NextResponse.json({
    conversationId: id,
    status,
    rawStatus,
    callSuccessful,
    terminationReason: typeof terminationReason === "string" ? terminationReason : undefined,
    transcript,
    durationSec,
    recordingUrl,
  });
}
