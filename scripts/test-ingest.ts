/**
 * Test script for the RAG ingestion pipeline.
 *
 * Usage:
 *   npx tsx scripts/test-ingest.ts <s3-key>
 *
 * Example:
 *   npx tsx scripts/test-ingest.ts documents/sample.pdf
 *
 * Prerequisites:
 *   - Fill in .env.local with real API keys
 *   - Upload a test document to your S3 bucket
 *   - Run the Supabase migration SQL
 *   - Create the Pinecone index (dimension: 384, metric: cosine)
 */

import "dotenv/config";

async function main() {
  const s3Key = process.argv[2];

  if (!s3Key) {
    console.error("Usage: npx tsx scripts/test-ingest.ts <s3-key>");
    console.error("Example: npx tsx scripts/test-ingest.ts documents/sample.pdf");
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
  ];

  const missing = required.filter((key) => !process.env[key]);
  if (missing.length > 0) {
    console.error("❌ Missing environment variables:");
    missing.forEach((key) => console.error(`   - ${key}`));
    console.error("\nCopy .env.example to .env.local and fill in real values.");
    process.exit(1);
  }

  console.log("🚀 Starting ingestion test...");
  console.log(`   S3 Key: ${s3Key}`);
  console.log(`   Bucket: ${process.env.AWS_S3_BUCKET}`);
  console.log(`   Pinecone Index: ${process.env.PINECONE_INDEX_NAME}`);
  console.log("");

  try {
    // Dynamic import to allow env vars to be loaded first
    const { ingestDocument } = await import("@/lib/documents/ingest");

    const result = await ingestDocument(s3Key, "public");

    if (result.status === "completed") {
      console.log("✅ Ingestion completed successfully!");
      console.log(`   Document ID: ${result.documentId}`);
      console.log(`   File: ${result.fileName}`);
      console.log(`   Chunks: ${result.totalChunks}`);
    } else {
      console.error("❌ Ingestion failed:");
      console.error(`   Error: ${result.error}`);
    }
  } catch (error) {
    console.error("❌ Fatal error:", error);
    process.exit(1);
  }
}

main();
