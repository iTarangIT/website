/**
 * Clean extracted text: normalize whitespace, remove control characters,
 * collapse blank lines, and trim.
 */
export function cleanText(raw: string): string {
  return (
    raw
      // Replace common non-breaking and special spaces with regular space
      .replace(/[\u00A0\u200B\u200C\u200D\uFEFF]/g, " ")
      // Remove control characters (except newlines and tabs)
      .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "")
      // Normalize line endings
      .replace(/\r\n/g, "\n")
      .replace(/\r/g, "\n")
      // Collapse 3+ newlines into 2
      .replace(/\n{3,}/g, "\n\n")
      // Collapse multiple spaces/tabs on same line
      .replace(/[^\S\n]+/g, " ")
      // Trim each line
      .split("\n")
      .map((line) => line.trim())
      .join("\n")
      .trim()
  );
}
