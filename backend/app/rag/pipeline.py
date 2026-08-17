from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import structlog
import time

from app.services.embeddings import EmbeddingProvider
from app.services.llm import LLMMessage, LLMProvider, LLMResponse
from app.services.vector_store import VectorStore

logger = structlog.get_logger()

DEFAULT_SYSTEM_PROMPT = """You are AskBase, an AI assistant that answers questions accurately based on the user's documents.

Instructions:
- Answer ONLY based on the provided context from the user's documents
- If the context doesn't contain enough information to answer fully, clearly state what's missing
- Cite sources using [Source: document_title] when referencing specific information
- Be concise, well-structured, and accurate
- Use bullet points or numbered lists for multi-part answers
- If multiple sources agree on a point, synthesize them into a coherent answer"""


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    score: float
    document_id: str
    document_title: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResult:
    answer: str
    chunks: list[RetrievedChunk]
    llm_response: LLMResponse
    retrieval_latency_ms: float
    total_latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGPipelineConfig:
    collection_name: str
    top_k: int = 8
    similarity_threshold: float = 0.25
    temperature: float = 0.1
    max_tokens: int = 2048
    system_prompt: str | None = None
    reranker_top_k: int = 5
    filters: dict[str, Any] | None = None


class RAGPipeline:
    """Core RAG pipeline: query → embed → retrieve → assemble context → generate."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
    ):
        self.vector_store = vector_store
        self.embedding = embedding_provider
        self.llm = llm_provider

    async def query(self, question: str, config: RAGPipelineConfig) -> RAGResult:
        total_start = time.perf_counter()

        # 1. Embed the query
        query_vector = await self.embedding.embed_query(question)

        # 2. Retrieve relevant chunks
        retrieval_start = time.perf_counter()
        raw_results = await self.vector_store.search(
            collection=config.collection_name,
            query_vector=query_vector,
            limit=config.top_k,
            score_threshold=config.similarity_threshold,
            filters=config.filters,
        )
        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

        chunks = [
            RetrievedChunk(
                chunk_id=r["id"],
                content=r["payload"].get("content", ""),
                score=r["score"],
                document_id=r["payload"].get("document_id", ""),
                document_title=r["payload"].get("document_title", ""),
                metadata=r["payload"],
            )
            for r in raw_results
        ]

        await logger.ainfo(
            "Retrieved chunks",
            count=len(chunks),
            retrieval_ms=round(retrieval_ms, 1),
            top_score=round(chunks[0].score, 4) if chunks else 0,
        )

        # 3. Build context from chunks
        context = self._build_context(chunks)

        # 4. Assemble messages
        system_prompt = config.system_prompt or DEFAULT_SYSTEM_PROMPT
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(
                role="user",
                content=f"Context:\n{context}\n\nQuestion: {question}",
            ),
        ]

        # 5. Generate answer
        llm_response = await self.llm.generate(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        total_ms = (time.perf_counter() - total_start) * 1000

        await logger.ainfo(
            "RAG query completed",
            total_ms=round(total_ms, 1),
            retrieval_ms=round(retrieval_ms, 1),
            llm_ms=round(llm_response.latency_ms, 1),
            chunks_used=len(chunks),
            tokens=llm_response.total_tokens,
        )

        return RAGResult(
            answer=llm_response.content,
            chunks=chunks,
            llm_response=llm_response,
            retrieval_latency_ms=retrieval_ms,
            total_latency_ms=total_ms,
            metadata={
                "model": llm_response.model,
                "embedding_model": self.embedding.model_name,
                "top_k": config.top_k,
            },
        )

    async def stream_query(
        self, question: str, config: RAGPipelineConfig
    ) -> AsyncIterator[str | RetrievedChunk]:
        """Stream the RAG response — yields chunks first, then streamed LLM tokens."""
        query_vector = await self.embedding.embed_query(question)

        raw_results = await self.vector_store.search(
            collection=config.collection_name,
            query_vector=query_vector,
            limit=config.top_k,
            score_threshold=config.similarity_threshold,
            filters=config.filters,
        )

        chunks = [
            RetrievedChunk(
                chunk_id=r["id"],
                content=r["payload"].get("content", ""),
                score=r["score"],
                document_id=r["payload"].get("document_id", ""),
                document_title=r["payload"].get("document_title", ""),
                metadata=r["payload"],
            )
            for r in raw_results
        ]

        for chunk in chunks:
            yield chunk

        context = self._build_context(chunks)
        system_prompt = config.system_prompt or DEFAULT_SYSTEM_PROMPT
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(
                role="user",
                content=f"Context:\n{context}\n\nQuestion: {question}",
            ),
        ]

        async for token in self.llm.stream(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        ):
            yield token

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "No relevant context found."

        parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.document_title or "Unknown"
            relevance = f"{chunk.score * 100:.0f}%"
            parts.append(f"[{i}] Source: {source} (relevance: {relevance})\n{chunk.content}")
        return "\n\n---\n\n".join(parts)
