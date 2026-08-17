from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from app.auth.dependencies import CurrentUser
from app.core.dependencies import DatabaseSession
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseList,
)
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(
    data: KnowledgeBaseCreate, db: DatabaseSession, user: CurrentUser
):
    svc = KnowledgeBaseService(db, user.id)
    kb = await svc.create(user.id, data)
    await db.refresh(kb)
    return kb


@router.get("", response_model=KnowledgeBaseList)
async def list_knowledge_bases(
    db: DatabaseSession, user: CurrentUser, skip: int = 0, limit: int = 50
):
    svc = KnowledgeBaseService(db, user.id)
    items, total = await svc.list(user.id, skip, limit)
    return KnowledgeBaseList(items=items, total=total)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: uuid.UUID, db: DatabaseSession, user: CurrentUser
):
    svc = KnowledgeBaseService(db, user.id)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(
    kb_id: uuid.UUID, db: DatabaseSession, user: CurrentUser
):
    svc = KnowledgeBaseService(db, user.id)
    deleted = await svc.delete(kb_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
