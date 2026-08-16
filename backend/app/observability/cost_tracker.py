from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import UsageRecord
from app.observability.metrics import COST_TOTAL, TOKEN_USAGE

logger = structlog.get_logger()

# Pricing per 1M tokens (USD) — update as providers change prices
PRICING: dict[str, dict[str, dict[str, float]]] = {
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "text-embedding-3-small": {"input": 0.02, "output": 0.0},
        "text-embedding-3-large": {"input": 0.13, "output": 0.0},
        "text-embedding-ada-002": {"input": 0.10, "output": 0.0},
    },
    "anthropic": {
        "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    },
    "google": {
        "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
        "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    },
    "cohere": {
        "rerank-english-v3.0": {"input": 2.00, "output": 0.0},
        "embed-english-v3.0": {"input": 0.10, "output": 0.0},
    },
}


@dataclass
class CostEstimate:
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    provider: str
    model: str


def estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int = 0,
) -> CostEstimate:
    """Estimate cost based on provider pricing tables."""
    provider_prices = PRICING.get(provider, {})

    prices = provider_prices.get(model)
    if not prices:
        for key in provider_prices:
            if key in model or model in key:
                prices = provider_prices[key]
                break

    if not prices:
        prices = {"input": 0.0, "output": 0.0}

    input_cost = (input_tokens / 1_000_000) * prices["input"]
    output_cost = (output_tokens / 1_000_000) * prices["output"]

    return CostEstimate(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost=round(input_cost, 8),
        output_cost=round(output_cost, 8),
        total_cost=round(input_cost + output_cost, 8),
        provider=provider,
        model=model,
    )


async def record_usage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    knowledge_base_id: uuid.UUID | None,
    operation: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int = 0,
    latency_ms: float = 0.0,
    api_key_id: uuid.UUID | None = None,
) -> UsageRecord:
    """Record a usage event with cost estimation."""
    cost = estimate_cost(provider, model, input_tokens, output_tokens)

    record = UsageRecord(
        tenant_id=tenant_id,
        knowledge_base_id=knowledge_base_id,
        operation=operation,
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        latency_ms=latency_ms,
        cost=cost.total_cost,
        api_key_id=api_key_id,
    )
    db.add(record)

    # Update Prometheus counters
    TOKEN_USAGE.labels(provider=provider, model=model, direction="input").inc(input_tokens)
    TOKEN_USAGE.labels(provider=provider, model=model, direction="output").inc(output_tokens)
    COST_TOTAL.labels(provider=provider, model=model, operation=operation).inc(cost.total_cost)

    return record


async def get_cost_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    days: int = 30,
) -> dict[str, Any]:
    """Aggregate cost summary for a tenant over the last N days."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Total cost
    total = (await db.execute(
        select(func.coalesce(func.sum(UsageRecord.cost), 0.0)).where(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.created_at >= cutoff,
        )
    )).scalar()

    # By provider
    by_provider = (await db.execute(
        select(
            UsageRecord.provider,
            func.sum(UsageRecord.cost).label("cost"),
            func.sum(UsageRecord.total_tokens).label("tokens"),
            func.count().label("requests"),
        )
        .where(UsageRecord.tenant_id == tenant_id, UsageRecord.created_at >= cutoff)
        .group_by(UsageRecord.provider)
    )).all()

    # By operation
    by_operation = (await db.execute(
        select(
            UsageRecord.operation,
            func.sum(UsageRecord.cost).label("cost"),
            func.count().label("requests"),
        )
        .where(UsageRecord.tenant_id == tenant_id, UsageRecord.created_at >= cutoff)
        .group_by(UsageRecord.operation)
    )).all()

    # Daily breakdown
    daily = (await db.execute(
        select(
            func.date_trunc("day", UsageRecord.created_at).label("day"),
            func.sum(UsageRecord.cost).label("cost"),
            func.sum(UsageRecord.total_tokens).label("tokens"),
            func.count().label("requests"),
        )
        .where(UsageRecord.tenant_id == tenant_id, UsageRecord.created_at >= cutoff)
        .group_by(func.date_trunc("day", UsageRecord.created_at))
        .order_by(func.date_trunc("day", UsageRecord.created_at))
    )).all()

    return {
        "total_cost_usd": round(float(total or 0), 6),
        "period_days": days,
        "by_provider": [
            {
                "provider": row.provider,
                "cost_usd": round(float(row.cost or 0), 6),
                "tokens": int(row.tokens or 0),
                "requests": row.requests,
            }
            for row in by_provider
        ],
        "by_operation": [
            {
                "operation": row.operation,
                "cost_usd": round(float(row.cost or 0), 6),
                "requests": row.requests,
            }
            for row in by_operation
        ],
        "daily": [
            {
                "date": row.day.isoformat() if row.day else "",
                "cost_usd": round(float(row.cost or 0), 6),
                "tokens": int(row.tokens or 0),
                "requests": row.requests,
            }
            for row in daily
        ],
    }
