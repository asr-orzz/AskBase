from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase, KBStatus
from app.models.document import Document
from app.schemas.knowledge_base import KnowledgeBaseCreate
from app.services.vector_store import get_vector_store

logger = structlog.get_logger()


class KnowledgeBaseService:
    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def create(self, org_id: uuid.UUID, data: KnowledgeBaseCreate) -> KnowledgeBase:
        collection_name = f"kb_{uuid.uuid4().hex[:12]}"

        kb = KnowledgeBase(
            tenant_id=self.tenant_id,
            organization_id=org_id,
            name=data.name,
            description=data.description,
            collection_name=collection_name,
            status=KBStatus.ACTIVE,
        )
        self.db.add(kb)
        await self.db.flush()

        from app.services.embeddings import get_embedding_provider
        embedder = get_embedding_provider()
        vector_store = get_vector_store()
        await vector_store.create_collection(collection_name, dimension=embedder.dimensions)

        await logger.ainfo("Knowledge base created", kb_id=str(kb.id), name=data.name)
        return kb

    async def get(self, kb_id: uuid.UUID) -> KnowledgeBase | None:
        result = await self.db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(self, org_id: uuid.UUID, skip: int = 0, limit: int = 50) -> tuple[list[KnowledgeBase], int]:
        count_q = select(func.count()).select_from(KnowledgeBase).where(
            KnowledgeBase.organization_id == org_id,
            KnowledgeBase.tenant_id == self.tenant_id,
        )
        total = (await self.db.execute(count_q)).scalar() or 0

        q = (
            select(KnowledgeBase)
            .where(
                KnowledgeBase.organization_id == org_id,
                KnowledgeBase.tenant_id == self.tenant_id,
            )
            .order_by(KnowledgeBase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def delete(self, kb_id: uuid.UUID) -> bool:
        kb = await self.get(kb_id)
        if not kb:
            return False

        vector_store = get_vector_store()
        await vector_store.delete_collection(kb.collection_name)

        await self.db.delete(kb)
        await self.db.flush()
        await logger.ainfo("Knowledge base deleted", kb_id=str(kb_id))
        return True

    async def list_documents(
        self, kb_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list[Document], int]:
        count_q = select(func.count()).select_from(Document).where(
            Document.knowledge_base_id == kb_id,
            Document.tenant_id == self.tenant_id,
        )
        total = (await self.db.execute(count_q)).scalar() or 0

        q = (
            select(Document)
            .where(
                Document.knowledge_base_id == kb_id,
                Document.tenant_id == self.tenant_id,
            )
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(q)
        return list(result.scalars().all()), total
