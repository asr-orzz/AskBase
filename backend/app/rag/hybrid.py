from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

from app.rag.bm25 import BM25Index, BM25Result
from app.rag.pipeline import RetrievedChunk
from app.services.embeddings import EmbeddingProvider
from app.services.vector_store import VectorStore

logger = structlog.get_logger()


@dataclass
class HybridResult:
    chunk_id: str
    content: str
    score: float
    vector_score: float
    bm25_score: float
    document_id: str
    document_title: str
    metadata: dict[str, Any] = field(default_factory=dict)


def reciprocal_rank_fusion(
    result_lists: list[list[dict[str, Any]]],
    k: int = 60,
    id_key: str = "chunk_id",
) -> list[dict[str, Any]]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion.

    RRF score = sum(1 / (k + rank_i)) for each list where the item appears.
    """
    fused_scores: dict[str, float] = {}
    item_data: dict[str, dict[str, Any]] = {}

    for result_list in result_lists:
        for rank, item in enumerate(result_list):
            item_id = item[id_key]
            rrf_score = 1.0 / (k + rank + 1)
            fused_scores[item_id] = fused_scores.get(item_id, 0.0) + rrf_score

            if item_id not in item_data:
                item_data[item_id] = item

    sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)

    results = []
    for item_id in sorted_ids:
        data = item_data[item_id].copy()
        data["rrf_score"] = fused_scores[item_id]
        results.append(data)

    return results


class HybridRetriever:
    """Combines vector search + BM25 via Reciprocal Rank Fusion."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
        bm25_index: BM25Index,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.embedding = embedding_provider
        self.bm25 = bm25_index
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        collection: str,
        top_k: int = 10,
        vector_weight: int = 1,
        bm25_weight: int = 1,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[HybridResult]:
        # 1. Vector search
        query_vector = await self.embedding.embed_query(query)
        vector_results = await self.vector_store.search(
            collection=collection,
            query_vector=query_vector,
            limit=top_k * 2,
            score_threshold=score_threshold,
            filters=filters,
        )

        vector_list = [
            {
                "chunk_id": r["id"],
                "content": r["payload"].get("content", ""),
                "score": r["score"],
                "document_id": r["payload"].get("document_id", ""),
                "document_title": r["payload"].get("document_title", ""),
                "metadata": r["payload"],
            }
            for r in vector_results
        ]

        # 2. BM25 search
        bm25_results = self.bm25.search(query, top_k=top_k * 2)
        bm25_list = [
            {
                "chunk_id": r.chunk_id,
                "content": r.content,
                "score": r.score,
                "document_id": r.metadata.get("document_id", ""),
                "document_title": r.metadata.get("document_title", ""),
                "metadata": r.metadata,
            }
            for r in bm25_results
        ]

        # 3. Build weighted lists for RRF
        all_lists: list[list[dict[str, Any]]] = []
        for _ in range(vector_weight):
            all_lists.append(vector_list)
        for _ in range(bm25_weight):
            all_lists.append(bm25_list)

        # 4. Fuse with RRF
        fused = reciprocal_rank_fusion(all_lists, k=self.rrf_k)

        # 5. Build vector/bm25 score lookup
        vector_scores = {r["chunk_id"]: r["score"] for r in vector_list}
        bm25_scores = {r.chunk_id: r.score for r in bm25_results}

        results: list[HybridResult] = []
        for item in fused[:top_k]:
            results.append(
                HybridResult(
                    chunk_id=item["chunk_id"],
                    content=item["content"],
                    score=item.get("rrf_score", 0.0),
                    vector_score=vector_scores.get(item["chunk_id"], 0.0),
                    bm25_score=bm25_scores.get(item["chunk_id"], 0.0),
                    document_id=item.get("document_id", ""),
                    document_title=item.get("document_title", ""),
                    metadata=item.get("metadata", {}),
                )
            )

        await logger.ainfo(
            "Hybrid retrieval",
            vector_hits=len(vector_list),
            bm25_hits=len(bm25_list),
            fused=len(results),
        )

        return results

    def to_retrieved_chunks(self, results: list[HybridResult]) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id=r.chunk_id,
                content=r.content,
                score=r.score,
                document_id=r.document_id,
                document_title=r.document_title,
                metadata={
                    **r.metadata,
                    "vector_score": r.vector_score,
                    "bm25_score": r.bm25_score,
                },
            )
            for r in results
        ]
