import uuid

from fastapi import APIRouter, HTTPException, Query

from app.core.dependencies import DatabaseSession
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseList,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)
from app.schemas.data_source import DataSourceCreate, DataSourceResponse
from app.schemas.document import DocumentList
from app.schemas.rag import RAGConfigCreate, RAGConfigResponse
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["Knowledge Bases"])

# Placeholder tenant/org — replaced by real auth in Commit 24
TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEMP_ORG_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _get_service(db: DatabaseSession) -> KnowledgeBaseService:
    return KnowledgeBaseService(db, TEMP_TENANT_ID)


@router.post("", response_model=KnowledgeBaseResponse, status_code=201)
async def create_knowledge_base(data: KnowledgeBaseCreate, db: DatabaseSession):
    svc = _get_service(db)
    kb = await svc.create(TEMP_ORG_ID, data)
    return kb


@router.get("", response_model=KnowledgeBaseList)
async def list_knowledge_bases(
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    svc = _get_service(db)
    items, total = await svc.list(TEMP_ORG_ID, skip=skip, limit=limit)
    return KnowledgeBaseList(items=items, total=total)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(kb_id: uuid.UUID, db: DatabaseSession):
    svc = _get_service(db)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.patch("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: uuid.UUID, data: KnowledgeBaseUpdate, db: DatabaseSession
):
    svc = _get_service(db)
    kb = await svc.update(kb_id, data)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/{kb_id}", status_code=204)
async def delete_knowledge_base(kb_id: uuid.UUID, db: DatabaseSession):
    svc = _get_service(db)
    deleted = await svc.delete(kb_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Knowledge base not found")


# --- Data Sources ---


@router.post("/{kb_id}/data-sources", response_model=DataSourceResponse, status_code=201)
async def add_data_source(
    kb_id: uuid.UUID, data: DataSourceCreate, db: DatabaseSession
):
    svc = _get_service(db)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    ds = await svc.add_data_source(kb_id, data)
    return ds


@router.get("/{kb_id}/data-sources", response_model=list[DataSourceResponse])
async def list_data_sources(kb_id: uuid.UUID, db: DatabaseSession):
    svc = _get_service(db)
    return await svc.list_data_sources(kb_id)


@router.delete("/{kb_id}/data-sources/{ds_id}", status_code=204)
async def delete_data_source(
    kb_id: uuid.UUID, ds_id: uuid.UUID, db: DatabaseSession
):
    svc = _get_service(db)
    deleted = await svc.delete_data_source(ds_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Data source not found")


# --- Documents ---


@router.get("/{kb_id}/documents", response_model=DocumentList)
async def list_documents(
    kb_id: uuid.UUID,
    db: DatabaseSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    svc = _get_service(db)
    items, total = await svc.list_documents(kb_id, skip=skip, limit=limit)
    return DocumentList(items=items, total=total)


# --- RAG Configs ---


@router.post("/{kb_id}/rag-configs", response_model=RAGConfigResponse, status_code=201)
async def create_rag_config(
    kb_id: uuid.UUID, data: RAGConfigCreate, db: DatabaseSession
):
    svc = _get_service(db)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    config = await svc.create_rag_config(kb_id, data)
    return config


@router.get("/{kb_id}/rag-configs", response_model=list[RAGConfigResponse])
async def list_rag_configs(kb_id: uuid.UUID, db: DatabaseSession):
    svc = _get_service(db)
    return await svc.list_rag_configs(kb_id)
