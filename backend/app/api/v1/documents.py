from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.auth.dependencies import CurrentUser
from app.core.dependencies import DatabaseSession
from app.schemas.document import DocumentResponse, DocumentList
from app.services.ingestion import IngestionService
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["Documents"])

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.get("", response_model=DocumentList)
async def list_documents(
    kb_id: uuid.UUID,
    db: DatabaseSession,
    user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
):
    svc = KnowledgeBaseService(db, user.id)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    items, total = await svc.list_documents(kb_id, skip, limit)
    return DocumentList(items=items, total=total)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: uuid.UUID,
    db: DatabaseSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    title: str | None = Form(None),
):
    kb_svc = KnowledgeBaseService(db, user.id)
    kb = await kb_svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    doc_title = title or file.filename or "Untitled"

    user_api_key = user.custom_api_key if user.use_custom_key else None
    ingestion = IngestionService(db, user.id, api_key=user_api_key)
    try:
        doc = await ingestion.ingest_document(
            kb=kb,
            title=doc_title,
            content=content,
            filename=file.filename or "document",
            mime_type=file.content_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    await db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: DatabaseSession,
    user: CurrentUser,
):
    from sqlalchemy import select
    from app.models.document import Document
    from app.models.chunk import Chunk
    from app.services.vector_store import get_vector_store

    kb_svc = KnowledgeBaseService(db, user.id)
    kb = await kb_svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.knowledge_base_id == kb_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_result = await db.execute(select(Chunk.vector_id).where(Chunk.document_id == doc_id))
    vector_ids = [r for r in chunks_result.scalars().all() if r]

    if vector_ids:
        vector_store = get_vector_store()
        await vector_store.delete(kb.collection_name, vector_ids)

    kb.document_count = max((kb.document_count or 1) - 1, 0)
    kb.chunk_count = max((kb.chunk_count or 0) - doc.chunk_count, 0)

    await db.delete(doc)
    await db.flush()
