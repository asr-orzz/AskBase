import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.dependencies import DatabaseSession
from app.rag.pipeline import RAGPipeline, RAGPipelineConfig, RetrievedChunk
from app.schemas.rag import ChunkResponse, RAGQueryRequest, RAGQueryResponse
from app.services.embeddings import get_embedding_provider
from app.services.knowledge_base import KnowledgeBaseService
from app.services.llm import get_llm_provider
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/query", tags=["Query"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.post("/{kb_id}", response_model=RAGQueryResponse)
async def query_knowledge_base(
    kb_id: uuid.UUID,
    request: RAGQueryRequest,
    db: DatabaseSession,
):
    svc = KnowledgeBaseService(db, TEMP_TENANT_ID)
    kb = await svc.get(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    rag_config = await svc.get_active_rag_config(kb_id)

    embedding = get_embedding_provider(
        provider=rag_config.embedding_provider if rag_config else "openai",
        model=rag_config.embedding_model if rag_config else None,
        dimensions=rag_config.embedding_dimensions if rag_config else None,
    )
    llm = get_llm_provider(
        provider=rag_config.llm_provider if rag_config else "openai",
        model=rag_config.llm_model if rag_config else None,
    )

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
        system_prompt=rag_config.system_prompt if rag_config else None,
        filters=request.filters,
    )

    if request.stream:
        return StreamingResponse(
            _stream_response(pipeline, request.question, config),
            media_type="text/event-stream",
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


async def _stream_response(pipeline: RAGPipeline, question: str, config: RAGPipelineConfig):
    """SSE stream: sends sources first, then LLM tokens."""
    import json

    async for item in pipeline.stream_query(question, config):
        if isinstance(item, RetrievedChunk):
            data = json.dumps({
                "type": "source",
                "chunk_id": item.chunk_id,
                "document_title": item.document_title,
                "score": item.score,
            })
            yield f"data: {data}\n\n"
        else:
            data = json.dumps({"type": "token", "content": item})
            yield f"data: {data}\n\n"

    yield "data: [DONE]\n\n"
