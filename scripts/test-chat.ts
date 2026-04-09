/**
 * Test script for the RAG chat pipeline.
 *
 * Usage:
 *   npx tsx scripts/test-chat.ts "your question here"
 *
 * Example:
 *   npx tsx scripts/test-chat.ts "What products does iTarang offer?"
 *
 * Prerequisites:
 *   - Fill in .env.local with real API keys
 *   - Run at least one ingestion first (test-ingest.ts)
 *   - Pinecone index must have vectors
 */

import "dotenv/config";

async function main() {
  const query = process.argv.slice(2).join(" ");

  if (!query) {
    console.error('Usage: npx tsx scripts/test-chat.ts "your question"');
    console.error('Example: npx tsx scripts/test-chat.ts "What products does iTarang offer?"');
    process.exit(1);
  }

  // Validate required env vars
  const required = [
    "PINECONE_API_KEY",
    "GROQ_API_KEY",
  ];

  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    console.error("❌ Missing environment variables:");
    missing.forEach((key) => console.error(`   - ${key}`));
    console.error("\nCopy .env.example to .env.local and fill in real values.");
    process.exit(1);
  }

  console.log("🔍 RAG Chat Test");
  console.log(`   Query: "${query}"`);
  console.log(`   Model: ${process.env.GROQ_MODEL || "llama-3.3-70b-versatile"}`);
  console.log("");

  try {
    const { searchRelevantChunks } = await import("@/lib/retrieval/search");
    const { buildSystemPrompt, buildUserMessage } = await import("@/lib/retrieval/prompt");
    const { generateAnswer } = await import("@/lib/groq/client");
    const { sanitizeOutput } = await import("@/lib/retrieval/safety");

    // Step 1: Search
    console.log("📡 Searching for relevant chunks...");
    const chunks = await searchRelevantChunks(query, {
      visibility: ["public"],
    });
    console.log(`   Found ${chunks.length} relevant chunks`);

    if (chunks.length > 0) {
      console.log("\n📄 Top sources:");
      chunks.forEach((c, i) => {
        console.log(`   ${i + 1}. ${c.metadata.fileName} (chunk ${c.metadata.chunkIndex}, score: ${c.score.toFixed(4)})`);
      });
    }

    // Step 2: Build prompt
    const systemPrompt = buildSystemPrompt(chunks);
    const userMessage = buildUserMessage(query);

    // Step 3: Generate answer
    console.log("\n🤖 Generating answer...");
    const rawAnswer = await generateAnswer(systemPrompt, userMessage);

    // Step 4: Safety check
    const safety = sanitizeOutput(rawAnswer);

    console.log("\n" + "=".repeat(60));
    console.log("ANSWER:");
    console.log("=".repeat(60));
    console.log(safety.text);

    if (!safety.safe) {
      console.log("\n⚠️  Response was filtered for safety.");
    }
  } catch (error) {
    console.error("❌ Fatal error:", error);
    process.exit(1);
  }
}

main();
