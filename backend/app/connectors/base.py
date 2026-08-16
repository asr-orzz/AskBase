from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class ChangeOperation(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


@dataclass
class DocumentEvent:
    """Unified event emitted by every connector."""

    document_id: str
    source_id: str
    tenant_id: str
    operation: ChangeOperation
    title: str
    content_location: str  # path, URL, or S3 key
    content_hash: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiscoveredItem:
    """Item found during connector discovery."""

    identifier: str
    title: str
    location: str
    mime_type: str | None = None
    file_size: int | None = None
    last_modified: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """Abstract connector interface — every data source implements this."""

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any] | None = None):
        self.config = config
        self.credentials = credentials or {}

    @property
    @abstractmethod
    def source_type(self) -> str: ...

    @abstractmethod
    async def validate(self) -> bool:
        """Test the connection / credentials. Returns True if valid."""
        ...

    @abstractmethod
    async def discover(self) -> list[DiscoveredItem]:
        """List all available items from the source."""
        ...

    @abstractmethod
    async def fetch(self, item: DiscoveredItem) -> bytes:
        """Download the raw content for a single item."""
        ...

    @abstractmethod
    async def get_changes(self, since: datetime | None = None) -> list[DocumentEvent]:
        """Return change events since the given timestamp (for incremental sync)."""
        ...
