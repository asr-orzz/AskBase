import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.data_source import DataSource
    from app.models.document import Document
    from app.models.rag_config import RAGConfig


class KBStatus(str, enum.Enum):
    ACTIVE = "active"
    SYNCING = "syncing"
    ERROR = "error"
    ARCHIVED = "archived"


class KnowledgeBase(BaseModel, TenantMixin):
    __tablename__ = "knowledge_bases"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[KBStatus] = mapped_column(
        SAEnum(KBStatus, values_callable=lambda e: [x.value for x in e], name="kb_status"),
        default=KBStatus.ACTIVE, nullable=False,
    )
    document_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    collection_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    organization: Mapped["Organization"] = relationship(back_populates="knowledge_bases")
    data_sources: Mapped[list["DataSource"]] = relationship(
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )
    rag_configs: Mapped[list["RAGConfig"]] = relationship(
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )
