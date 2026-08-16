from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ragops",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=600,
    task_time_limit=900,
    task_routes={
        "app.workers.tasks.sync_data_source": {"queue": "sync"},
        "app.workers.tasks.ingest_document": {"queue": "ingest"},
        "app.workers.tasks.reindex_knowledge_base": {"queue": "ingest"},
        "app.workers.tasks.run_evaluation": {"queue": "eval"},
    },
    task_default_queue="default",
)

celery_app.autodiscover_tasks(["app.workers"])
