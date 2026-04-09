import OpenAI from "openai";
import type { EmbeddingProvider } from "@/lib/embeddings/types";

const MODEL = process.env.OPENAI_EMBEDDING_MODEL || "text-embedding-3-small";
const DIMENSION = 1536;

let client: OpenAI | null = null;

function getClient(): OpenAI {
  if (client) return client;

  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey || apiKey === "YOUR_OPENAI_API_KEY") {
    throw new Error(
      "[OpenAI] Missing OPENAI_API_KEY in environment variables"
    );
  }

  client = new OpenAI({ apiKey });
  return client;
}

/**
 * Embed a single piece of text using the OpenAI embeddings API.
 */
export async function embedText(text: string): Promise<number[]> {
  const openai = getClient();
  const response = await openai.embeddings.create({
    model: MODEL,
    input: text,
  });
  return response.data[0].embedding;
}

/**
 * Embed multiple texts in a single API call.
 * OpenAI supports batched input natively.
 */
export async function embedBatch(texts: string[]): Promise<number[][]> {
  if (texts.length === 0) return [];

  const openai = getClient();

  // OpenAI has a limit on batch size; process in groups of 100
  const BATCH_SIZE = 100;
  const allEmbeddings: number[][] = [];

  for (let i = 0; i < texts.length; i += BATCH_SIZE) {
    const batch = texts.slice(i, i + BATCH_SIZE);
    const response = await openai.embeddings.create({
      model: MODEL,
      input: batch,
    });

    // Sort by index to ensure correct ordering
    const sorted = response.data
      .sort((a, b) => a.index - b.index)
      .map((item) => item.embedding);

    allEmbeddings.push(...sorted);
  }

  return allEmbeddings;
}

/**
 * Class wrapper that implements the EmbeddingProvider interface.
 */
export class OpenAIEmbeddingProvider implements EmbeddingProvider {
  async embed(text: string): Promise<number[]> {
    return embedText(text);
  }

  async embedBatch(texts: string[]): Promise<number[][]> {
    return embedBatch(texts);
  }

  getDimension(): number {
    return DIMENSION;
  }
}
