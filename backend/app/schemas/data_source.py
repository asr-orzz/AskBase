from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.data_source import SourceType, SyncStatus


class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    source_type: SourceType
    config: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, Any] | None = None


class DataSourceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    config: dict[str, Any] | None = None
    credentials: dict[str, Any] | None = None


class DataSourceResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    name: str
    source_type: SourceType
    config: dict[str, Any]
    sync_status: SyncStatus
    last_synced_at: datetime | None
    sync_error: str | None
    document_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
