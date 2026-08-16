from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=16384)
    stream: bool = False
    filters: dict[str, Any] | None = None


class ChunkResponse(BaseModel):
    chunk_id: str
    content: str
    score: float
    document_id: str
    document_title: str


class RAGQueryResponse(BaseModel):
    answer: str
    chunks: list[ChunkResponse]
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    retrieval_latency_ms: float
    total_latency_ms: float


class RAGConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

    chunking_strategy: str = "recursive"
    chunk_size: int = Field(default=800, ge=100, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)

    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    retrieval_mode: str = "hybrid"
    top_k: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

    reranker_enabled: bool = True
    reranker_provider: str | None = "bge"
    reranker_model: str | None = None
    reranker_top_k: int = Field(default=5, ge=1, le=20)

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=16384)
    system_prompt: str | None = None


class RAGConfigResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    name: str
    version: int
    is_active: bool

    chunking_strategy: str
    chunk_size: int
    chunk_overlap: int

    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int

    retrieval_mode: str
    top_k: int
    similarity_threshold: float

    reranker_enabled: bool
    reranker_provider: str | None
    reranker_model: str | None
    reranker_top_k: int

    llm_provider: str
    llm_model: str
    temperature: float
    max_tokens: int
    system_prompt: str | None

    created_at: Any
    updated_at: Any

    model_config = {"from_attributes": True}
