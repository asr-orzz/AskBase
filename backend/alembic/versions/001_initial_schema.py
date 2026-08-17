"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # KB status enum
    kb_status = postgresql.ENUM("active", "inactive", "indexing", "error", name="kb_status", create_type=False)
    kb_status.create(op.get_bind(), checkfirst=True)

    # Document status enum
    doc_status = postgresql.ENUM("pending", "processing", "indexed", "failed", name="document_status", create_type=False)
    doc_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", kb_status, nullable=False, server_default="active"),
        sa.Column("collection_name", sa.String(255), unique=True, nullable=False),
        sa.Column("document_count", sa.Integer, server_default="0"),
        sa.Column("chunk_count", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("file_size", sa.BigInteger, nullable=True),
        sa.Column("version", sa.Integer, server_default="1"),
        sa.Column("status", doc_status, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("chunk_count", sa.Integer, server_default="0"),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("vector_id", sa.String(100), nullable=True, index=True),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("knowledge_bases")
    op.execute("DROP TYPE IF EXISTS document_status")
    op.execute("DROP TYPE IF EXISTS kb_status")
