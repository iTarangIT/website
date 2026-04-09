-- ============================================
-- iTarang RAG Pipeline — Schema Expansion
-- ============================================
-- Run this AFTER 001_knowledge_tables.sql in Supabase SQL Editor.
-- Adds fields required for role-based access, source tracking, and safety logging.

-- ── knowledge_documents: add new columns ──

ALTER TABLE knowledge_documents
  DROP CONSTRAINT IF EXISTS knowledge_documents_visibility_check;

ALTER TABLE knowledge_documents
  ADD CONSTRAINT knowledge_documents_visibility_check
  CHECK (visibility IN ('public', 'dealer', 'partner', 'internal', 'admin'));

ALTER TABLE knowledge_documents
  ALTER COLUMN visibility SET DEFAULT 'internal';

ALTER TABLE knowledge_documents
  ADD COLUMN IF NOT EXISTS s3_bucket TEXT,
  ADD COLUMN IF NOT EXISTS mime_type TEXT,
  ADD COLUMN IF NOT EXISTS source_type TEXT DEFAULT 'upload',
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_visibility
  ON knowledge_documents(visibility);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_s3_key
  ON knowledge_documents(s3_key);


-- ── knowledge_chunks: add new columns ──

ALTER TABLE knowledge_chunks
  ADD COLUMN IF NOT EXISTS visibility TEXT DEFAULT 'internal',
  ADD COLUMN IF NOT EXISTS page_number INTEGER,
  ADD COLUMN IF NOT EXISTS section_name TEXT,
  ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_visibility
  ON knowledge_chunks(visibility);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_pinecone_vector
  ON knowledge_chunks(pinecone_vector_id);


-- ── chat_logs: add new columns ──

ALTER TABLE chat_logs
  RENAME COLUMN sources TO retrieved_sources_json;

ALTER TABLE chat_logs
  ADD COLUMN IF NOT EXISTS blocked_reason TEXT,
  ADD COLUMN IF NOT EXISTS user_role TEXT DEFAULT 'public';

CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id
  ON chat_logs(user_id);
