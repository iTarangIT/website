import { fetchFileFromS3 } from "@/lib/aws/s3";
import { upsertVectors, deleteByDocumentId } from "@/lib/pinecone/client";
import {
  insertDocument,
  updateDocumentStatus,
  insertChunks,
  getDocumentByS3Key,
  deleteDocumentAndChunks,
} from "@/lib/supabase/client";
import { embedBatch } from "@/lib/openai/embeddings";
import { extractPdfText } from "./extractors/pdf";
import { extractDocxText } from "./extractors/docx";
import { extractPlainText } from "./extractors/text";
import { cleanText } from "./cleaner";
import { chunkText } from "./chunker";
import type { ChunkMetadata, IngestResult, Visibility } from "@/lib/embeddings/types";

const MIME_TYPES: Record<string, string> = {
  pdf: "application/pdf",
  docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  text: "text/plain",
};

/**
 * Detect file type from extension.
 */
function getFileType(fileName: string): "pdf" | "docx" | "text" {
  const ext = fileName.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "pdf";
  if (ext === "docx" || ext === "doc") return "docx";
  return "text";
}

/**
 * Extract text from a buffer based on file type.
 */
async function extractText(buffer: Buffer, fileType: string): Promise<string> {
  switch (fileType) {
    case "pdf":
      return extractPdfText(buffer);
    case "docx":
      return extractDocxText(buffer);
    default:
      return extractPlainText(buffer);
  }
}

export interface IngestOptions {
  visibility?: Visibility;
  sourceType?: string;
  /** If true, delete existing document with same s3Key before re-ingesting */
  reindex?: boolean;
}

/**
 * Full ingestion pipeline for a single document:
 * 1. Fetch from S3
 * 2. Extract text
 * 3. Clean text
 * 4. Chunk text
 * 5. Generate embeddings via OpenAI
 * 6. Store vectors in Pinecone
 * 7. Store metadata in Supabase
 */
export async function ingestDocument(
  s3Key: string,
  options: IngestOptions = {}
): Promise<IngestResult> {
  const {
    visibility = "internal",
    sourceType = "upload",
    reindex = false,
  } = options;

  const fileName = s3Key.split("/").pop() || s3Key;
  const fileType = getFileType(fileName);
  let documentId = "";

  try {
    // Check for existing document with same s3Key
    const existing = await getDocumentByS3Key(s3Key);
    if (existing && !reindex) {
      console.log(`[Ingest] ${fileName}: already ingested (id=${existing.id}). Use reindex=true to re-ingest.`);
      return {
        documentId: existing.id,
        fileName,
        totalChunks: existing.total_chunks ?? 0,
        status: "completed",
      };
    }

    // If reindexing, clean up old data first
    if (existing && reindex) {
      console.log(`[Ingest] ${fileName}: reindexing — removing old data`);
      await deleteByDocumentId(existing.id);
      await deleteDocumentAndChunks(existing.id);
    }

    // Step 1: Fetch from S3 and register in Supabase
    console.log(`[Ingest] Starting: ${fileName}`);
    const buffer = await fetchFileFromS3(s3Key);

    documentId = await insertDocument({
      file_name: fileName,
      s3_key: s3Key,
      file_type: fileType,
      file_size_bytes: buffer.length,
      visibility,
      s3_bucket: process.env.AWS_S3_BUCKET,
      mime_type: MIME_TYPES[fileType] || "application/octet-stream",
      source_type: sourceType,
    });

    // Step 2: Extract text
    const rawText = await extractText(buffer, fileType);
    if (!rawText || rawText.trim().length === 0) {
      throw new Error("No text content extracted from document");
    }

    // Step 3: Clean text
    const cleaned = cleanText(rawText);

    // Step 4: Chunk text
    const chunks = chunkText(cleaned);
    if (chunks.length === 0) {
      throw new Error("No chunks produced from document");
    }
    console.log(`[Ingest] ${fileName}: ${chunks.length} chunks created`);

    // Step 5: Generate embeddings via OpenAI
    const texts = chunks.map((c) => c.text);
    const embeddings = await embedBatch(texts);
    console.log(`[Ingest] ${fileName}: embeddings generated`);

    // Step 6: Store vectors in Pinecone
    const vectors = chunks.map((chunk, i) => ({
      id: `${documentId}_chunk_${chunk.index}`,
      values: embeddings[i],
      metadata: {
        documentId,
        fileName,
        chunkIndex: chunk.index,
        text: chunk.text.slice(0, 1000), // Pinecone metadata limit
        s3Key,
        visibility,
        sourceType,
      } satisfies ChunkMetadata,
    }));
    await upsertVectors(vectors);

    // Step 7: Store chunk metadata in Supabase
    await insertChunks(
      chunks.map((chunk) => ({
        document_id: documentId,
        chunk_index: chunk.index,
        text: chunk.text,
        token_count: chunk.tokenEstimate,
        pinecone_vector_id: `${documentId}_chunk_${chunk.index}`,
        visibility,
      }))
    );

    // Step 8: Update document status
    await updateDocumentStatus(documentId, "completed", chunks.length);
    console.log(`[Ingest] ${fileName}: completed successfully`);

    return {
      documentId,
      fileName,
      totalChunks: chunks.length,
      status: "completed",
    };
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : String(error);
    console.error(`[Ingest] ${fileName}: FAILED — ${errorMessage}`);

    if (documentId) {
      await updateDocumentStatus(documentId, "failed", 0, errorMessage).catch(
        () => {}
      );
    }

    return {
      documentId,
      fileName,
      totalChunks: 0,
      status: "failed",
      error: errorMessage,
    };
  }
}

/**
 * Ingest multiple documents from S3.
 */
export async function ingestMultipleDocuments(
  s3Keys: string[],
  options: IngestOptions = {}
): Promise<IngestResult[]> {
  const results: IngestResult[] = [];
  for (const key of s3Keys) {
    const result = await ingestDocument(key, options);
    results.push(result);
  }
  return results;
}
