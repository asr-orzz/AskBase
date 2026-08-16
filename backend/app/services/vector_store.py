from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

import structlog
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import get_settings

logger = structlog.get_logger()


class VectorStore(ABC):
    """Abstract interface for vector storage backends."""

    @abstractmethod
    async def create_collection(self, name: str, dimension: int) -> None: ...

    @abstractmethod
    async def delete_collection(self, name: str) -> None: ...

    @abstractmethod
    async def upsert(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None: ...

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def delete(self, collection: str, ids: list[str]) -> None: ...

    @abstractmethod
    async def count(self, collection: str) -> int: ...


class QdrantVectorStore(VectorStore):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key or None,
            prefer_grpc=True,
            grpc_port=settings.qdrant_grpc_port,
        )

    async def create_collection(self, name: str, dimension: int) -> None:
        try:
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                ),
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=20000,
                ),
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                ),
            )
            await logger.ainfo("Created Qdrant collection", collection=name, dimension=dimension)
        except UnexpectedResponse as e:
            if "already exists" in str(e):
                await logger.ainfo("Collection already exists", collection=name)
            else:
                raise

    async def delete_collection(self, name: str) -> None:
        try:
            self.client.delete_collection(collection_name=name)
            await logger.ainfo("Deleted Qdrant collection", collection=name)
        except UnexpectedResponse:
            await logger.awarning("Collection not found for deletion", collection=name)

    async def upsert(
        self,
        collection: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        points = [
            models.PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]

        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            self.client.upsert(collection_name=collection, points=batch, wait=True)

        await logger.ainfo(
            "Upserted vectors",
            collection=collection,
            count=len(points),
        )

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query_filter = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    must_conditions.append(
                        models.FieldCondition(
                            key=key, match=models.MatchAny(any=value)
                        )
                    )
                else:
                    must_conditions.append(
                        models.FieldCondition(
                            key=key, match=models.MatchValue(value=value)
                        )
                    )
            query_filter = models.Filter(must=must_conditions)

        results = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload or {},
            }
            for point in results.points
        ]

    async def delete(self, collection: str, ids: list[str]) -> None:
        self.client.delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=ids),
        )
        await logger.ainfo("Deleted vectors", collection=collection, count=len(ids))

    async def count(self, collection: str) -> int:
        info = self.client.get_collection(collection_name=collection)
        return info.points_count or 0

    async def collection_exists(self, name: str) -> bool:
        try:
            self.client.get_collection(collection_name=name)
            return True
        except UnexpectedResponse:
            return False


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = QdrantVectorStore()
    return _vector_store
