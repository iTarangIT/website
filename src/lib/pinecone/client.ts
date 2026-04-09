import { Pinecone } from "@pinecone-database/pinecone";
import type { ChunkMetadata } from "@/lib/embeddings/types";

function getPineconeClient(): Pinecone {
  const apiKey = process.env.PINECONE_API_KEY;
  if (!apiKey) {
    throw new Error("[Pinecone] Missing PINECONE_API_KEY in .env.local");
  }
  return new Pinecone({ apiKey });
}

function getIndex() {
  const indexName = process.env.PINECONE_INDEX_NAME || "itarang-index";
  return getPineconeClient().index(indexName);
}

function getNamespace() {
  return process.env.PINECONE_NAMESPACE || "documents";
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
    await ns.upsert({ records: batch });
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

  const result = await ns.query({
    vector: queryVector,
    topK,
    includeMetadata: true,
    filter,
  });

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

  await ns.deleteMany({ filter: { documentId } });
  console.log(`[Pinecone] Deleted vectors for document: ${documentId}`);
}
