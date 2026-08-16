from __future__ import annotations

import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
import xxhash

from app.connectors.base import (
    BaseConnector,
    ChangeOperation,
    DiscoveredItem,
    DocumentEvent,
)

logger = structlog.get_logger()

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm", ".docx", ".csv", ".json"}


class FileConnector(BaseConnector):
    """Connector for local filesystem directories.

    Config:
        path: str — directory path to scan
        extensions: list[str] | None — file extensions to include (default: all supported)
        recursive: bool — scan subdirectories (default: True)
    """

    @property
    def source_type(self) -> str:
        return "file"

    async def validate(self) -> bool:
        path = Path(self.config.get("path", ""))
        return path.exists() and path.is_dir()

    async def discover(self) -> list[DiscoveredItem]:
        root = Path(self.config["path"])
        extensions = set(self.config.get("extensions", SUPPORTED_EXTENSIONS))
        recursive = self.config.get("recursive", True)

        pattern = "**/*" if recursive else "*"
        items: list[DiscoveredItem] = []

        for filepath in root.glob(pattern):
            if not filepath.is_file():
                continue
            if filepath.suffix.lower() not in extensions:
                continue

            stat = filepath.stat()
            mime_type, _ = mimetypes.guess_type(str(filepath))

            items.append(
                DiscoveredItem(
                    identifier=str(filepath.relative_to(root)),
                    title=filepath.name,
                    location=str(filepath),
                    mime_type=mime_type,
                    file_size=stat.st_size,
                    last_modified=datetime.fromtimestamp(stat.st_mtime),
                    metadata={"relative_path": str(filepath.relative_to(root))},
                )
            )

        await logger.ainfo("File discovery complete", path=str(root), items=len(items))
        return items

    async def fetch(self, item: DiscoveredItem) -> bytes:
        return Path(item.location).read_bytes()

    async def get_changes(self, since: datetime | None = None) -> list[DocumentEvent]:
        items = await self.discover()
        events: list[DocumentEvent] = []

        for item in items:
            if since and item.last_modified and item.last_modified <= since:
                continue

            content = await self.fetch(item)
            content_hash = xxhash.xxh64(content).hexdigest()

            events.append(
                DocumentEvent(
                    document_id=item.identifier,
                    source_id=self.config.get("source_id", ""),
                    tenant_id=self.config.get("tenant_id", ""),
                    operation=ChangeOperation.UPDATED if since else ChangeOperation.CREATED,
                    title=item.title,
                    content_location=item.location,
                    content_hash=content_hash,
                    mime_type=item.mime_type,
                    file_size=item.file_size,
                    metadata=item.metadata,
                )
            )

        return events
