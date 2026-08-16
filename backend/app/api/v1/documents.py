from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.dependencies import DatabaseSession
from app.schemas.document import DocumentResponse
from app.services.ingestion import IngestionService
from app.services.knowledge_base import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases/{kb_id}/documents", tags=["Documents"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    kb_id: uuid.UUID,
    db: DatabaseSession,
    file: UploadFile = File(...),
    title: str | None = Form(None),
):
    kb_svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    kb = await kb_svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    doc_title = title or file.filename or "Untitled"

    rag_config = await kb_svc.get_active_rag_config(kb_id)

    ingestion = IngestionService(db, TEMP_TENANT_ID)
    doc = await ingestion.ingest_document(
        kb=kb,
        title=doc_title,
        content=content,
        filename=file.filename or "document",
        mime_type=file.content_type,
        embedding_provider=rag_config.embedding_provider if rag_config else "openai",
        embedding_model=rag_config.embedding_model if rag_config else "text-embedding-3-small",
        embedding_dims=rag_config.embedding_dimensions if rag_config else 1536,
        chunk_strategy=rag_config.chunking_strategy if rag_config else "recursive",
        chunk_size=rag_config.chunk_size if rag_config else 800,
        chunk_overlap=rag_config.chunk_overlap if rag_config else 100,
    )

    return doc


@router.post("/upload-batch", response_model=list[DocumentResponse], status_code=201)
async def upload_documents_batch(
    kb_id: uuid.UUID,
    db: DatabaseSession,
    files: list[UploadFile] = File(...),
):
    kb_svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    kb = await kb_svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Max 20 files per batch")

    rag_config = await kb_svc.get_active_rag_config(kb_id)
    ingestion = IngestionService(db, TEMP_TENANT_ID)
    results = []

    for file in files:
        content = await file.read()
        if not content or len(content) > MAX_FILE_SIZE:
            continue

        doc = await ingestion.ingest_document(
            kb=kb,
            title=file.filename or "Untitled",
            content=content,
            filename=file.filename or "document",
            mime_type=file.content_type,
            embedding_provider=rag_config.embedding_provider if rag_config else "openai",
            embedding_model=rag_config.embedding_model if rag_config else "text-embedding-3-small",
            embedding_dims=rag_config.embedding_dimensions if rag_config else 1536,
            chunk_strategy=rag_config.chunking_strategy if rag_config else "recursive",
            chunk_size=rag_config.chunk_size if rag_config else 800,
            chunk_overlap=rag_config.chunk_overlap if rag_config else 100,
        )
        results.append(doc)

    return results


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    db: DatabaseSession,
):
    from sqlalchemy import select
    from app.models.document import Document
    from app.models.chunk import Chunk
    from app.services.vector_store import get_vector_store

    kb_svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    kb = await kb_svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.knowledge_base_id == kb_id,
            Document.tenant_id == TEMP_TENANT_ID,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_result = await db.execute(
        select(Chunk.vector_id).where(Chunk.document_id == doc_id)
    )
    vector_ids = [r for r in chunks_result.scalars().all() if r]

    if vector_ids:
        vector_store = get_vector_store()
        await vector_store.delete(kb.collection_name, vector_ids)

    kb.document_count = max((kb.document_count or 1) - 1, 0)
    kb.chunk_count = max((kb.chunk_count or 0) - doc.chunk_count, 0)

    await db.delete(doc)
    await db.flush()
