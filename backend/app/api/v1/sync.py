from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.dependencies import DatabaseSession
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/sync", tags=["Sync"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class SyncResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.post("/{kb_id}/data-sources/{ds_id}", response_model=SyncResponse)
async def trigger_sync(kb_id: uuid.UUID, ds_id: uuid.UUID, db: DatabaseSession):
    """Trigger an async data source sync via Celery."""
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)

    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    data_sources = await svc.list_data_sources(kb_id)
    ds = next((d for d in data_sources if d.id == ds_id), None)
    if not ds:
        raise HTTPException(status_code=404, detail="Data source not found")

    from app.workers.tasks import sync_data_source

    task = sync_data_source.delay(
        data_source_id=str(ds_id),
        tenant_id=str(TEMP_TENANT_ID),
        knowledge_base_id=str(kb_id),
    )

    return SyncResponse(
        task_id=task.id,
        status="queued",
        message=f"Sync queued for data source '{ds.name}'",
    )


@router.post("/{kb_id}/reindex", response_model=SyncResponse)
async def trigger_reindex(kb_id: uuid.UUID, db: DatabaseSession):
    """Trigger a full re-index of a knowledge base via Celery."""
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)

    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    from app.workers.tasks import reindex_knowledge_base

    task = reindex_knowledge_base.delay(
        knowledge_base_id=str(kb_id),
        tenant_id=str(TEMP_TENANT_ID),
    )

    return SyncResponse(
        task_id=task.id,
        status="queued",
        message=f"Re-index queued for '{kb.name}'",
    )
