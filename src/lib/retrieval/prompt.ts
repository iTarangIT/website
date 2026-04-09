import type { SearchResult } from "@/lib/embeddings/types";

/**
 * Build a grounded system prompt from retrieved context chunks.
 * Enforces strict answer-from-context rules.
 */
export function buildSystemPrompt(chunks: SearchResult[]): string {
  const contextBlock = chunks
    .map(
      (c, i) =>
        `[Source ${i + 1} — ${c.metadata.fileName}, chunk ${c.metadata.chunkIndex}]\n${c.text}`
    )
    .join("\n\n---\n\n");

  return `You are an AI assistant for iTarang Technologies. Answer the user's question using ONLY the context provided below.

## RULES — follow these strictly:
1. Answer ONLY from the provided context. Do NOT use prior knowledge.
2. If the answer is not in the context, say: "I don't have enough information to answer that. Please contact iTarang at founders@itarang.in or +91-8920828425."
3. Do NOT hallucinate, guess, or make up information.
4. Do NOT reveal confidential internal data, pricing formulas, or cost structures unless the context explicitly states them as public.
5. Cite the source by mentioning the document name when relevant.
6. Keep answers concise, professional, and helpful.
7. Use markdown formatting when it improves readability.

## CONTEXT:
${contextBlock || "No relevant context found."}`;
}

/**
 * Build the final user message sent to the LLM.
 */
export function buildUserMessage(query: string): string {
  return `User question: ${query}`;
}
