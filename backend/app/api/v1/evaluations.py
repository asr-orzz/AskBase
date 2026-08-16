from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DatabaseSession
from app.models.evaluation import EvaluationDataset, EvaluationItem, EvaluationRun, EvalStatus

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# --- Schemas ---

class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    knowledge_base_id: str


class DatasetItemCreate(BaseModel):
    question: str
    expected_answer: str | None = None
    expected_contexts: list[str] | None = None


class EvalRunCreate(BaseModel):
    dataset_id: str
    rag_config_id: str


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: str | None
    knowledge_base_id: str
    item_count: int
    created_at: str

    model_config = {"from_attributes": True}


class EvalRunResponse(BaseModel):
    id: str
    dataset_id: str
    rag_config_id: str
    status: str
    recall_at_k: float | None
    precision_at_k: float | None
    mrr: float | None
    ndcg: float | None
    faithfulness: float | None
    answer_relevance: float | None
    avg_latency_ms: float | None
    total_items: int
    completed_items: int
    error_message: str | None
    created_at: str

    model_config = {"from_attributes": True}


# --- Datasets ---

@router.post("/datasets", status_code=201)
async def create_dataset(data: DatasetCreate, db: DatabaseSession):
    dataset = EvaluationDataset(
        tenant_id=TEMP_TENANT_ID,
        name=data.name,
        description=data.description,
        knowledge_base_id=uuid.UUID(data.knowledge_base_id),
    )
    db.add(dataset)
    await db.flush()
    return {"id": str(dataset.id), "name": dataset.name}


@router.get("/datasets")
async def list_datasets(db: DatabaseSession):
    result = await db.execute(
        select(EvaluationDataset)
        .where(EvaluationDataset.tenant_id == TEMP_TENANT_ID)
        .order_by(EvaluationDataset.created_at.desc())
    )
    datasets = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "description": d.description,
            "item_count": d.item_count,
            "created_at": d.created_at.isoformat() if d.created_at else "",
        }
        for d in datasets
    ]


@router.post("/datasets/{dataset_id}/items", status_code=201)
async def add_dataset_items(
    dataset_id: uuid.UUID,
    items: list[DatasetItemCreate],
    db: DatabaseSession,
):
    dataset = (await db.execute(
        select(EvaluationDataset).where(EvaluationDataset.id == dataset_id)
    )).scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    for item_data in items:
        item = EvaluationItem(
            dataset_id=dataset_id,
            question=item_data.question,
            expected_answer=item_data.expected_answer,
            expected_contexts=item_data.expected_contexts,
        )
        db.add(item)

    dataset.item_count = (dataset.item_count or 0) + len(items)
    await db.flush()
    return {"added": len(items), "total": dataset.item_count}


@router.get("/datasets/{dataset_id}/items")
async def list_dataset_items(dataset_id: uuid.UUID, db: DatabaseSession):
    result = await db.execute(
        select(EvaluationItem).where(EvaluationItem.dataset_id == dataset_id)
    )
    items = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "question": i.question,
            "expected_answer": i.expected_answer,
            "expected_contexts": i.expected_contexts,
        }
        for i in items
    ]


# --- Runs ---

@router.post("/runs", status_code=201)
async def create_evaluation_run(data: EvalRunCreate, db: DatabaseSession):
    run = EvaluationRun(
        tenant_id=TEMP_TENANT_ID,
        dataset_id=uuid.UUID(data.dataset_id),
        rag_config_id=uuid.UUID(data.rag_config_id),
        status=EvalStatus.PENDING,
    )
    db.add(run)
    await db.flush()

    from app.workers.tasks import run_evaluation
    run_evaluation.delay(str(run.id), str(TEMP_TENANT_ID))

    return {"id": str(run.id), "status": "queued"}


@router.get("/runs")
async def list_evaluation_runs(db: DatabaseSession):
    result = await db.execute(
        select(EvaluationRun)
        .where(EvaluationRun.tenant_id == TEMP_TENANT_ID)
        .order_by(EvaluationRun.created_at.desc())
    )
    runs = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "dataset_id": str(r.dataset_id),
            "rag_config_id": str(r.rag_config_id),
            "status": r.status.value if r.status else "pending",
            "recall_at_k": r.recall_at_k,
            "precision_at_k": r.precision_at_k,
            "mrr": r.mrr,
            "ndcg": r.ndcg,
            "faithfulness": r.faithfulness,
            "answer_relevance": r.answer_relevance,
            "avg_latency_ms": r.avg_latency_ms,
            "total_items": r.total_items,
            "completed_items": r.completed_items,
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in runs
    ]


@router.get("/runs/{run_id}")
async def get_evaluation_run(run_id: uuid.UUID, db: DatabaseSession):
    run = (await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )).scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Evaluation run not found")

    return {
        "id": str(run.id),
        "status": run.status.value if run.status else "pending",
        "recall_at_k": run.recall_at_k,
        "precision_at_k": run.precision_at_k,
        "mrr": run.mrr,
        "ndcg": run.ndcg,
        "faithfulness": run.faithfulness,
        "answer_relevance": run.answer_relevance,
        "avg_latency_ms": run.avg_latency_ms,
        "total_items": run.total_items,
        "completed_items": run.completed_items,
        "detailed_results": run.detailed_results,
        "error_message": run.error_message,
    }
