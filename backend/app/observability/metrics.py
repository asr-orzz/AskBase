from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST

# --- Request metrics ---
REQUEST_COUNT = Counter(
    "ragops_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "ragops_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# --- RAG pipeline metrics ---
RAG_QUERY_COUNT = Counter(
    "ragops_rag_queries_total",
    "Total RAG queries",
    ["knowledge_base", "status"],
)
RAG_QUERY_LATENCY = Histogram(
    "ragops_rag_query_duration_seconds",
    "RAG query end-to-end latency",
    ["knowledge_base"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)
RETRIEVAL_LATENCY = Histogram(
    "ragops_retrieval_duration_seconds",
    "Vector retrieval latency",
    ["knowledge_base"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)
LLM_LATENCY = Histogram(
    "ragops_llm_duration_seconds",
    "LLM generation latency",
    ["provider", "model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# --- Token metrics ---
TOKEN_USAGE = Counter(
    "ragops_tokens_total",
    "Total tokens consumed",
    ["provider", "model", "direction"],  # direction: input/output
)

# --- Embedding metrics ---
EMBEDDING_LATENCY = Histogram(
    "ragops_embedding_duration_seconds",
    "Embedding generation latency",
    ["provider", "model"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
)
CHUNKS_EMBEDDED = Counter(
    "ragops_chunks_embedded_total",
    "Total chunks embedded",
    ["provider", "model"],
)

# --- Ingestion metrics ---
DOCUMENTS_INGESTED = Counter(
    "ragops_documents_ingested_total",
    "Total documents ingested",
    ["knowledge_base", "status"],
)
INGESTION_LATENCY = Histogram(
    "ragops_ingestion_duration_seconds",
    "Document ingestion latency",
    ["knowledge_base"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# --- Cost metrics ---
COST_TOTAL = Counter(
    "ragops_cost_usd_total",
    "Total cost in USD",
    ["provider", "model", "operation"],  # operation: embedding/generation/rerank
)

# --- System metrics ---
ACTIVE_KNOWLEDGE_BASES = Gauge(
    "ragops_active_knowledge_bases",
    "Number of active knowledge bases",
)
TOTAL_DOCUMENTS = Gauge(
    "ragops_total_documents",
    "Total indexed documents",
)
TOTAL_CHUNKS = Gauge(
    "ragops_total_chunks",
    "Total chunks in vector store",
)
APP_INFO = Info(
    "ragops",
    "RAGOps application info",
)


def get_metrics() -> bytes:
    return generate_latest()


def get_metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
