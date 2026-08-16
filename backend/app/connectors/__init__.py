from __future__ import annotations

from typing import Any

from app.connectors.base import BaseConnector, ChangeOperation, DiscoveredItem, DocumentEvent
from app.connectors.file_connector import FileConnector
from app.connectors.s3_connector import S3Connector
from app.connectors.github_connector import GitHubConnector
from app.connectors.postgres_connector import PostgresConnector
from app.connectors.rest_connector import RESTConnector

CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "file": FileConnector,
    "s3": S3Connector,
    "github": GitHubConnector,
    "postgresql": PostgresConnector,
    "rest_api": RESTConnector,
}


def get_connector(
    source_type: str,
    config: dict[str, Any],
    credentials: dict[str, Any] | None = None,
) -> BaseConnector:
    cls = CONNECTOR_REGISTRY.get(source_type)
    if not cls:
        raise ValueError(f"Unknown connector type: {source_type}. Options: {list(CONNECTOR_REGISTRY)}")
    return cls(config=config, credentials=credentials)


__all__ = [
    "BaseConnector",
    "ChangeOperation",
    "DiscoveredItem",
    "DocumentEvent",
    "FileConnector",
    "S3Connector",
    "GitHubConnector",
    "PostgresConnector",
    "RESTConnector",
    "get_connector",
    "CONNECTOR_REGISTRY",
]
