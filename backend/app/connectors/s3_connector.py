from __future__ import annotations

import mimetypes
from datetime import datetime
from typing import Any

import structlog
import xxhash

from app.connectors.base import (
    BaseConnector,
    ChangeOperation,
    DiscoveredItem,
    DocumentEvent,
)
from app.core.config import get_settings

logger = structlog.get_logger()

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm", ".docx", ".csv", ".json"}


class S3Connector(BaseConnector):
    """Connector for S3-compatible storage (AWS S3, MinIO).

    Config:
        bucket: str — bucket name
        prefix: str — key prefix to scan (default: "")
        extensions: list[str] | None — file extensions to include
        endpoint_url: str | None — custom endpoint (MinIO)

    Credentials:
        access_key: str
        secret_key: str
    """

    def __init__(self, config: dict[str, Any], credentials: dict[str, Any] | None = None):
        super().__init__(config, credentials)
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import boto3

            settings = get_settings()
            self._client = boto3.client(
                "s3",
                endpoint_url=self.config.get("endpoint_url", settings.s3_endpoint_url),
                aws_access_key_id=self.credentials.get("access_key", settings.s3_access_key),
                aws_secret_access_key=self.credentials.get("secret_key", settings.s3_secret_key),
                region_name=self.config.get("region", settings.s3_region),
            )
        return self._client

    @property
    def source_type(self) -> str:
        return "s3"

    async def validate(self) -> bool:
        try:
            client = self._get_client()
            bucket = self.config.get("bucket", get_settings().s3_bucket_name)
            client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            return False

    async def discover(self) -> list[DiscoveredItem]:
        client = self._get_client()
        bucket = self.config.get("bucket", get_settings().s3_bucket_name)
        prefix = self.config.get("prefix", "")
        extensions = set(self.config.get("extensions", SUPPORTED_EXTENSIONS))

        items: list[DiscoveredItem] = []
        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                ext = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""

                if ext not in extensions:
                    continue
                if key.endswith("/"):
                    continue

                mime_type, _ = mimetypes.guess_type(key)
                filename = key.rsplit("/", 1)[-1] if "/" in key else key

                items.append(
                    DiscoveredItem(
                        identifier=key,
                        title=filename,
                        location=f"s3://{bucket}/{key}",
                        mime_type=mime_type,
                        file_size=obj.get("Size"),
                        last_modified=obj.get("LastModified"),
                        metadata={"bucket": bucket, "key": key, "etag": obj.get("ETag", "")},
                    )
                )

        await logger.ainfo("S3 discovery complete", bucket=bucket, prefix=prefix, items=len(items))
        return items

    async def fetch(self, item: DiscoveredItem) -> bytes:
        client = self._get_client()
        bucket = item.metadata.get("bucket", self.config.get("bucket"))
        key = item.metadata.get("key", item.identifier)

        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    async def get_changes(self, since: datetime | None = None) -> list[DocumentEvent]:
        items = await self.discover()
        events: list[DocumentEvent] = []

        for item in items:
            if since and item.last_modified and item.last_modified.replace(tzinfo=None) <= since:
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
