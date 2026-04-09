import { scrapeUrl, scrapeWithPrompt, searchWeb, mapSite } from "@/lib/firecrawl";

export async function POST(req: Request) {
  try {
    const { action, url, query, prompt, limit } = await req.json();

    switch (action) {
      case "scrape": {
        if (!url) return Response.json({ error: "url is required" }, { status: 400 });
        const result = await scrapeUrl(url);
        return Response.json(result);
      }
      case "extract": {
        if (!url || !prompt) return Response.json({ error: "url and prompt are required" }, { status: 400 });
        const result = await scrapeWithPrompt(url, prompt);
        return Response.json(result);
      }
      case "search": {
        if (!query) return Response.json({ error: "query is required" }, { status: 400 });
        const result = await searchWeb(query, limit);
        return Response.json(result);
      }
      case "map": {
        if (!url) return Response.json({ error: "url is required" }, { status: 400 });
        const result = await mapSite(url);
        return Response.json(result);
      }
      default:
        return Response.json(
          { error: "Invalid action. Use: scrape, extract, search, or map" },
          { status: 400 },
        );
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return Response.json({ error: message }, { status: 500 });
  }
}
