import enum
import uuid
from datetime import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from app.models.knowledge_base import KnowledgeBase
    from app.models.document import Document


class SourceType(str, enum.Enum):
    FILE = "file"
    S3 = "s3"
    GITHUB = "github"
    POSTGRESQL = "postgresql"
    REST_API = "rest_api"
    WEB = "web"


class SyncStatus(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DataSource(BaseModel, TenantMixin):
    __tablename__ = "data_sources"

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, values_callable=lambda e: [x.value for x in e], name="source_type"), nullable=False
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    credentials: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sync_status: Mapped[SyncStatus] = mapped_column(
        SAEnum(SyncStatus, values_callable=lambda e: [x.value for x in e], name="sync_status"), default=SyncStatus.IDLE, nullable=False
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_count: Mapped[int] = mapped_column(default=0)

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="data_sources")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="data_source", cascade="all, delete-orphan"
    )
