/**
 * Extract text content from a plain text buffer (.txt, .md, .csv).
 */
export function extractPlainText(buffer: Buffer): string {
  return buffer.toString("utf-8");
}
