import type { SearchResult } from "@/lib/embeddings/types";

/**
 * Filter search results by visibility. Remove restricted chunks
 * unless explicitly requested.
 */
export function filterByVisibility(
  results: SearchResult[],
  allowedVisibility: string[] = ["public"]
): SearchResult[] {
  return results.filter((r) =>
    allowedVisibility.includes(r.metadata.visibility)
  );
}

/**
 * Check if LLM output contains patterns that should be blocked.
 * Returns the sanitized output or flags issues.
 */
export function sanitizeOutput(output: string): {
  safe: boolean;
  text: string;
  blocked?: string;
} {
  const blockedPatterns = [
    // Block attempts to leak environment variables or secrets
    /(?:api[_-]?key|secret|password|token)\s*[:=]\s*\S+/gi,
    // Block SQL injection attempts in output
    /(?:DROP\s+TABLE|DELETE\s+FROM|ALTER\s+TABLE)/gi,
    // Block attempts to output base64-encoded secrets
    /(?:eyJ[A-Za-z0-9_-]{20,})/g,
  ];

  for (const pattern of blockedPatterns) {
    if (pattern.test(output)) {
      return {
        safe: false,
        text: "I'm unable to provide that information. Please contact iTarang support.",
        blocked: `Output matched blocked pattern: ${pattern.source}`,
      };
    }
  }

  return { safe: true, text: output };
}

/**
 * Validate that user input is reasonable before processing.
 */
export function validateUserInput(message: string): {
  valid: boolean;
  error?: string;
} {
  if (!message || message.trim().length === 0) {
    return { valid: false, error: "Message cannot be empty" };
  }

  if (message.length > 5000) {
    return { valid: false, error: "Message too long (max 5000 characters)" };
  }

  return { valid: true };
}
