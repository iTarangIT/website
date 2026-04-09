/**
 * Test script for the RAG chat pipeline.
 *
 * Usage:
 *   npx tsx scripts/test-chat.ts "your question here" [role]
 *
 * Examples:
 *   npx tsx scripts/test-chat.ts "What products does iTarang offer?"
 *   npx tsx scripts/test-chat.ts "What is the go-to-market strategy?" internal
 *   npx tsx scripts/test-chat.ts "Tell me about iTarang" public
 *
 * Prerequisites:
 *   - Fill in .env with real API keys
 *   - Run at least one ingestion first (test-ingest.ts)
 *   - Pinecone index must have vectors
 */

import "dotenv/config";

async function main() {
  const args = process.argv.slice(2);
  const roles = ["public", "dealer", "partner", "internal", "admin"];
  const role = args.find((a) => roles.includes(a)) || "internal";
  const query = args.filter((a) => !roles.includes(a)).join(" ");

  if (!query) {
    console.error('Usage: npx tsx scripts/test-chat.ts "your question" [role]');
    console.error('Example: npx tsx scripts/test-chat.ts "What products does iTarang offer?" internal');
    console.error(`\nRoles: ${roles.join(", ")}`);
    process.exit(1);
  }

  // Validate required env vars
  const required = [
    "PINECONE_API_KEY",
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
  ];

  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    console.error("Missing environment variables:");
    missing.forEach((key) => console.error(`   - ${key}`));
    console.error("\nFill in real values in .env");
    process.exit(1);
  }

  console.log("RAG Chat Test");
  console.log(`   Query: "${query}"`);
  console.log(`   Role:  ${role}`);
  console.log(`   Model: ${process.env.GROQ_MODEL || "llama-3.3-70b-versatile"}`);
  console.log("");

  try {
    const { searchRelevantChunks } = await import("@/lib/retrieval/search");
    const { buildSystemPrompt, buildUserMessage } = await import("@/lib/retrieval/prompt");
    const { generateAnswer } = await import("@/lib/groq/client");
    const { sanitizeOutput } = await import("@/lib/retrieval/safety");

    // Step 1: Search
    const startSearch = Date.now();
    console.log("Searching for relevant chunks...");
    const chunks = await searchRelevantChunks(query, {
      userRole: role as "public" | "dealer" | "partner" | "internal" | "admin",
    });
    const searchMs = Date.now() - startSearch;
    console.log(`   Found ${chunks.length} relevant chunks (${searchMs}ms)`);

    if (chunks.length > 0) {
      console.log("\nTop sources:");
      chunks.forEach((c, i) => {
        console.log(`   ${i + 1}. ${c.metadata.fileName} (chunk ${c.metadata.chunkIndex}, score: ${c.score.toFixed(4)}, visibility: ${c.metadata.visibility})`);
      });
    } else {
      console.log("\nNo relevant chunks found for this query with role:", role);
      console.log("If the document was ingested as 'internal', try: npx tsx scripts/test-chat.ts \"your query\" internal");
      return;
    }

    // Step 2: Build prompt
    const systemPrompt = buildSystemPrompt(chunks);
    const userMessage = buildUserMessage(query);

    // Step 3: Generate answer
    const startLlm = Date.now();
    console.log("\nGenerating answer...");
    const rawAnswer = await generateAnswer(systemPrompt, userMessage);
    const llmMs = Date.now() - startLlm;

    // Step 4: Safety check
    const safety = sanitizeOutput(rawAnswer);

    console.log("\n" + "=".repeat(60));
    console.log("ANSWER:");
    console.log("=".repeat(60));
    console.log(safety.text);

    if (!safety.safe) {
      console.log("\nResponse was filtered for safety.");
      console.log(`Reason: ${safety.blocked}`);
    }

    console.log("\n" + "=".repeat(60));
    console.log(`Search: ${searchMs}ms | LLM: ${llmMs}ms | Total: ${searchMs + llmMs}ms`);
  } catch (error) {
    console.error("Fatal error:", error);
    process.exit(1);
  }
}

main();
