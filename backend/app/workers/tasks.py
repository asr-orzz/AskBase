from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger()


def run_async(coro):
    """Run an async function from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.tasks.sync_data_source", max_retries=3)
def sync_data_source(self, data_source_id: str, tenant_id: str, knowledge_base_id: str):
    """Sync a data source: discover → fetch → ingest each document."""

    async def _sync():
        from sqlalchemy import select
        from app.core.database import async_session_factory
        from app.models.data_source import DataSource, SyncStatus
        from app.models.knowledge_base import KnowledgeBase
        from app.connectors import get_connector
        from app.services.ingestion import IngestionService

        async with async_session_factory() as db:
            ds = (await db.execute(
                select(DataSource).where(DataSource.id == uuid.UUID(data_source_id))
            )).scalar_one_or_none()
            if not ds:
                return {"error": "Data source not found"}

            kb = (await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == uuid.UUID(knowledge_base_id))
            )).scalar_one_or_none()
            if not kb:
                return {"error": "Knowledge base not found"}

            ds.sync_status = SyncStatus.RUNNING
            ds.sync_error = None
            await db.commit()

            try:
                connector = get_connector(ds.source_type, ds.config, ds.credentials)
                items = await connector.discover()

                ingestion = IngestionService(db, uuid.UUID(tenant_id))
                ingested = 0

                for item in items:
                    content = await connector.fetch(item)
                    if not content:
                        continue

                    await ingestion.ingest_document(
                        kb=kb,
                        title=item.title,
                        content=content,
                        filename=item.title,
                        mime_type=item.mime_type,
                        data_source_id=ds.id,
                        source_url=item.location,
                    )
                    ingested += 1

                ds.sync_status = SyncStatus.COMPLETED
                ds.last_synced_at = datetime.utcnow()
                ds.document_count = ingested
                await db.commit()

                return {"status": "completed", "documents_ingested": ingested}

            except Exception as e:
                ds.sync_status = SyncStatus.FAILED
                ds.sync_error = str(e)[:500]
                await db.commit()
                raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

    return run_async(_sync())


@celery_app.task(bind=True, name="app.workers.tasks.ingest_document", max_retries=3)
def ingest_document(
    self,
    knowledge_base_id: str,
    tenant_id: str,
    title: str,
    content_b64: str,
    filename: str,
    mime_type: str | None = None,
):
    """Ingest a single document asynchronously."""
    import base64

    async def _ingest():
        from sqlalchemy import select
        from app.core.database import async_session_factory
        from app.models.knowledge_base import KnowledgeBase
        from app.services.ingestion import IngestionService

        content = base64.b64decode(content_b64)

        async with async_session_factory() as db:
            kb = (await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == uuid.UUID(knowledge_base_id))
            )).scalar_one_or_none()
            if not kb:
                return {"error": "Knowledge base not found"}

            ingestion = IngestionService(db, uuid.UUID(tenant_id))
            doc = await ingestion.ingest_document(
                kb=kb,
                title=title,
                content=content,
                filename=filename,
                mime_type=mime_type,
            )
            await db.commit()
            return {"status": "indexed", "document_id": str(doc.id), "chunks": doc.chunk_count}

    return run_async(_ingest())


@celery_app.task(bind=True, name="app.workers.tasks.reindex_knowledge_base", max_retries=1)
def reindex_knowledge_base(self, knowledge_base_id: str, tenant_id: str):
    """Re-embed and re-index all documents in a knowledge base."""

    async def _reindex():
        from sqlalchemy import select
        from app.core.database import async_session_factory
        from app.models.knowledge_base import KnowledgeBase, KBStatus
        from app.models.document import Document, DocumentStatus
        from app.models.chunk import Chunk
        from app.services.embeddings import get_embedding_provider
        from app.services.vector_store import get_vector_store

        async with async_session_factory() as db:
            kb = (await db.execute(
                select(KnowledgeBase).where(KnowledgeBase.id == uuid.UUID(knowledge_base_id))
            )).scalar_one_or_none()
            if not kb:
                return {"error": "Knowledge base not found"}

            kb.status = KBStatus.SYNCING
            await db.commit()

            try:
                docs = (await db.execute(
                    select(Document).where(
                        Document.knowledge_base_id == kb.id,
                        Document.status == DocumentStatus.INDEXED,
                    )
                )).scalars().all()

                embedder = get_embedding_provider()
                vector_store = get_vector_store()
                total_chunks = 0

                for doc in docs:
                    chunks = (await db.execute(
                        select(Chunk).where(Chunk.document_id == doc.id)
                    )).scalars().all()

                    if not chunks:
                        continue

                    texts = [c.content for c in chunks]
                    vectors = await embedder.embed_texts(texts)
                    ids = [c.vector_id for c in chunks if c.vector_id]
                    payloads = [
                        {
                            "content": c.content,
                            "document_id": str(doc.id),
                            "document_title": doc.title,
                            "chunk_index": c.chunk_index,
                            "tenant_id": str(c.tenant_id),
                            "knowledge_base_id": str(kb.id),
                        }
                        for c in chunks
                    ]

                    await vector_store.upsert(kb.collection_name, ids, vectors, payloads)
                    total_chunks += len(chunks)

                kb.status = KBStatus.ACTIVE
                await db.commit()

                return {"status": "completed", "documents": len(docs), "chunks": total_chunks}

            except Exception as e:
                kb.status = KBStatus.ERROR
                await db.commit()
                raise

    return run_async(_reindex())


@celery_app.task(name="app.workers.tasks.run_evaluation")
def run_evaluation(evaluation_run_id: str, tenant_id: str):
    """Placeholder — implemented in Commit 21."""
    return {"status": "pending", "run_id": evaluation_run_id}
