from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import structlog
import xxhash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import BaseConnector, ChangeOperation, DocumentEvent
from app.models.chunk import Chunk
from app.models.document import Document, DocumentStatus
from app.models.knowledge_base import KnowledgeBase
from app.services.chunking import get_chunker, ChunkResult
from app.services.document_parser import DocumentParser
from app.services.embeddings import get_embedding_provider
from app.services.vector_store import get_vector_store

logger = structlog.get_logger()


@dataclass
class SyncStats:
    discovered: int = 0
    unchanged: int = 0
    created: int = 0
    updated: int = 0
    deleted: int = 0
    failed: int = 0
    chunks_added: int = 0
    chunks_removed: int = 0


class IncrementalIndexer:
    """Handles incremental sync: only processes changed documents.

    Strategy:
        1. Discover all items from the connector
        2. For each item, compute content_hash
        3. Compare against existing document hashes in Postgres
        4. Skip unchanged, process created/updated, remove deleted
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.parser = DocumentParser()

    async def sync(
        self,
        kb: KnowledgeBase,
        connector: BaseConnector,
        data_source_id: uuid.UUID,
        embedding_provider: str = "openai",
        embedding_model: str = "text-embedding-3-small",
        embedding_dims: int = 1536,
        chunk_strategy: str = "recursive",
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> SyncStats:
        stats = SyncStats()

        # 1. Get existing documents for this data source
        existing_docs = await self._get_existing_docs(data_source_id)
        existing_by_source_url: dict[str, Document] = {
            doc.source_url: doc for doc in existing_docs if doc.source_url
        }

        # 2. Discover items from connector
        items = await connector.discover()
        stats.discovered = len(items)

        discovered_ids: set[str] = set()

        for item in items:
            discovered_ids.add(item.location)

            try:
                # 3. Fetch content and compute hash
                content = await connector.fetch(item)
                if not content:
                    continue

                content_hash = xxhash.xxh64(content).hexdigest()

                existing_doc = existing_by_source_url.get(item.location)

                if existing_doc and existing_doc.content_hash == content_hash:
                    # Unchanged — skip
                    stats.unchanged += 1
                    continue

                if existing_doc:
                    # Updated — remove old chunks, re-process
                    chunks_removed = await self._remove_document_vectors(kb, existing_doc)
                    stats.chunks_removed += chunks_removed

                    await self._process_document(
                        kb=kb,
                        doc=existing_doc,
                        content=content,
                        content_hash=content_hash,
                        title=item.title,
                        mime_type=item.mime_type,
                        embedding_provider=embedding_provider,
                        embedding_model=embedding_model,
                        embedding_dims=embedding_dims,
                        chunk_strategy=chunk_strategy,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    )
                    existing_doc.version += 1
                    stats.updated += 1
                else:
                    # Created — new document
                    doc = Document(
                        tenant_id=self.tenant_id,
                        knowledge_base_id=kb.id,
                        data_source_id=data_source_id,
                        title=item.title,
                        source_url=item.location,
                        mime_type=item.mime_type,
                        content_hash=content_hash,
                        file_size=len(content),
                        status=DocumentStatus.PROCESSING,
                        embedding_model=f"{embedding_provider}/{embedding_model}",
                    )
                    self.db.add(doc)
                    await self.db.flush()

                    await self._process_document(
                        kb=kb,
                        doc=doc,
                        content=content,
                        content_hash=content_hash,
                        title=item.title,
                        mime_type=item.mime_type,
                        embedding_provider=embedding_provider,
                        embedding_model=embedding_model,
                        embedding_dims=embedding_dims,
                        chunk_strategy=chunk_strategy,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    )
                    stats.created += 1

            except Exception as e:
                stats.failed += 1
                await logger.aerror("Failed to process item", item=item.title, error=str(e))

        # 4. Handle deleted documents (in source but no longer discovered)
        for source_url, doc in existing_by_source_url.items():
            if source_url not in discovered_ids:
                chunks_removed = await self._remove_document_vectors(kb, doc)
                stats.chunks_removed += chunks_removed
                doc.status = DocumentStatus.DELETED
                stats.deleted += 1

        await self.db.flush()

        await logger.ainfo(
            "Incremental sync complete",
            kb=kb.name,
            discovered=stats.discovered,
            unchanged=stats.unchanged,
            created=stats.created,
            updated=stats.updated,
            deleted=stats.deleted,
            failed=stats.failed,
        )

        return stats

    async def _get_existing_docs(self, data_source_id: uuid.UUID) -> list[Document]:
        result = await self.db.execute(
            select(Document).where(
                Document.data_source_id == data_source_id,
                Document.tenant_id == self.tenant_id,
                Document.status != DocumentStatus.DELETED,
            )
        )
        return list(result.scalars().all())

    async def _remove_document_vectors(self, kb: KnowledgeBase, doc: Document) -> int:
        result = await self.db.execute(
            select(Chunk).where(Chunk.document_id == doc.id)
        )
        chunks = list(result.scalars().all())

        if not chunks:
            return 0

        vector_ids = [c.vector_id for c in chunks if c.vector_id]
        if vector_ids:
            vector_store = get_vector_store()
            await vector_store.delete(kb.collection_name, vector_ids)

        for chunk in chunks:
            await self.db.delete(chunk)

        return len(chunks)

    async def _process_document(
        self,
        kb: KnowledgeBase,
        doc: Document,
        content: bytes,
        content_hash: str,
        title: str,
        mime_type: str | None,
        embedding_provider: str,
        embedding_model: str,
        embedding_dims: int,
        chunk_strategy: str,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        # Parse
        text = await self.parser.parse(content, title, mime_type)
        if not text.strip():
            doc.status = DocumentStatus.FAILED
            doc.error_message = "No text content extracted"
            return

        # Chunk
        chunker = get_chunker(chunk_strategy, chunk_size, chunk_overlap)
        chunk_results = chunker.chunk(text)
        if not chunk_results:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "No chunks produced"
            return

        # Embed
        embedder = get_embedding_provider(embedding_provider, embedding_model, embedding_dims)
        texts = [c.content for c in chunk_results]
        vectors = await embedder.embed_texts(texts)

        # Store chunks + index
        vector_ids: list[str] = []
        payloads: list[dict[str, Any]] = []

        for i, (cr, vec) in enumerate(zip(chunk_results, vectors)):
            vid = str(uuid.uuid4())
            vector_ids.append(vid)

            chunk_model = Chunk(
                tenant_id=self.tenant_id,
                document_id=doc.id,
                content=cr.content,
                chunk_index=i,
                content_hash=cr.content_hash,
                token_count=cr.token_count,
                embedding_model=f"{embedding_provider}/{embedding_model}",
                vector_id=vid,
                metadata_={
                    "document_id": str(doc.id),
                    "document_title": title,
                    "chunk_index": i,
                },
            )
            self.db.add(chunk_model)

            payloads.append({
                "content": cr.content,
                "document_id": str(doc.id),
                "document_title": title,
                "chunk_index": i,
                "tenant_id": str(self.tenant_id),
                "knowledge_base_id": str(kb.id),
            })

        vector_store = get_vector_store()
        await vector_store.upsert(kb.collection_name, vector_ids, vectors, payloads)

        doc.content_hash = content_hash
        doc.status = DocumentStatus.INDEXED
        doc.chunk_count = len(chunk_results)
        doc.embedding_model = f"{embedding_provider}/{embedding_model}"
