from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.knowledge_base import KBStatus


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class KnowledgeBaseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    organization_id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    status: KBStatus
    document_count: int
    chunk_count: int
    collection_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseList(BaseModel):
    items: list[KnowledgeBaseResponse]
    total: int
