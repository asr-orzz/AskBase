from __future__ import annotations

import uuid
import time
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.metrics import (
    EvalMetrics,
    recall_at_k,
    precision_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    faithfulness_score,
    answer_relevance_score,
)
from app.models.evaluation import EvaluationDataset, EvaluationItem, EvaluationRun, EvalStatus
from app.models.knowledge_base import KnowledgeBase
from app.models.rag_config import RAGConfig
from app.rag.pipeline import RAGPipeline, RAGPipelineConfig
from app.services.embeddings import get_embedding_provider
from app.services.llm import get_llm_provider
from app.services.vector_store import get_vector_store

logger = structlog.get_logger()


class EvaluationRunner:
    """Runs a full evaluation: iterates dataset items through the RAG pipeline and computes metrics."""

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def run(self, run_id: uuid.UUID) -> EvaluationRun:
        eval_run = (await self.db.execute(
            select(EvaluationRun).where(EvaluationRun.id == run_id)
        )).scalar_one_or_none()
        if not eval_run:
            raise ValueError("Evaluation run not found")

        dataset = (await self.db.execute(
            select(EvaluationDataset).where(EvaluationDataset.id == eval_run.dataset_id)
        )).scalar_one_or_none()
        if not dataset:
            raise ValueError("Dataset not found")

        rag_config = (await self.db.execute(
            select(RAGConfig).where(RAGConfig.id == eval_run.rag_config_id)
        )).scalar_one_or_none()
        if not rag_config:
            raise ValueError("RAG config not found")

        kb = (await self.db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == rag_config.knowledge_base_id)
        )).scalar_one_or_none()
        if not kb:
            raise ValueError("Knowledge base not found")

        items_result = await self.db.execute(
            select(EvaluationItem).where(EvaluationItem.dataset_id == dataset.id)
        )
        items = list(items_result.scalars().all())

        eval_run.status = EvalStatus.RUNNING
        eval_run.total_items = len(items)
        await self.db.flush()

        pipeline = RAGPipeline(
            vector_store=get_vector_store(),
            embedding_provider=get_embedding_provider(
                rag_config.embedding_provider,
                rag_config.embedding_model,
                rag_config.embedding_dimensions,
            ),
            llm_provider=get_llm_provider(
                rag_config.llm_provider,
                rag_config.llm_model,
            ),
        )

        config = RAGPipelineConfig(
            collection_name=kb.collection_name,
            top_k=rag_config.top_k,
            similarity_threshold=rag_config.similarity_threshold,
            temperature=rag_config.temperature,
            max_tokens=rag_config.max_tokens,
            system_prompt=rag_config.system_prompt,
        )

        all_metrics: list[EvalMetrics] = []
        detailed_results: list[dict[str, Any]] = []
        total_cost = 0.0

        try:
            for i, item in enumerate(items):
                item_start = time.perf_counter()

                result = await pipeline.query(item.question, config)

                retrieved_doc_ids = [c.document_id for c in result.chunks]
                expected_doc_ids = item.expected_contexts or []

                r_at_k = recall_at_k(retrieved_doc_ids, expected_doc_ids, k=rag_config.top_k)
                p_at_k = precision_at_k(retrieved_doc_ids, expected_doc_ids, k=rag_config.top_k)
                mrr = mean_reciprocal_rank(retrieved_doc_ids, expected_doc_ids)
                ndcg = ndcg_at_k(retrieved_doc_ids, expected_doc_ids, k=rag_config.top_k)

                faith = 0.0
                relevance = 0.0
                try:
                    contexts = [c.content for c in result.chunks]
                    faith = await faithfulness_score(
                        result.answer, contexts,
                        rag_config.llm_provider, rag_config.llm_model,
                    )
                    relevance = await answer_relevance_score(
                        item.question, result.answer,
                        rag_config.llm_provider, rag_config.llm_model,
                    )
                except Exception:
                    pass

                item_latency = (time.perf_counter() - item_start) * 1000

                metrics = EvalMetrics(
                    recall_at_k=r_at_k,
                    precision_at_k=p_at_k,
                    mrr=mrr,
                    ndcg=ndcg,
                    faithfulness=faith,
                    answer_relevance=relevance,
                    latency_ms=item_latency,
                )
                all_metrics.append(metrics)

                detailed_results.append({
                    "question": item.question,
                    "answer": result.answer,
                    "expected_answer": item.expected_answer,
                    "recall_at_k": r_at_k,
                    "precision_at_k": p_at_k,
                    "mrr": mrr,
                    "ndcg": ndcg,
                    "faithfulness": faith,
                    "answer_relevance": relevance,
                    "latency_ms": item_latency,
                    "tokens": result.llm_response.total_tokens,
                    "chunks_retrieved": len(result.chunks),
                })

                eval_run.completed_items = i + 1
                await self.db.flush()

            # Aggregate
            n = len(all_metrics) or 1
            eval_run.recall_at_k = sum(m.recall_at_k for m in all_metrics) / n
            eval_run.precision_at_k = sum(m.precision_at_k for m in all_metrics) / n
            eval_run.mrr = sum(m.mrr for m in all_metrics) / n
            eval_run.ndcg = sum(m.ndcg for m in all_metrics) / n
            eval_run.faithfulness = sum(m.faithfulness for m in all_metrics) / n
            eval_run.answer_relevance = sum(m.answer_relevance for m in all_metrics) / n
            eval_run.avg_latency_ms = sum(m.latency_ms for m in all_metrics) / n
            eval_run.detailed_results = {"items": detailed_results}
            eval_run.status = EvalStatus.COMPLETED

            await self.db.flush()

            await logger.ainfo(
                "Evaluation complete",
                run_id=str(run_id),
                items=len(items),
                recall=round(eval_run.recall_at_k, 3),
                faithfulness=round(eval_run.faithfulness, 3),
                avg_latency=round(eval_run.avg_latency_ms, 1),
            )

        except Exception as e:
            eval_run.status = EvalStatus.FAILED
            eval_run.error_message = str(e)[:500]
            await self.db.flush()
            raise

        return eval_run
