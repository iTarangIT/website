import { ingestDocument } from "@/lib/documents/ingest";
import type { Visibility } from "@/lib/embeddings/types";

/**
 * POST /api/knowledge/reindex
 *
 * Re-ingest an existing document (deletes old vectors + chunks, then re-processes).
 *
 * Body: { s3Key: string, visibility?: Visibility }
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { s3Key, visibility = "internal" as Visibility } = body;

    if (!s3Key) {
      return Response.json({ error: "s3Key is required" }, { status: 400 });
    }

    const result = await ingestDocument(s3Key, {
      visibility,
      reindex: true,
    });

    return Response.json(result, {
      status: result.status === "completed" ? 200 : 500,
    });
  } catch (error) {
    console.error("[Reindex API]", error);
    return Response.json(
      { error: error instanceof Error ? error.message : "Reindex failed" },
      { status: 500 }
    );
  }
}
