import { embedText } from "@/lib/openai/embeddings";
import { queryVectors } from "@/lib/pinecone/client";
import type { SearchResult, Visibility } from "@/lib/embeddings/types";
import { filterByVisibility, getAllowedVisibilities } from "./safety";

/**
 * Embed a user query via OpenAI and retrieve the most relevant chunks
 * from Pinecone, filtered by the caller's role-based visibility.
 */
export async function searchRelevantChunks(
  query: string,
  options: {
    topK?: number;
    userRole?: Visibility;
    visibility?: Visibility[];
  } = {}
): Promise<SearchResult[]> {
  const topK = options.topK ?? (Number(process.env.TOP_K_RETRIEVAL) || 5);

  // Determine allowed visibility levels from role hierarchy
  const allowed =
    options.visibility ?? getAllowedVisibilities(options.userRole ?? "public");

  // Step 1: Embed the user query via OpenAI
  const queryVector = await embedText(query);

  // Step 2: Build Pinecone filter
  const filter: Record<string, unknown> = {};
  if (allowed.length > 0) {
    filter.visibility = { $in: allowed };
  }

  // Step 3: Query Pinecone
  const matches = await queryVectors(
    queryVector,
    topK,
    Object.keys(filter).length > 0 ? filter : undefined
  );

  // Step 4: Map to SearchResult format
  const results: SearchResult[] = matches.map((m) => ({
    text: m.metadata.text,
    score: m.score,
    metadata: m.metadata,
  }));

  // Step 5: Apply visibility safety filter (defence in depth)
  return filterByVisibility(results, allowed);
}
