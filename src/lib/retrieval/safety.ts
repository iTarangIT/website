import type { SearchResult, Visibility } from "@/lib/embeddings/types";

/**
 * Visibility hierarchy: each role can see its own level and all levels below.
 *   public < dealer < partner < internal < admin
 */
const VISIBILITY_HIERARCHY: Visibility[] = [
  "public",
  "dealer",
  "partner",
  "internal",
  "admin",
];

/**
 * Return the set of visibility levels a given role is allowed to access.
 */
export function getAllowedVisibilities(role: Visibility): Visibility[] {
  const idx = VISIBILITY_HIERARCHY.indexOf(role);
  if (idx === -1) return ["public"];
  return VISIBILITY_HIERARCHY.slice(0, idx + 1);
}

/**
 * Filter search results so only chunks the user's role can access are returned.
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
    // Block internal pricing / margin / cost structures
    /(?:internal\s+(?:cost|margin|pricing|markup))\s*[:=]/gi,
  ];

  for (const pattern of blockedPatterns) {
    if (pattern.test(output)) {
      return {
        safe: false,
        text: "I'm unable to provide that information. Please contact iTarang support at founders@itarang.in.",
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
