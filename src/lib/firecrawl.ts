import Firecrawl from "@mendable/firecrawl-js";

// Singleton client — reused across requests (auto-reads FIRECRAWL_API_KEY from env)
let client: Firecrawl | null = null;

function getClient(): Firecrawl {
  if (!process.env.FIRECRAWL_API_KEY || process.env.FIRECRAWL_API_KEY === "[TO_BE_PROVIDED]") {
    throw new Error("FIRECRAWL_API_KEY is not configured");
  }
  if (!client) {
    client = new Firecrawl({ apiKey: process.env.FIRECRAWL_API_KEY });
  }
  return client;
}

/** Scrape a single URL and return markdown + metadata. */
export async function scrapeUrl(url: string) {
  const fc = getClient();
  return fc.scrape(url, { formats: ["markdown"] });
}

/** Scrape a URL and extract structured data using a prompt. */
export async function scrapeWithPrompt(url: string, prompt: string) {
  const fc = getClient();
  return fc.scrape(url, {
    formats: ["markdown", { type: "json", prompt }],
  });
}

/** Search the web via Firecrawl and return results. */
export async function searchWeb(query: string, limit = 5) {
  const fc = getClient();
  return fc.search(query, { limit });
}

/** Get a sitemap/link list of a domain. */
export async function mapSite(url: string) {
  const fc = getClient();
  return fc.map(url);
}

export { getClient };
