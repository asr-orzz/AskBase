export interface KnowledgeBase {
  id: string;
  organization_id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  status: "active" | "syncing" | "error" | "archived";
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

export interface DataSource {
  id: string;
  knowledge_base_id: string;
  name: string;
  source_type: "file" | "s3" | "github" | "postgresql" | "rest_api" | "web";
  config: Record<string, unknown>;
  sync_status: "idle" | "running" | "completed" | "failed";
  last_synced_at: string | null;
  sync_error: string | null;
  document_count: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  knowledge_base_id: string;
  data_source_id: string | null;
  title: string;
  source_url: string | null;
  mime_type: string | null;
  content_hash: string;
  file_size: number | null;
  version: number;
  status: "pending" | "processing" | "indexed" | "failed" | "deleted";
  chunk_count: number;
  embedding_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentList {
  items: Document[];
  total: number;
}

export interface ChunkResult {
  chunk_id: string;
  content: string;
  score: number;
  document_id: string;
  document_title: string;
}

export interface RAGQueryResponse {
  answer: string;
  chunks: ChunkResult[];
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  retrieval_latency_ms: number;
  total_latency_ms: number;
}

export interface RAGConfig {
  id: string;
  knowledge_base_id: string;
  name: string;
  version: number;
  is_active: boolean;
  chunking_strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  embedding_provider: string;
  embedding_model: string;
  retrieval_mode: string;
  top_k: number;
  llm_provider: string;
  llm_model: string;
  temperature: number;
  max_tokens: number;
  created_at: string;
  updated_at: string;
}
