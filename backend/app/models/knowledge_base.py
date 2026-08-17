import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from app.models.document import Document


class KBStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    INDEXING = "indexing"
    ERROR = "error"


class KnowledgeBase(BaseModel, TenantMixin):
    __tablename__ = "knowledge_bases"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[KBStatus] = mapped_column(
        SAEnum(KBStatus, values_callable=lambda e: [x.value for x in e], name="kb_status"),
        default=KBStatus.ACTIVE,
        nullable=False,
    )
    collection_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    document_count: Mapped[int] = mapped_column(default=0)
    chunk_count: Mapped[int] = mapped_column(default=0)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base", cascade="all, delete-orphan"
    )
