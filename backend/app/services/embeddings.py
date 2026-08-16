from abc import ABC, abstractmethod
from typing import Any

import structlog
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = structlog.get_logger()


class EmbeddingProvider(ABC):
    """Abstract interface for embedding providers."""

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def dimensions(self) -> int: ...

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed_texts([text])
        return results[0]

    def count_tokens(self, text: str) -> int:
        try:
            encoder = tiktoken.encoding_for_model(self.model_name)
        except KeyError:
            encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))


class OpenAIEmbedding(EmbeddingProvider):
    def __init__(self, model: str = "text-embedding-3-small", dims: int = 1536):
        from openai import AsyncOpenAI

        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = model
        self._dims = dims

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dims

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self._client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self._dims,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            await logger.adebug(
                "OpenAI embedding batch",
                batch_index=i // batch_size,
                count=len(batch),
                tokens=response.usage.total_tokens,
            )

        return all_embeddings


class CohereEmbedding(EmbeddingProvider):
    def __init__(self, model: str = "embed-english-v3.0", dims: int = 1024):
        import httpx

        settings = get_settings()
        self._api_key = settings.openai_api_key  # reuse or add cohere key
        self._client = httpx.AsyncClient(
            base_url="https://api.cohere.com/v1",
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=60.0,
        )
        self._model = model
        self._dims = dims

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dims

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        batch_size = 96

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self._client.post(
                "/embed",
                json={
                    "model": self._model,
                    "texts": batch,
                    "input_type": "search_document",
                    "truncate": "END",
                },
            )
            response.raise_for_status()
            data = response.json()
            all_embeddings.extend(data["embeddings"])

        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        response = await self._client.post(
            "/embed",
            json={
                "model": self._model,
                "texts": [text],
                "input_type": "search_query",
                "truncate": "END",
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["embeddings"][0]


class LocalEmbedding(EmbeddingProvider):
    """Sentence-transformers based local embedding."""

    def __init__(self, model: str = "all-MiniLM-L6-v2", dims: int = 384):
        self._model_name = model
        self._dims = dims
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info("Loaded local embedding model", model=self._model_name)
        return self._model

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dims

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()


PROVIDER_MAP: dict[str, type[EmbeddingProvider]] = {
    "openai": OpenAIEmbedding,
    "cohere": CohereEmbedding,
    "local": LocalEmbedding,
}

# Default models and dimensions per provider
PROVIDER_DEFAULTS: dict[str, dict[str, Any]] = {
    "openai": {"model": "text-embedding-3-small", "dims": 1536},
    "cohere": {"model": "embed-english-v3.0", "dims": 1024},
    "local": {"model": "all-MiniLM-L6-v2", "dims": 384},
}


def get_embedding_provider(
    provider: str = "openai",
    model: str | None = None,
    dimensions: int | None = None,
) -> EmbeddingProvider:
    cls = PROVIDER_MAP.get(provider)
    if not cls:
        raise ValueError(f"Unknown embedding provider: {provider}. Options: {list(PROVIDER_MAP)}")

    defaults = PROVIDER_DEFAULTS.get(provider, {})
    model = model or defaults.get("model", "")
    dimensions = dimensions or defaults.get("dims", 1536)

    return cls(model=model, dims=dimensions)
