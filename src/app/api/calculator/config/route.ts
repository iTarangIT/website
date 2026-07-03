import { NextResponse } from "next/server";
import { resolveConfigMeta } from "@/lib/calculator/config-resolver";

export const dynamic = "force-dynamic";
export const runtime = "nodejs"; // postgres-js cannot run on the edge runtime

// Dropdown data for Card 1: active battery models, available tenures, coverage
// cities. Public (unauthenticated) — read-only config, no PII.
export async function GET() {
  try {
    const meta = await resolveConfigMeta();
    return NextResponse.json({
      success: true,
      data: meta,
      timestamp: new Date().toISOString(),
    });
  } catch (err) {
    console.error("[calculator/config]", err);
    return NextResponse.json(
      {
        success: false,
        error: { message: "Failed to load calculator config." },
        timestamp: new Date().toISOString(),
      },
      { status: 500 },
    );
  }
}
