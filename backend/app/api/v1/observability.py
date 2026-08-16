from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from starlette.responses import Response

from app.core.dependencies import DatabaseSession
from app.observability.cost_tracker import get_cost_summary
from app.observability.metrics import get_metrics, get_metrics_content_type

router = APIRouter(tags=["Observability"])

TEMP_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.get("/metrics")
async def prometheus_metrics():
    return Response(content=get_metrics(), media_type=get_metrics_content_type())


@router.get("/cost/summary")
async def cost_summary(
    db: DatabaseSession,
    days: int = Query(default=30, ge=1, le=365),
):
    return await get_cost_summary(db, TEMP_TENANT_ID, days)


@router.get("/cost/usage")
async def cost_usage(
    db: DatabaseSession,
    days: int = Query(default=30, ge=1, le=365),
    provider: str | None = None,
    operation: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
):
    from sqlalchemy import select
    from app.models.usage import UsageRecord
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        select(UsageRecord)
        .where(UsageRecord.tenant_id == TEMP_TENANT_ID, UsageRecord.created_at >= cutoff)
    )
    if provider:
        query = query.where(UsageRecord.provider == provider)
    if operation:
        query = query.where(UsageRecord.operation == operation)

    query = query.order_by(UsageRecord.created_at.desc()).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "operation": r.operation,
            "provider": r.provider,
            "model": r.model,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "total_tokens": r.total_tokens,
            "latency_ms": r.latency_ms,
            "cost_usd": round(float(r.cost or 0), 8),
            "created_at": r.created_at.isoformat() if r.created_at else "",
        }
        for r in records
    ]
