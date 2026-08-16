import enum
import uuid
from typing import Any, TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from app.models.rag_config import RAGConfig


class DeploymentEnv(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ROLLING_BACK = "rolling_back"


class Deployment(BaseModel, TenantMixin):
    __tablename__ = "deployments"

    rag_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False
    )
    environment: Mapped[DeploymentEnv] = mapped_column(
        SAEnum(DeploymentEnv, values_callable=lambda e: [x.value for x in e], name="deployment_env"), nullable=False
    )
    status: Mapped[DeploymentStatus] = mapped_column(
        SAEnum(DeploymentStatus, values_callable=lambda e: [x.value for x in e], name="deployment_status"),
        default=DeploymentStatus.ACTIVE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    traffic_percentage: Mapped[int] = mapped_column(default=100)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )

    rag_config: Mapped["RAGConfig"] = relationship(back_populates="deployments")
