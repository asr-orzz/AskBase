import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.chunk import Chunk


class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class Document(BaseModel, TenantMixin):
    __tablename__ = "documents"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    version: Mapped[int] = mapped_column(default=1)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, values_callable=lambda e: [x.value for x in e], name="document_status"),
        default=DocumentStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(default=0)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
