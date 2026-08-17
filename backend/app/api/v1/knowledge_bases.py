from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.core.dependencies import DatabaseSession
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseList,
)
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEMP_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(data: KnowledgeBaseCreate, db: DatabaseSession):
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    kb = await svc.create(TEMP_ORG_ID, data)
    await db.refresh(kb)
    return kb


@router.get("", response_model=KnowledgeBaseList)
async def list_knowledge_bases(db: DatabaseSession, skip: int = 0, limit: int = 50):
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    items, total = await svc.list(TEMP_ORG_ID, skip, limit)
    return KnowledgeBaseList(items=items, total=total)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: uuid.UUID, db: DatabaseSession):
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: uuid.UUID, db: DatabaseSession):
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    deleted = await svc.delete(kb_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
