export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  status: string;
  document_count: number;
  chunk_count: number;
  collection_name: string;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseList {
  items: KnowledgeBase[];
  total: number;
}

export interface Document {
  id: string;
  knowledge_base_id: string;
  title: string;
  mime_type: string | null;
  content_hash: string;
  file_size: number | null;
  version: number;
  status: string;
  chunk_count: number;
  embedding_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentList {
  items: Document[];
  total: number;
}

export interface ChunkResponse {
  chunk_id: string;
  content: string;
  score: number;
  document_id: string;
  document_title: string;
}

export interface RAGQueryResponse {
  answer: string;
  chunks: ChunkResponse[];
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  retrieval_latency_ms: number;
  total_latency_ms: number;
}
