import { ingestDocument } from "@/lib/documents/ingest";
import { listS3Files } from "@/lib/aws/s3";
import type { Visibility } from "@/lib/embeddings/types";

/**
 * POST /api/knowledge/ingest
 *
 * Trigger document ingestion from S3.
 *
 * Body:
 *   { s3Key: string, visibility?: Visibility, sourceType?: string, reindex?: boolean }
 * OR
 *   { prefix: string, visibility?: Visibility, sourceType?: string, reindex?: boolean }
 *   (ingests all files under the S3 prefix)
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const {
      s3Key,
      prefix,
      visibility = "internal" as Visibility,
      sourceType = "upload",
      reindex = false,
    } = body;

    if (!s3Key && !prefix) {
      return Response.json(
        { error: "Provide either s3Key or prefix" },
        { status: 400 }
      );
    }

    const options = { visibility, sourceType, reindex };

    // Single file ingestion
    if (s3Key) {
      const result = await ingestDocument(s3Key, options);
      return Response.json(result, {
        status: result.status === "completed" ? 200 : 500,
      });
    }

    // Batch ingestion by prefix
    const keys = await listS3Files(prefix);
    if (keys.length === 0) {
      return Response.json(
        { error: `No files found under prefix: ${prefix}` },
        { status: 404 }
      );
    }

    const results = [];
    for (const key of keys) {
      const result = await ingestDocument(key, options);
      results.push(result);
    }

    const completed = results.filter((r) => r.status === "completed").length;
    const failed = results.filter((r) => r.status === "failed").length;

    return Response.json({
      total: results.length,
      completed,
      failed,
      results,
    });
  } catch (error) {
    console.error("[Ingest API]", error);
    return Response.json(
      { error: error instanceof Error ? error.message : "Ingestion failed" },
      { status: 500 }
    );
  }
}
