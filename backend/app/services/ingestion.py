from __future__ import annotations

import uuid
from typing import Any

import structlog
import xxhash
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.services.chunking import get_chunker
from app.services.document_parser import DocumentParser
from app.services.embeddings import get_embedding_provider
from app.services.vector_store import get_vector_store

logger = structlog.get_logger()


class IngestionService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, api_key: str | None = None):
        self.db = db
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.parser = DocumentParser()

    async def ingest_document(
        self,
        kb: KnowledgeBase,
        title: str,
        content: bytes,
        filename: str,
        mime_type: str | None = None,
    ) -> Document:
        content_hash = xxhash.xxh64(content).hexdigest()
        embedder = get_embedding_provider(api_key=self.api_key)

        doc = Document(
            tenant_id=self.tenant_id,
            knowledge_base_id=kb.id,
            title=title,
            mime_type=mime_type,
            content_hash=content_hash,
            file_size=len(content),
            status=DocumentStatus.PROCESSING,
            embedding_model=embedder.model_name,
        )
        self.db.add(doc)
        await self.db.flush()

        try:
            text = await self.parser.parse(content, filename, mime_type)
            if not text.strip():
                doc.status = DocumentStatus.FAILED
                doc.error_message = "No text content extracted"
                await self.db.flush()
                return doc

            chunker = get_chunker("recursive", 1000, 200)
            chunk_results = chunker.chunk(text, metadata={"document_id": str(doc.id)})

            if not chunk_results:
                doc.status = DocumentStatus.FAILED
                doc.error_message = "No chunks produced"
                await self.db.flush()
                return doc

            texts = [c.content for c in chunk_results]
            vectors = await embedder.embed_texts(texts)

            chunk_models: list[Chunk] = []
            vector_ids: list[str] = []
            payloads: list[dict[str, Any]] = []

            for i, (cr, vec) in enumerate(zip(chunk_results, vectors)):
                vid = str(uuid.uuid4())
                vector_ids.append(vid)

                chunk_models.append(Chunk(
                    tenant_id=self.tenant_id,
                    document_id=doc.id,
                    content=cr.content,
                    chunk_index=cr.index,
                    content_hash=cr.content_hash,
                    token_count=cr.token_count,
                    embedding_model=embedder.model_name,
                    vector_id=vid,
                    metadata_={
                        "document_id": str(doc.id),
                        "document_title": title,
                        "chunk_index": i,
                    },
                ))

                payloads.append({
                    "content": cr.content,
                    "document_id": str(doc.id),
                    "document_title": title,
                    "chunk_index": i,
                    "tenant_id": str(self.tenant_id),
                    "knowledge_base_id": str(kb.id),
                })

            self.db.add_all(chunk_models)

            vector_store = get_vector_store()
            await vector_store.upsert(
                collection=kb.collection_name,
                ids=vector_ids,
                vectors=vectors,
                payloads=payloads,
            )

            doc.status = DocumentStatus.INDEXED
            doc.chunk_count = len(chunk_models)
            kb.document_count = (kb.document_count or 0) + 1
            kb.chunk_count = (kb.chunk_count or 0) + len(chunk_models)

            await self.db.flush()
            await logger.ainfo("Document ingested", doc_id=str(doc.id), title=title, chunks=len(chunk_models))

        except Exception as e:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)[:500]
            await self.db.flush()
            await logger.aerror("Ingestion failed", doc_id=str(doc.id), error=str(e))
            raise

        return doc
