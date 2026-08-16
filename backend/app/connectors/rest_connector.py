from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import httpx
import structlog
import xxhash

from app.connectors.base import (
    BaseConnector,
    ChangeOperation,
    DiscoveredItem,
    DocumentEvent,
)

logger = structlog.get_logger()


class RESTConnector(BaseConnector):
    """Connector for REST APIs that return JSON documents.

    Config:
        base_url: str — API base URL
        list_endpoint: str — endpoint that returns a list of items (default: "/")
        detail_endpoint: str — endpoint template for item detail, use {id} placeholder
        id_field: str — field in list response for item ID (default: "id")
        title_field: str — field for document title (default: "title")
        content_field: str — field containing text content (default: "content")
        items_path: str — JSON path to items array in list response (default: "" = root)
        headers: dict — additional request headers
        params: dict — query parameters for list endpoint

    Credentials:
        api_key: str — added as Authorization: Bearer header
        headers: dict — additional auth headers
    """

    @property
    def source_type(self) -> str:
        return "rest_api"

    def _get_headers(self) -> dict[str, str]:
        headers: dict[str, str] = self.config.get("headers", {})
        api_key = self.credentials.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        auth_headers = self.credentials.get("headers", {})
        headers.update(auth_headers)
        return headers

    async def validate(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = self.config["base_url"].rstrip("/")
                resp = await client.get(url, headers=self._get_headers())
                return resp.status_code < 500
        except Exception:
            return False

    async def discover(self) -> list[DiscoveredItem]:
        base_url = self.config["base_url"].rstrip("/")
        list_endpoint = self.config.get("list_endpoint", "/")
        id_field = self.config.get("id_field", "id")
        title_field = self.config.get("title_field", "title")
        items_path = self.config.get("items_path", "")
        params = self.config.get("params", {})

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{base_url}{list_endpoint}",
                headers=self._get_headers(),
                params=params,
            )
            resp.raise_for_status()
            data = resp.json()

        if items_path:
            for key in items_path.split("."):
                data = data[key]

        if not isinstance(data, list):
            data = [data]

        items: list[DiscoveredItem] = []
        for record in data:
            item_id = str(record.get(id_field, ""))
            title = str(record.get(title_field, item_id))

            items.append(
                DiscoveredItem(
                    identifier=item_id,
                    title=title,
                    location=f"{base_url}/{item_id}",
                    mime_type="application/json",
                    metadata={"source_record": record},
                )
            )

        await logger.ainfo("REST discovery complete", base_url=base_url, items=len(items))
        return items

    async def fetch(self, item: DiscoveredItem) -> bytes:
        base_url = self.config["base_url"].rstrip("/")
        detail_endpoint = self.config.get("detail_endpoint", "/{id}")
        content_field = self.config.get("content_field", "content")

        url = f"{base_url}{detail_endpoint}".replace("{id}", item.identifier)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, headers=self._get_headers())
            resp.raise_for_status()
            data = resp.json()

        if content_field and content_field in data:
            content = str(data[content_field])
        else:
            content = json.dumps(data, indent=2, default=str)

        return content.encode("utf-8")

    async def get_changes(self, since: datetime | None = None) -> list[DocumentEvent]:
        items = await self.discover()
        events: list[DocumentEvent] = []

        for item in items:
            content = await self.fetch(item)
            events.append(
                DocumentEvent(
                    document_id=item.identifier,
                    source_id=self.config.get("source_id", ""),
                    tenant_id=self.config.get("tenant_id", ""),
                    operation=ChangeOperation.CREATED,
                    title=item.title,
                    content_location=item.location,
                    content_hash=xxhash.xxh64(content).hexdigest(),
                    file_size=len(content),
                    mime_type="application/json",
                    metadata=item.metadata,
                )
            )

        return events
