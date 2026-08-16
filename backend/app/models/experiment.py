import enum
import uuid
from typing import Any

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TenantMixin


class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Experiment(BaseModel, TenantMixin):
    __tablename__ = "experiments"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus, values_callable=lambda e: [x.value for x in e], name="experiment_status"),
        default=ExperimentStatus.DRAFT,
        nullable=False,
    )
    variant_a_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False
    )
    variant_b_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False
    )
    variant_a_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="SET NULL"), nullable=True
    )
    variant_b_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation_runs.id", ondelete="SET NULL"), nullable=True
    )
    winner: Mapped[str | None] = mapped_column(String(1), nullable=True)
    results: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
