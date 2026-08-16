from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import structlog
from confluent_kafka import Producer

from app.core.config import get_settings

logger = structlog.get_logger()


class EventTopics:
    DOCUMENT_CREATED = "ragops.document.created"
    DOCUMENT_UPDATED = "ragops.document.updated"
    DOCUMENT_DELETED = "ragops.document.deleted"
    SYNC_STARTED = "ragops.sync.started"
    SYNC_COMPLETED = "ragops.sync.completed"
    SYNC_FAILED = "ragops.sync.failed"
    EMBEDDING_REQUESTED = "ragops.embedding.requested"
    EMBEDDING_COMPLETED = "ragops.embedding.completed"
    INDEX_UPDATED = "ragops.index.updated"
    QUERY_EXECUTED = "ragops.query.executed"


class KafkaProducer:
    """Produces events to Kafka topics."""

    def __init__(self) -> None:
        settings = get_settings()
        self._producer = Producer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "client.id": "ragops-api",
            "acks": "all",
            "retries": 3,
            "retry.backoff.ms": 500,
            "linger.ms": 10,
            "batch.num.messages": 100,
        })

    def _delivery_callback(self, err: Any, msg: Any) -> None:
        if err:
            logger.error("Kafka delivery failed", error=str(err), topic=msg.topic())
        else:
            logger.debug("Kafka delivered", topic=msg.topic(), partition=msg.partition())

    def produce(self, topic: str, key: str, value: dict[str, Any]) -> None:
        value["_timestamp"] = datetime.utcnow().isoformat()
        self._producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=json.dumps(value, default=str).encode("utf-8"),
            callback=self._delivery_callback,
        )
        self._producer.poll(0)

    def flush(self, timeout: float = 5.0) -> None:
        self._producer.flush(timeout)

    def emit_document_created(
        self, tenant_id: str, kb_id: str, doc_id: str, title: str, **extra: Any
    ) -> None:
        self.produce(
            EventTopics.DOCUMENT_CREATED,
            key=doc_id,
            value={"tenant_id": tenant_id, "knowledge_base_id": kb_id, "document_id": doc_id, "title": title, **extra},
        )

    def emit_document_updated(
        self, tenant_id: str, kb_id: str, doc_id: str, title: str, **extra: Any
    ) -> None:
        self.produce(
            EventTopics.DOCUMENT_UPDATED,
            key=doc_id,
            value={"tenant_id": tenant_id, "knowledge_base_id": kb_id, "document_id": doc_id, "title": title, **extra},
        )

    def emit_document_deleted(self, tenant_id: str, kb_id: str, doc_id: str) -> None:
        self.produce(
            EventTopics.DOCUMENT_DELETED,
            key=doc_id,
            value={"tenant_id": tenant_id, "knowledge_base_id": kb_id, "document_id": doc_id},
        )

    def emit_sync_started(self, tenant_id: str, kb_id: str, ds_id: str) -> None:
        self.produce(
            EventTopics.SYNC_STARTED,
            key=ds_id,
            value={"tenant_id": tenant_id, "knowledge_base_id": kb_id, "data_source_id": ds_id},
        )

    def emit_sync_completed(self, tenant_id: str, kb_id: str, ds_id: str, doc_count: int) -> None:
        self.produce(
            EventTopics.SYNC_COMPLETED,
            key=ds_id,
            value={"tenant_id": tenant_id, "knowledge_base_id": kb_id, "data_source_id": ds_id, "document_count": doc_count},
        )

    def emit_query_executed(
        self, tenant_id: str, kb_id: str, latency_ms: float, tokens: int, model: str
    ) -> None:
        self.produce(
            EventTopics.QUERY_EXECUTED,
            key=kb_id,
            value={
                "tenant_id": tenant_id,
                "knowledge_base_id": kb_id,
                "latency_ms": latency_ms,
                "total_tokens": tokens,
                "model": model,
            },
        )


_producer: KafkaProducer | None = None


def get_kafka_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        _producer = KafkaProducer()
    return _producer
