from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.rag.pipeline import RetrievedChunk

logger = structlog.get_logger()


@dataclass
class RerankResult:
    chunk: RetrievedChunk
    rerank_score: float
    original_rank: int


class Reranker(ABC):
    """Abstract interface for rerankers."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RerankResult]: ...


class BGEReranker(Reranker):
    """Cross-encoder reranker using BGE or any sentence-transformers model."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self._model_name = model_name
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self._model_name)
            logger.info("Loaded reranker model", model=self._model_name)
        return self._model

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RerankResult]:
        if not chunks:
            return []

        model = self._load_model()

        pairs = [[query, chunk.content] for chunk in chunks]
        scores = model.predict(pairs, show_progress_bar=False)

        scored = []
        for i, (chunk, score) in enumerate(zip(chunks, scores)):
            scored.append(
                RerankResult(
                    chunk=chunk,
                    rerank_score=float(score),
                    original_rank=i,
                )
            )

        scored.sort(key=lambda x: x.rerank_score, reverse=True)

        await logger.ainfo(
            "BGE reranked",
            input_chunks=len(chunks),
            output_chunks=min(top_k, len(scored)),
            top_score=round(scored[0].rerank_score, 4) if scored else 0,
        )

        return scored[:top_k]


class CohereReranker(Reranker):
    """Cohere API-based reranker."""

    def __init__(self, model: str = "rerank-english-v3.0", api_key: str | None = None):
        import httpx

        self._model = model
        self._api_key = api_key or ""
        self._client = httpx.AsyncClient(
            base_url="https://api.cohere.com/v1",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=30.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RerankResult]:
        if not chunks:
            return []

        documents = [chunk.content for chunk in chunks]

        response = await self._client.post(
            "/rerank",
            json={
                "model": self._model,
                "query": query,
                "documents": documents,
                "top_n": top_k,
                "return_documents": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("results", []):
            idx = item["index"]
            results.append(
                RerankResult(
                    chunk=chunks[idx],
                    rerank_score=item["relevance_score"],
                    original_rank=idx,
                )
            )

        await logger.ainfo(
            "Cohere reranked",
            input_chunks=len(chunks),
            output_chunks=len(results),
            top_score=round(results[0].rerank_score, 4) if results else 0,
        )

        return results


class NoOpReranker(Reranker):
    """Pass-through reranker — returns chunks as-is (for when reranking is disabled)."""

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RerankResult]:
        return [
            RerankResult(chunk=chunk, rerank_score=chunk.score, original_rank=i)
            for i, chunk in enumerate(chunks[:top_k])
        ]


RERANKER_MAP: dict[str, type[Reranker]] = {
    "bge": BGEReranker,
    "cohere": CohereReranker,
    "none": NoOpReranker,
}

RERANKER_DEFAULTS: dict[str, str] = {
    "bge": "BAAI/bge-reranker-base",
    "cohere": "rerank-english-v3.0",
}


def get_reranker(
    provider: str = "bge",
    model: str | None = None,
    api_key: str | None = None,
) -> Reranker:
    if not provider or provider == "none":
        return NoOpReranker()

    cls = RERANKER_MAP.get(provider)
    if not cls:
        raise ValueError(f"Unknown reranker provider: {provider}. Options: {list(RERANKER_MAP)}")

    if provider == "cohere":
        return cls(model=model or RERANKER_DEFAULTS["cohere"], api_key=api_key)

    return cls(model_name=model or RERANKER_DEFAULTS.get(provider, ""))
