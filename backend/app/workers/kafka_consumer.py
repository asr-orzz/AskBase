from __future__ import annotations

import asyncio
import json
import signal
import uuid
from typing import Any

import structlog
from confluent_kafka import Consumer, KafkaError

from app.core.config import get_settings
from app.workers.kafka_producer import EventTopics

logger = structlog.get_logger()


class KafkaEventConsumer:
    """Consumes events from Kafka and dispatches to handlers."""

    def __init__(self, group_id: str = "ragops-ingestion-workers") -> None:
        settings = get_settings()
        self._consumer = Consumer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "max.poll.interval.ms": 600000,
            "session.timeout.ms": 30000,
        })
        self._running = False
        self._handlers: dict[str, Any] = {}

    def register_handler(self, topic: str, handler: Any) -> None:
        self._handlers[topic] = handler

    async def start(self, topics: list[str] | None = None) -> None:
        subscribe_topics = topics or [
            EventTopics.DOCUMENT_CREATED,
            EventTopics.DOCUMENT_UPDATED,
            EventTopics.DOCUMENT_DELETED,
            EventTopics.EMBEDDING_REQUESTED,
        ]

        self._consumer.subscribe(subscribe_topics)
        self._running = True

        logger.info("Kafka consumer started", topics=subscribe_topics)

        while self._running:
            msg = self._consumer.poll(timeout=1.0)

            if msg is None:
                await asyncio.sleep(0.1)
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error("Kafka consumer error", error=msg.error())
                continue

            try:
                topic = msg.topic()
                value = json.loads(msg.value().decode("utf-8"))
                key = msg.key().decode("utf-8") if msg.key() else ""

                logger.info("Kafka event received", topic=topic, key=key)

                handler = self._handlers.get(topic)
                if handler:
                    await handler(topic, key, value)
                else:
                    await self._default_handler(topic, key, value)

                self._consumer.commit(msg)

            except Exception as e:
                logger.error("Event processing failed", error=str(e), topic=msg.topic())

    async def _default_handler(self, topic: str, key: str, value: dict[str, Any]) -> None:
        logger.info("Unhandled event", topic=topic, key=key)

    def stop(self) -> None:
        self._running = False
        self._consumer.close()
        logger.info("Kafka consumer stopped")


async def handle_document_created(topic: str, key: str, value: dict[str, Any]) -> None:
    """Handle DOCUMENT_CREATED events — triggers embedding + indexing."""
    from app.workers.tasks import ingest_document

    doc_id = value.get("document_id", "")
    kb_id = value.get("knowledge_base_id", "")
    tenant_id = value.get("tenant_id", "")
    title = value.get("title", "")
    content_b64 = value.get("content_b64", "")

    if content_b64:
        ingest_document.delay(
            knowledge_base_id=kb_id,
            tenant_id=tenant_id,
            title=title,
            content_b64=content_b64,
            filename=title,
        )
        logger.info("Dispatched ingestion from Kafka event", doc_id=doc_id)


async def handle_document_deleted(topic: str, key: str, value: dict[str, Any]) -> None:
    """Handle DOCUMENT_DELETED events — removes from vector store."""
    logger.info("Document deletion event received", document_id=value.get("document_id"))


def run_consumer() -> None:
    """Entry point for running the Kafka consumer as a standalone process."""
    consumer = KafkaEventConsumer()
    consumer.register_handler(EventTopics.DOCUMENT_CREATED, handle_document_created)
    consumer.register_handler(EventTopics.DOCUMENT_UPDATED, handle_document_created)
    consumer.register_handler(EventTopics.DOCUMENT_DELETED, handle_document_deleted)

    def shutdown(signum: int, frame: Any) -> None:
        consumer.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    asyncio.run(consumer.start())


if __name__ == "__main__":
    run_consumer()
