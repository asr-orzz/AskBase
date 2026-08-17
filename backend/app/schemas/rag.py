from typing import Any

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=16384)


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
