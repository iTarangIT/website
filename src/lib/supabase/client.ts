import { createClient, SupabaseClient } from "@supabase/supabase-js";

let serverClient: SupabaseClient | null = null;

/**
 * Server-side Supabase client using service role key.
 * Use this for all backend/ingestion operations.
 */
export function getSupabaseServer(): SupabaseClient {
  if (serverClient) return serverClient;

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    throw new Error(
      "[Supabase] Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env.local"
    );
  }

  serverClient = createClient(url, key, {
    auth: { autoRefreshToken: false, persistSession: false },
  });

  return serverClient;
}

/**
 * Browser-safe Supabase client using anon key.
 */
export function getSupabaseBrowser(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !key) {
    throw new Error(
      "[Supabase] Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY"
    );
  }

  return createClient(url, key);
}

// ── Document operations ──────────────────────────────────

export async function insertDocument(doc: {
  file_name: string;
  s3_key: string;
  file_type: string;
  file_size_bytes: number;
  visibility: string;
}) {
  const supabase = getSupabaseServer();
  const { data, error } = await supabase
    .from("knowledge_documents")
    .insert({ ...doc, status: "processing" })
    .select("id")
    .single();

  if (error) throw new Error(`[Supabase] Insert document failed: ${error.message}`);
  return data.id as string;
}

export async function updateDocumentStatus(
  documentId: string,
  status: "completed" | "failed",
  totalChunks?: number,
  errorMessage?: string
) {
  const supabase = getSupabaseServer();
  const { error } = await supabase
    .from("knowledge_documents")
    .update({
      status,
      total_chunks: totalChunks ?? 0,
      error_message: errorMessage ?? null,
      processed_at: new Date().toISOString(),
    })
    .eq("id", documentId);

  if (error) throw new Error(`[Supabase] Update document status failed: ${error.message}`);
}

export async function insertChunks(
  chunks: {
    document_id: string;
    chunk_index: number;
    text: string;
    token_count: number;
    pinecone_vector_id: string;
  }[]
) {
  const supabase = getSupabaseServer();
  const { error } = await supabase.from("knowledge_chunks").insert(chunks);
  if (error) throw new Error(`[Supabase] Insert chunks failed: ${error.message}`);
}

export async function insertChatLog(log: {
  session_id: string;
  user_id?: string;
  user_message: string;
  assistant_message: string;
  sources: object;
  latency_ms: number;
}) {
  const supabase = getSupabaseServer();
  const { error } = await supabase.from("chat_logs").insert(log);
  if (error) console.error(`[Supabase] Insert chat log failed: ${error.message}`);
}
