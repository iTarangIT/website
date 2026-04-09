import type { EmbeddingProvider } from "./types";

// Singleton: load model once, reuse across requests
let pipeline: any = null;
let loadingPromise: Promise<any> | null = null;

const MODEL_NAME = "Xenova/all-MiniLM-L6-v2";
const DIMENSION = 384;

async function getModel() {
  if (pipeline) return pipeline;

  if (loadingPromise) return loadingPromise;

  loadingPromise = (async () => {
    try {
      // Dynamic import – @xenova/transformers is ESM-only
      const { pipeline: createPipeline } = await import(
        "@xenova/transformers"
      );
      pipeline = await createPipeline("feature-extraction", MODEL_NAME, {
        // Quantized model for faster load + lower memory
        quantized: true,
      });
      console.log(`[Embedding] Model "${MODEL_NAME}" loaded successfully`);
      return pipeline;
    } catch (error) {
      loadingPromise = null;
      throw new Error(
        `[Embedding] Failed to load local model "${MODEL_NAME}": ${error instanceof Error ? error.message : String(error)}`
      );
    }
  })();

  return loadingPromise;
}

/**
 * Embed a single piece of text using the local MiniLM model.
 */
export async function embedText(text: string): Promise<number[]> {
  const model = await getModel();
  const output = await model(text, { pooling: "mean", normalize: true });
  // output.data is a Float32Array; convert to number[]
  return Array.from(output.data as Float32Array).slice(0, DIMENSION);
}

/**
 * Embed multiple texts in batch. Processes sequentially to stay within
 * memory budget on modest hardware.
 */
export async function embedBatch(texts: string[]): Promise<number[][]> {
  const model = await getModel();
  const results: number[][] = [];

  for (const text of texts) {
    const output = await model(text, { pooling: "mean", normalize: true });
    results.push(Array.from(output.data as Float32Array).slice(0, DIMENSION));
  }

  return results;
}

/**
 * Class wrapper that implements the EmbeddingProvider interface.
 */
export class LocalEmbeddingProvider implements EmbeddingProvider {
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
