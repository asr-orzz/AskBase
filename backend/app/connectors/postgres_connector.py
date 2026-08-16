from __future__ import annotations

import json
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

logger = structlog.get_logger()


class PostgresConnector(BaseConnector):
    """Connector for PostgreSQL tables/views.

    Config:
        connection_string: str — postgres://user:pass@host:port/db
        table: str — table or view name
        content_column: str — column containing text content
        title_column: str | None — column for document title
        id_column: str — primary key column (default: "id")
        updated_at_column: str | None — column for change detection
        extra_columns: list[str] — additional columns to include as metadata

    Credentials:
        connection_string: str — alternative to config
    """

    @property
    def source_type(self) -> str:
        return "postgresql"

    def _get_conn_string(self) -> str:
        return (
            self.credentials.get("connection_string")
            or self.config.get("connection_string", "")
        )

    async def validate(self) -> bool:
        try:
            import psycopg2

            conn = psycopg2.connect(self._get_conn_string())
            conn.close()
            return True
        except Exception:
            return False

    async def discover(self) -> list[DiscoveredItem]:
        import psycopg2
        import psycopg2.extras

        table = self.config["table"]
        id_col = self.config.get("id_column", "id")
        title_col = self.config.get("title_column", id_col)
        content_col = self.config.get("content_column", "content")

        conn = psycopg2.connect(self._get_conn_string())
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"SELECT {id_col}, {title_col} FROM {table} ORDER BY {id_col}"  # noqa: S608
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        items: list[DiscoveredItem] = []
        for row in rows:
            row_id = str(row[id_col])
            title = str(row.get(title_col, row_id))
            items.append(
                DiscoveredItem(
                    identifier=row_id,
                    title=title,
                    location=f"pg://{table}/{row_id}",
                    mime_type="text/plain",
                    metadata={"table": table, "id_column": id_col},
                )
            )

        await logger.ainfo("Postgres discovery complete", table=table, items=len(items))
        return items

    async def fetch(self, item: DiscoveredItem) -> bytes:
        import psycopg2
        import psycopg2.extras

        table = self.config["table"]
        id_col = self.config.get("id_column", "id")
        content_col = self.config.get("content_column", "content")
        extra_cols = self.config.get("extra_columns", [])

        columns = [content_col] + extra_cols
        col_str = ", ".join(columns)

        conn = psycopg2.connect(self._get_conn_string())
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    f"SELECT {col_str} FROM {table} WHERE {id_col} = %s",  # noqa: S608
                    (item.identifier,),
                )
                row = cur.fetchone()
        finally:
            conn.close()

        if not row:
            return b""

        if extra_cols:
            parts = [str(row[content_col])]
            for col in extra_cols:
                if row.get(col):
                    parts.append(f"\n\n{col}: {row[col]}")
            return "\n".join(parts).encode("utf-8")

        return str(row[content_col]).encode("utf-8")

    async def get_changes(self, since: datetime | None = None) -> list[DocumentEvent]:
        import psycopg2
        import psycopg2.extras

        table = self.config["table"]
        id_col = self.config.get("id_column", "id")
        content_col = self.config.get("content_column", "content")
        updated_col = self.config.get("updated_at_column")

        conn = psycopg2.connect(self._get_conn_string())
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if since and updated_col:
                    cur.execute(
                        f"SELECT {id_col}, {content_col} FROM {table} WHERE {updated_col} > %s",  # noqa: S608
                        (since,),
                    )
                else:
                    cur.execute(f"SELECT {id_col}, {content_col} FROM {table}")  # noqa: S608
                rows = cur.fetchall()
        finally:
            conn.close()

        events: list[DocumentEvent] = []
        for row in rows:
            content = str(row[content_col]).encode("utf-8")
            events.append(
                DocumentEvent(
                    document_id=str(row[id_col]),
                    source_id=self.config.get("source_id", ""),
                    tenant_id=self.config.get("tenant_id", ""),
                    operation=ChangeOperation.UPDATED if since else ChangeOperation.CREATED,
                    title=str(row[id_col]),
                    content_location=f"pg://{table}/{row[id_col]}",
                    content_hash=xxhash.xxh64(content).hexdigest(),
                    file_size=len(content),
                    mime_type="text/plain",
                )
            )

        return events
