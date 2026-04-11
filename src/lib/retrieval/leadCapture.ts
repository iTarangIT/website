/**
 * Parse and strip the [LEAD: name="...", phone="..."] marker from LLM output.
 */

export interface LeadData {
  name: string;
  phone: string;
}

const LEAD_PATTERN = /\[LEAD:\s*name="([^"]+)",\s*phone="([^"]+)"\]/;

/**
 * Extract lead data from the LLM response and return the cleaned text.
 */
export function extractLead(response: string): {
  cleanedResponse: string;
  lead: LeadData | null;
} {
  const match = response.match(LEAD_PATTERN);

  if (!match) {
    return { cleanedResponse: response, lead: null };
  }

  const name = match[1].trim();
  const phone = match[2].trim();

  // Strip the marker from the response
  const cleanedResponse = response.replace(LEAD_PATTERN, "").trimEnd();

  // Basic validation — name should be non-empty, phone should have digits
  if (!name || !/\d{7,}/.test(phone.replace(/[\s\-+()]/g, ""))) {
    return { cleanedResponse, lead: null };
  }

  return { cleanedResponse, lead: { name, phone } };
}
