import { embedText } from "@/lib/embeddings/localEmbedding";
import { queryVectors } from "@/lib/pinecone/client";
import type { SearchResult } from "@/lib/embeddings/types";
import { filterByVisibility } from "./safety";

/**
 * Embed a user query locally and retrieve the most relevant chunks
 * from Pinecone, filtered by visibility.
 */
export async function searchRelevantChunks(
  query: string,
  options: {
    topK?: number;
    visibility?: ("public" | "internal" | "restricted")[];
  } = {}
): Promise<SearchResult[]> {
  const topK = options.topK ?? (Number(process.env.TOP_K_RETRIEVAL) || 5);

  // Step 1: Embed the user query locally
  const queryVector = await embedText(query);

  // Step 2: Build Pinecone filter
  const filter: Record<string, unknown> = {};
  if (options.visibility && options.visibility.length > 0) {
    filter.visibility = { $in: options.visibility };
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

  // Step 5: Apply visibility safety filter
  return filterByVisibility(results);
}
