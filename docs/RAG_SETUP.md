# RAG Pipeline Setup Guide

Document-to-chatbot pipeline for iTarang Technologies using S3, Pinecone, Supabase, Groq, and local embeddings.

---

## Architecture

```
S3 (documents) → Extract text → Clean → Chunk → Local Embedding → Pinecone (vectors)
                                                                  ↓
User query → Local Embedding → Pinecone search → Build prompt → Groq → Grounded answer
                                                                  ↓
                                                          Supabase (logs)
```

**Embeddings run 100% locally** using `@xenova/transformers` with the `all-MiniLM-L6-v2` model (384 dimensions). No external embedding API is called.

---

## 1. Install Dependencies

Dependencies are already added to `package.json`. If starting fresh:

```bash
npm install
```

---

## 2. Configure Environment Variables

```bash
cp .env.example .env.local
```

Open `.env.local` and fill in your real keys:

| Variable | Where to get it |
|----------|----------------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | AWS IAM Console → Create access key |
| `AWS_S3_BUCKET` | AWS S3 Console → Your bucket name |
| `PINECONE_API_KEY` | Pinecone Dashboard → API Keys |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase Dashboard → Settings → API |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase Dashboard → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard → Settings → API (service_role) |
| `GROQ_API_KEY` | Groq Console → API Keys |

---

## 3. Set Up Pinecone Index

1. Go to [Pinecone Dashboard](https://app.pinecone.io/)
2. Create a new index:
   - **Name**: `itarang-index`
   - **Dimensions**: `384`
   - **Metric**: `cosine`
   - **Cloud**: Choose your preferred provider

---

## 4. Set Up Supabase Tables

1. Go to your Supabase project → SQL Editor
2. Copy and paste the contents of `supabase/migrations/001_knowledge_tables.sql`
3. Run the SQL

This creates three tables:
- `knowledge_documents` — tracks ingested files
- `knowledge_chunks` — individual text chunks with Pinecone vector IDs
- `chat_logs` — all chat interactions

---

## 5. Upload Documents to S3

Upload your documents (PDF, DOCX, TXT) to your S3 bucket:

```bash
aws s3 cp my-document.pdf s3://YOUR_BUCKET/documents/my-document.pdf
```

---

## 6. Test Ingestion

```bash
npx tsx scripts/test-ingest.ts documents/my-document.pdf
```

This will:
1. Fetch the file from S3
2. Extract text (PDF/DOCX/TXT)
3. Clean and chunk the text
4. Generate embeddings **locally** (first run downloads the model ~30MB)
5. Store vectors in Pinecone
6. Store metadata in Supabase

---

## 7. Test Chat

```bash
npx tsx scripts/test-chat.ts "What products does iTarang offer?"
```

This will:
1. Embed your query locally
2. Search Pinecone for relevant chunks
3. Build a grounded prompt
4. Call Groq for the answer
5. Display the answer with sources

---

## 8. Run the App

```bash
npm run dev
```

The RAG chat endpoint is available at:
```
POST /api/chat/rag
```

Request body:
```json
{
  "message": "What is iTarang?",
  "sessionId": "optional-session-id",
  "userId": "optional-user-id"
}
```

Response: Streaming text with headers:
- `X-Session-Id` — session tracking
- `X-Sources` — JSON array of source references

---

## File Structure

```
src/lib/
  aws/s3.ts                      — S3 fetch/list
  pinecone/client.ts             — Pinecone upsert/query/delete
  supabase/client.ts             — Supabase CRUD operations
  groq/client.ts                 — Groq chat completions
  embeddings/
    localEmbedding.ts            — Local MiniLM embedding (singleton)
    types.ts                     — Shared TypeScript types
  documents/
    extractors/pdf.ts            — PDF text extraction
    extractors/docx.ts           — DOCX text extraction
    extractors/text.ts           — Plain text extraction
    cleaner.ts                   — Text normalization
    chunker.ts                   — Sliding window chunker
    ingest.ts                    — Full ingestion orchestrator
  retrieval/
    search.ts                    — Embed query → Pinecone search
    prompt.ts                    — Grounded system prompt builder
    safety.ts                    — Visibility filter + output safety

src/app/api/chat/rag/route.ts   — RAG chat API endpoint
scripts/test-ingest.ts           — Ingestion test script
scripts/test-chat.ts             — Chat test script
supabase/migrations/             — Database schema
```

---

## Key Notes

- **Embeddings are 100% local** — no OpenAI or external API needed
- First embedding call downloads the model (~30MB) and caches it
- Subsequent calls reuse the loaded model (singleton pattern)
- The existing `/api/chat` route is untouched — it still uses static context
- The new `/api/chat/rag` route uses the full RAG pipeline
- All chat interactions are logged to Supabase for auditing
- Output is safety-filtered before delivery

---

## Known Limitations

1. **First embedding call is slow** (~5-10s) while the model downloads and loads into memory
2. **Large documents** may take time to process due to sequential embedding
3. **Pinecone free tier** has limits on vector count and queries
4. **No authentication** on the RAG endpoint yet — add auth middleware for production
5. **No document management UI** — ingestion is done via scripts
