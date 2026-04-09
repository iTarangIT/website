/**
 * Test script for the RAG ingestion pipeline.
 *
 * Usage:
 *   npx tsx scripts/test-ingest.ts <s3-key> [visibility]
 *
 * Examples:
 *   npx tsx scripts/test-ingest.ts documents/sample.pdf
 *   npx tsx scripts/test-ingest.ts documents/itarang-guidelines.pdf internal
 *   npx tsx scripts/test-ingest.ts documents/sample.pdf internal --reindex
 *
 * Prerequisites:
 *   - Fill in .env with real API keys
 *   - Upload a test document to your S3 bucket
 *   - Run the Supabase migration SQL (001 + 002)
 *   - Create the Pinecone index (dimension: 1536, metric: cosine)
 */

import "dotenv/config";

async function main() {
  const args = process.argv.slice(2);
  const s3Key = args.find((a) => !a.startsWith("--") && !["public", "dealer", "partner", "internal", "admin"].includes(a));
  const visibility = args.find((a) => ["public", "dealer", "partner", "internal", "admin"].includes(a)) || "internal";
  const reindex = args.includes("--reindex");

  if (!s3Key) {
    console.error("Usage: npx tsx scripts/test-ingest.ts <s3-key> [visibility] [--reindex]");
    console.error("Example: npx tsx scripts/test-ingest.ts documents/sample.pdf internal");
    console.error("\nVisibility levels: public, dealer, partner, internal, admin");
    process.exit(1);
  }

  // Validate required env vars
  const required = [
    "AWS_REGION",
    "AWS_S3_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "PINECONE_API_KEY",
    "NEXT_PUBLIC_SUPABASE_URL",
    "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY",
  ];

  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    console.error("Missing environment variables:");
    missing.forEach((key) => console.error(`   - ${key}`));
    console.error("\nFill in real values in .env");
    process.exit(1);
  }

  console.log("Starting ingestion test...");
  console.log(`   S3 Key:      ${s3Key}`);
  console.log(`   Bucket:      ${process.env.AWS_S3_BUCKET}`);
  console.log(`   Visibility:  ${visibility}`);
  console.log(`   Reindex:     ${reindex}`);
  console.log(`   Pinecone:    ${process.env.PINECONE_INDEX_NAME}`);
  console.log("");

  try {
    const { ingestDocument } = await import("@/lib/documents/ingest");

    const result = await ingestDocument(s3Key, {
      visibility: visibility as "public" | "dealer" | "partner" | "internal" | "admin",
      reindex,
    });

    if (result.status === "completed") {
      console.log("\nIngestion completed successfully!");
      console.log(`   Document ID: ${result.documentId}`);
      console.log(`   File:        ${result.fileName}`);
      console.log(`   Chunks:      ${result.totalChunks}`);
    } else {
      console.error("\nIngestion failed:");
      console.error(`   Error: ${result.error}`);
      process.exit(1);
    }
  } catch (error) {
    console.error("Fatal error:", error);
    process.exit(1);
  }
}

main();
