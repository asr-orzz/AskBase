from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import DatabaseSession
from app.models.experiment import Experiment, ExperimentStatus

router = APIRouter(prefix="/experiments", tags=["Experiments"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None
    knowledge_base_id: str
    dataset_id: str
    variant_a_config_id: str
    variant_b_config_id: str


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str | None
    status: str
    knowledge_base_id: str
    dataset_id: str
    variant_a_config_id: str
    variant_b_config_id: str
    variant_a_run_id: str | None
    variant_b_run_id: str | None
    winner: str | None
    results: dict | None
    created_at: str


@router.post("", status_code=201)
async def create_experiment(data: ExperimentCreate, db: DatabaseSession):
    experiment = Experiment(
        tenant_id=TEMP_TENANT_ID,
        name=data.name,
        description=data.description,
        knowledge_base_id=uuid.UUID(data.knowledge_base_id),
        dataset_id=uuid.UUID(data.dataset_id),
        variant_a_config_id=uuid.UUID(data.variant_a_config_id),
        variant_b_config_id=uuid.UUID(data.variant_b_config_id),
        status=ExperimentStatus.DRAFT,
    )
    db.add(experiment)
    await db.flush()
    return {"id": str(experiment.id), "name": experiment.name, "status": "draft"}


@router.get("")
async def list_experiments(db: DatabaseSession):
    result = await db.execute(
        select(Experiment)
        .where(Experiment.tenant_id == TEMP_TENANT_ID)
        .order_by(Experiment.created_at.desc())
    )
    experiments = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "description": e.description,
            "status": e.status.value if e.status else "draft",
            "winner": e.winner,
            "created_at": e.created_at.isoformat() if e.created_at else "",
        }
        for e in experiments
    ]


@router.get("/{experiment_id}")
async def get_experiment(experiment_id: uuid.UUID, db: DatabaseSession):
    experiment = (await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )).scalar_one_or_none()
    if not experiment:
        raise HTTPException(404, "Experiment not found")

    return {
        "id": str(experiment.id),
        "name": experiment.name,
        "description": experiment.description,
        "status": experiment.status.value if experiment.status else "draft",
        "knowledge_base_id": str(experiment.knowledge_base_id),
        "dataset_id": str(experiment.dataset_id),
        "variant_a_config_id": str(experiment.variant_a_config_id),
        "variant_b_config_id": str(experiment.variant_b_config_id),
        "variant_a_run_id": str(experiment.variant_a_run_id) if experiment.variant_a_run_id else None,
        "variant_b_run_id": str(experiment.variant_b_run_id) if experiment.variant_b_run_id else None,
        "winner": experiment.winner,
        "results": experiment.results,
        "created_at": experiment.created_at.isoformat() if experiment.created_at else "",
    }


@router.post("/{experiment_id}/run", status_code=202)
async def run_experiment(experiment_id: uuid.UUID, db: DatabaseSession):
    experiment = (await db.execute(
        select(Experiment).where(Experiment.id == experiment_id)
    )).scalar_one_or_none()
    if not experiment:
        raise HTTPException(404, "Experiment not found")
    if experiment.status == ExperimentStatus.RUNNING:
        raise HTTPException(409, "Experiment is already running")

    experiment.status = ExperimentStatus.DRAFT
    experiment.winner = None
    experiment.results = {}
    await db.flush()

    from app.workers.tasks import run_experiment_task
    run_experiment_task.delay(str(experiment_id), str(TEMP_TENANT_ID))

    return {"id": str(experiment.id), "status": "queued"}
