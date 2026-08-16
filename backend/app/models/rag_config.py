import enum
import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.deployment import Deployment


class ChunkingStrategy(str, enum.Enum):
    FIXED = "fixed"
    RECURSIVE = "recursive"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"


class RetrievalMode(str, enum.Enum):
    VECTOR = "vector"
    BM25 = "bm25"
    HYBRID = "hybrid"


class RAGConfig(BaseModel, TenantMixin):
    __tablename__ = "rag_configs"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    # Chunking
    chunking_strategy: Mapped[ChunkingStrategy] = mapped_column(
        SAEnum(ChunkingStrategy, name="chunking_strategy"),
        default=ChunkingStrategy.RECURSIVE,
        nullable=False,
    )
    chunk_size: Mapped[int] = mapped_column(Integer, default=800)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=100)

    # Embedding
    embedding_provider: Mapped[str] = mapped_column(String(50), default="openai")
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-3-small")
    embedding_dimensions: Mapped[int] = mapped_column(Integer, default=1536)

    # Retrieval
    retrieval_mode: Mapped[RetrievalMode] = mapped_column(
        SAEnum(RetrievalMode, name="retrieval_mode"),
        default=RetrievalMode.HYBRID,
        nullable=False,
    )
    top_k: Mapped[int] = mapped_column(Integer, default=10)
    similarity_threshold: Mapped[float] = mapped_column(Float, default=0.7)

    # Reranking
    reranker_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    reranker_provider: Mapped[str | None] = mapped_column(String(50), nullable=True, default="bge")
    reranker_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reranker_top_k: Mapped[int] = mapped_column(Integer, default=5)

    # LLM
    llm_provider: Mapped[str] = mapped_column(String(50), default="openai")
    llm_model: Mapped[str] = mapped_column(String(100), default="gpt-4o")
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Advanced
    query_rewrite_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    context_compression_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="rag_configs")
    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="rag_config", cascade="all, delete-orphan"
    )
