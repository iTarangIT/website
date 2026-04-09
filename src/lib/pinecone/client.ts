import { Pinecone } from "@pinecone-database/pinecone";
import type { ChunkMetadata } from "@/lib/embeddings/types";

// Singleton client — avoids repeated DNS lookups on every request
let _client: Pinecone | null = null;

function getPineconeClient(): Pinecone {
  if (_client) return _client;
  const apiKey = process.env.PINECONE_API_KEY;
  if (!apiKey) {
    throw new Error("[Pinecone] Missing PINECONE_API_KEY in .env.local");
  }
  _client = new Pinecone({ apiKey });
  return _client;
}

let _index: ReturnType<Pinecone["index"]> | null = null;

function getIndex() {
  if (_index) return _index;
  const indexName = process.env.PINECONE_INDEX_NAME || "itarang-index";
  _index = getPineconeClient().index(indexName);
  return _index;
}

function getNamespace() {
  return process.env.PINECONE_NAMESPACE || "documents";
}

async function withRetry<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (i === retries - 1) throw err;
      const delay = 100 * (i + 1); // 100ms, 200ms
      console.warn(`[Pinecone] Attempt ${i + 1} failed, retrying in ${delay}ms...`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("[Pinecone] Unreachable");
}

/**
 * Upsert vectors into Pinecone in batches of 100.
 */
export async function upsertVectors(
  vectors: { id: string; values: number[]; metadata: ChunkMetadata }[]
) {
  const index = getIndex();
  const ns = index.namespace(getNamespace());

  const BATCH_SIZE = 100;
  for (let i = 0; i < vectors.length; i += BATCH_SIZE) {
    const batch = vectors.slice(i, i + BATCH_SIZE);
    await withRetry(() => ns.upsert({ records: batch }));
  }

  console.log(`[Pinecone] Upserted ${vectors.length} vectors`);
}

/**
 * Query Pinecone for the top-k most similar vectors.
 */
export async function queryVectors(
  queryVector: number[],
  topK: number = Number(process.env.TOP_K_RETRIEVAL) || 5,
  filter?: Record<string, unknown>
) {
  const index = getIndex();
  const ns = index.namespace(getNamespace());

  const result = await withRetry(() =>
    ns.query({
      vector: queryVector,
      topK,
      includeMetadata: true,
      filter,
    })
  );

  return (result.matches ?? []).map((match) => ({
    score: match.score ?? 0,
    metadata: match.metadata as unknown as ChunkMetadata,
  }));
}

/**
 * Delete all vectors for a specific document.
 */
export async function deleteByDocumentId(documentId: string) {
  const index = getIndex();
  const ns = index.namespace(getNamespace());

  await withRetry(() => ns.deleteMany({ filter: { documentId } }));
  console.log(`[Pinecone] Deleted vectors for document: ${documentId}`);
}
