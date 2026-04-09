export interface Chunk {
  text: string;
  index: number;
  tokenEstimate: number;
}

/**
 * Split text into overlapping chunks using a sliding window.
 * Uses character count as a proxy for tokens (~4 chars ≈ 1 token).
 */
export function chunkText(
  text: string,
  maxChunkSize: number = Number(process.env.MAX_CHUNK_SIZE) || 800,
  overlap: number = Number(process.env.CHUNK_OVERLAP) || 120
): Chunk[] {
  if (!text || text.trim().length === 0) return [];

  // Split on paragraph boundaries first for cleaner chunks
  const paragraphs = text.split(/\n\n+/);
  const chunks: Chunk[] = [];
  let currentChunk = "";
  let chunkIndex = 0;

  for (const paragraph of paragraphs) {
    const trimmed = paragraph.trim();
    if (!trimmed) continue;

    // If adding this paragraph exceeds the limit, finalize current chunk
    if (currentChunk.length + trimmed.length + 1 > maxChunkSize && currentChunk.length > 0) {
      chunks.push({
        text: currentChunk.trim(),
        index: chunkIndex,
        tokenEstimate: Math.ceil(currentChunk.trim().length / 4),
      });
      chunkIndex++;

      // Keep overlap from the end of the current chunk
      if (overlap > 0) {
        currentChunk = currentChunk.slice(-overlap) + "\n\n" + trimmed;
      } else {
        currentChunk = trimmed;
      }
    } else {
      currentChunk = currentChunk ? currentChunk + "\n\n" + trimmed : trimmed;
    }

    // Handle paragraphs that are themselves longer than maxChunkSize
    while (currentChunk.length > maxChunkSize) {
      const splitPoint = currentChunk.lastIndexOf(" ", maxChunkSize);
      const breakAt = splitPoint > maxChunkSize * 0.3 ? splitPoint : maxChunkSize;

      chunks.push({
        text: currentChunk.slice(0, breakAt).trim(),
        index: chunkIndex,
        tokenEstimate: Math.ceil(currentChunk.slice(0, breakAt).trim().length / 4),
      });
      chunkIndex++;

      currentChunk = currentChunk.slice(breakAt - overlap).trim();
    }
  }

  // Push remaining text
  if (currentChunk.trim().length > 0) {
    chunks.push({
      text: currentChunk.trim(),
      index: chunkIndex,
      tokenEstimate: Math.ceil(currentChunk.trim().length / 4),
    });
  }

  return chunks;
}
