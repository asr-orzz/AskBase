import uuid

from fastapi import APIRouter, HTTPException

from app.auth.dependencies import CurrentUser
from app.core.dependencies import DatabaseSession
from app.rag.pipeline import RAGPipeline, RAGPipelineConfig
from app.schemas.rag import ChunkResponse, RAGQueryRequest, RAGQueryResponse
from app.services.embeddings import get_embedding_provider
from app.services.knowledge_base import KnowledgeBaseService
from app.services.llm import get_llm_provider
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/{kb_id}", response_model=RAGQueryResponse)
async def query_knowledge_base(
    kb_id: uuid.UUID,
    request: RAGQueryRequest,
    db: DatabaseSession,
    user: CurrentUser,
):
    svc = KnowledgeBaseService(db, user.id)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    embedding = get_embedding_provider()
    llm = get_llm_provider()

    pipeline = RAGPipeline(
        vector_store=get_vector_store(),
        embedding_provider=embedding,
        llm_provider=llm,
    )

    config = RAGPipelineConfig(
        collection_name=kb.collection_name,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    result = await pipeline.query(request.question, config)

    return RAGQueryResponse(
        answer=result.answer,
        chunks=[
            ChunkResponse(
                chunk_id=c.chunk_id,
                content=c.content,
                score=c.score,
                document_id=c.document_id,
                document_title=c.document_title,
            )
            for c in result.chunks
        ],
        model=result.llm_response.model,
        input_tokens=result.llm_response.input_tokens,
        output_tokens=result.llm_response.output_tokens,
        total_tokens=result.llm_response.total_tokens,
        retrieval_latency_ms=result.retrieval_latency_ms,
        total_latency_ms=result.total_latency_ms,
    )
