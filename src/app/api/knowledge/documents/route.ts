import { listDocuments } from "@/lib/supabase/client";

/**
 * GET /api/knowledge/documents
 *
 * List all ingested documents. Optional query param: ?status=completed|failed|processing
 */
export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const status = url.searchParams.get("status") ?? undefined;

    const documents = await listDocuments(status);

    return Response.json({
      count: documents.length,
      documents,
    });
  } catch (error) {
    console.error("[Documents API]", error);
    return Response.json(
      { error: error instanceof Error ? error.message : "Failed to list documents" },
      { status: 500 }
    );
  }
}
