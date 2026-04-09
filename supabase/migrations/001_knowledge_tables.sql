-- ============================================
-- iTarang RAG Pipeline — Supabase Tables
-- ============================================
-- Run this in the Supabase SQL Editor to create the required tables.

-- 1. Knowledge Documents — tracks ingested files
CREATE TABLE IF NOT EXISTS knowledge_documents (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name     TEXT NOT NULL,
  s3_key        TEXT NOT NULL UNIQUE,
  file_type     TEXT NOT NULL CHECK (file_type IN ('pdf', 'docx', 'text')),
  file_size_bytes BIGINT NOT NULL DEFAULT 0,
  visibility    TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('public', 'internal', 'restricted')),
  status        TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
  total_chunks  INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at  TIMESTAMPTZ
);

-- Index for listing documents by status
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_status ON knowledge_documents(status);


-- 2. Knowledge Chunks — individual text chunks with Pinecone references
CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id        UUID NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
  chunk_index        INTEGER NOT NULL,
  text               TEXT NOT NULL,
  token_count        INTEGER NOT NULL DEFAULT 0,
  pinecone_vector_id TEXT NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (document_id, chunk_index)
);

-- Index for looking up chunks by document
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document ON knowledge_chunks(document_id);


-- 3. Chat Logs — all RAG chat interactions for auditing
CREATE TABLE IF NOT EXISTS chat_logs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id        TEXT NOT NULL,
  user_id           TEXT,
  user_message      TEXT NOT NULL,
  assistant_message TEXT NOT NULL,
  sources           JSONB NOT NULL DEFAULT '[]'::jsonb,
  latency_ms        INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index for querying by session
CREATE INDEX IF NOT EXISTS idx_chat_logs_session ON chat_logs(session_id);
-- Index for querying by date
CREATE INDEX IF NOT EXISTS idx_chat_logs_created ON chat_logs(created_at DESC);
