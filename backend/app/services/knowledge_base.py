from __future__ import annotations

import uuid

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase, KBStatus
from app.models.data_source import DataSource
from app.models.document import Document
from app.models.rag_config import RAGConfig
from app.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate
from app.schemas.rag import RAGConfigCreate
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

        vector_store = get_vector_store()
        await vector_store.create_collection(collection_name, dimension=1536)

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

    async def update(self, kb_id: uuid.UUID, data: KnowledgeBaseUpdate) -> KnowledgeBase | None:
        kb = await self.get(kb_id)
        if not kb:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kb, key, value)

        await self.db.flush()
        return kb

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

    # --- Data Sources ---

    async def add_data_source(self, kb_id: uuid.UUID, data: DataSourceCreate) -> DataSource:
        ds = DataSource(
            tenant_id=self.tenant_id,
            knowledge_base_id=kb_id,
            name=data.name,
            source_type=data.source_type,
            config=data.config,
            credentials=data.credentials,
        )
        self.db.add(ds)
        await self.db.flush()
        return ds

    async def list_data_sources(self, kb_id: uuid.UUID) -> list[DataSource]:
        result = await self.db.execute(
            select(DataSource).where(
                DataSource.knowledge_base_id == kb_id,
                DataSource.tenant_id == self.tenant_id,
            )
        )
        return list(result.scalars().all())

    async def delete_data_source(self, ds_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(DataSource).where(
                DataSource.id == ds_id,
                DataSource.tenant_id == self.tenant_id,
            )
        )
        ds = result.scalar_one_or_none()
        if not ds:
            return False
        await self.db.delete(ds)
        await self.db.flush()
        return True

    # --- Documents ---

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

    # --- RAG Configs ---

    async def create_rag_config(self, kb_id: uuid.UUID, data: RAGConfigCreate) -> RAGConfig:
        count_q = select(func.count()).select_from(RAGConfig).where(
            RAGConfig.knowledge_base_id == kb_id,
        )
        version = ((await self.db.execute(count_q)).scalar() or 0) + 1

        config = RAGConfig(
            tenant_id=self.tenant_id,
            knowledge_base_id=kb_id,
            name=data.name,
            version=version,
            chunking_strategy=data.chunking_strategy,
            chunk_size=data.chunk_size,
            chunk_overlap=data.chunk_overlap,
            embedding_provider=data.embedding_provider,
            embedding_model=data.embedding_model,
            embedding_dimensions=data.embedding_dimensions,
            retrieval_mode=data.retrieval_mode,
            top_k=data.top_k,
            similarity_threshold=data.similarity_threshold,
            reranker_enabled=data.reranker_enabled,
            reranker_provider=data.reranker_provider,
            reranker_model=data.reranker_model,
            reranker_top_k=data.reranker_top_k,
            llm_provider=data.llm_provider,
            llm_model=data.llm_model,
            temperature=data.temperature,
            max_tokens=data.max_tokens,
            system_prompt=data.system_prompt,
        )
        self.db.add(config)
        await self.db.flush()
        return config

    async def list_rag_configs(self, kb_id: uuid.UUID) -> list[RAGConfig]:
        result = await self.db.execute(
            select(RAGConfig)
            .where(
                RAGConfig.knowledge_base_id == kb_id,
                RAGConfig.tenant_id == self.tenant_id,
            )
            .order_by(RAGConfig.version.desc())
        )
        return list(result.scalars().all())

    async def get_active_rag_config(self, kb_id: uuid.UUID) -> RAGConfig | None:
        result = await self.db.execute(
            select(RAGConfig).where(
                RAGConfig.knowledge_base_id == kb_id,
                RAGConfig.tenant_id == self.tenant_id,
                RAGConfig.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()
