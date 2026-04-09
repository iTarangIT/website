import mammoth from "mammoth";

/**
 * Extract text content from a DOCX buffer.
 */
export async function extractDocxText(buffer: Buffer): Promise<string> {
  const result = await mammoth.extractRawText({ buffer });
  return result.value;
}
