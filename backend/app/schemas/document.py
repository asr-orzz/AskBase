from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    data_source_id: UUID | None
    title: str
    source_url: str | None
    mime_type: str | None
    content_hash: str
    file_size: int | None
    version: int
    status: DocumentStatus
    chunk_count: int
    embedding_model: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentList(BaseModel):
    items: list[DocumentResponse]
    total: int
