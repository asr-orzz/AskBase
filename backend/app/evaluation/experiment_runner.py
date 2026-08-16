from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.runner import EvaluationRunner
from app.models.evaluation import EvaluationRun, EvalStatus
from app.models.experiment import Experiment, ExperimentStatus

logger = structlog.get_logger()

METRIC_WEIGHTS = {
    "recall_at_k": 0.15,
    "precision_at_k": 0.10,
    "mrr": 0.10,
    "ndcg": 0.10,
    "faithfulness": 0.25,
    "answer_relevance": 0.20,
    "avg_latency_ms": -0.10,
}


def _compute_composite_score(run: EvaluationRun) -> float:
    """Weighted composite score — higher is better. Latency is inverted."""
    score = 0.0
    for metric, weight in METRIC_WEIGHTS.items():
        val = getattr(run, metric, None)
        if val is None:
            continue
        if metric == "avg_latency_ms":
            # Normalise: 100ms → 1.0, 1000ms → 0.1 (lower latency = higher score)
            normalised = min(1.0, 100.0 / max(val, 1.0))
            score += abs(weight) * normalised
        else:
            score += weight * val
    return round(score, 4)


class ExperimentRunner:
    """
    Runs an A/B experiment:
    1. Creates two EvaluationRuns (variant A and B) against the same dataset.
    2. Runs both through the EvaluationRunner.
    3. Compares aggregate metrics and picks a winner.
    """

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def run(self, experiment_id: uuid.UUID) -> Experiment:
        experiment = (await self.db.execute(
            select(Experiment).where(Experiment.id == experiment_id)
        )).scalar_one_or_none()
        if not experiment:
            raise ValueError("Experiment not found")

        experiment.status = ExperimentStatus.RUNNING
        await self.db.flush()

        # Create eval runs for both variants
        run_a = EvaluationRun(
            tenant_id=self.tenant_id,
            dataset_id=experiment.dataset_id,
            rag_config_id=experiment.variant_a_config_id,
            status=EvalStatus.PENDING,
        )
        run_b = EvaluationRun(
            tenant_id=self.tenant_id,
            dataset_id=experiment.dataset_id,
            rag_config_id=experiment.variant_b_config_id,
            status=EvalStatus.PENDING,
        )
        self.db.add(run_a)
        self.db.add(run_b)
        await self.db.flush()

        experiment.variant_a_run_id = run_a.id
        experiment.variant_b_run_id = run_b.id
        await self.db.flush()

        eval_runner = EvaluationRunner(self.db, self.tenant_id)

        try:
            await logger.ainfo("Running variant A", experiment_id=str(experiment_id))
            run_a = await eval_runner.run(run_a.id)

            await logger.ainfo("Running variant B", experiment_id=str(experiment_id))
            run_b = await eval_runner.run(run_b.id)

            score_a = _compute_composite_score(run_a)
            score_b = _compute_composite_score(run_b)

            comparison: dict[str, Any] = {
                "variant_a": {
                    "run_id": str(run_a.id),
                    "config_id": str(experiment.variant_a_config_id),
                    "composite_score": score_a,
                    "recall_at_k": run_a.recall_at_k,
                    "precision_at_k": run_a.precision_at_k,
                    "mrr": run_a.mrr,
                    "ndcg": run_a.ndcg,
                    "faithfulness": run_a.faithfulness,
                    "answer_relevance": run_a.answer_relevance,
                    "avg_latency_ms": run_a.avg_latency_ms,
                },
                "variant_b": {
                    "run_id": str(run_b.id),
                    "config_id": str(experiment.variant_b_config_id),
                    "composite_score": score_b,
                    "recall_at_k": run_b.recall_at_k,
                    "precision_at_k": run_b.precision_at_k,
                    "mrr": run_b.mrr,
                    "ndcg": run_b.ndcg,
                    "faithfulness": run_b.faithfulness,
                    "answer_relevance": run_b.answer_relevance,
                    "avg_latency_ms": run_b.avg_latency_ms,
                },
                "score_diff": round(score_a - score_b, 4),
                "metric_weights": METRIC_WEIGHTS,
            }

            if score_a > score_b:
                experiment.winner = "A"
            elif score_b > score_a:
                experiment.winner = "B"
            else:
                experiment.winner = None

            experiment.results = comparison
            experiment.status = ExperimentStatus.COMPLETED
            await self.db.flush()

            await logger.ainfo(
                "Experiment complete",
                experiment_id=str(experiment_id),
                winner=experiment.winner,
                score_a=score_a,
                score_b=score_b,
            )

        except Exception as e:
            experiment.status = ExperimentStatus.CANCELLED
            experiment.results = {"error": str(e)[:500]}
            await self.db.flush()
            raise

        return experiment
