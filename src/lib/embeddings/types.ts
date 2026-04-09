export interface EmbeddingResult {
  text: string;
  vector: number[];
}

export interface EmbeddingProvider {
  embed(text: string): Promise<number[]>;
  embedBatch(texts: string[]): Promise<number[][]>;
  getDimension(): number;
}

export interface ChunkMetadata {
  [key: string]: string | number;
  documentId: string;
  fileName: string;
  chunkIndex: number;
  text: string;
  s3Key: string;
  visibility: string;
}

export interface SearchResult {
  text: string;
  score: number;
  metadata: ChunkMetadata;
}

export interface ChatRequest {
  message: string;
  sessionId?: string;
  userId?: string;
}

export interface ChatResponse {
  answer: string;
  sources: { fileName: string; chunkIndex: number; score: number }[];
  sessionId: string;
}

export interface IngestResult {
  documentId: string;
  fileName: string;
  totalChunks: number;
  status: "completed" | "failed";
  error?: string;
}
