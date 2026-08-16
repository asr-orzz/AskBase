"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-16
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
    # --- Enums ---
    org_role = postgresql.ENUM("admin", "developer", "viewer", name="org_role", create_type=False)
    kb_status = postgresql.ENUM("active", "syncing", "error", "archived", name="kb_status", create_type=False)
    source_type = postgresql.ENUM("file", "s3", "github", "postgresql", "rest_api", "web", name="source_type", create_type=False)
    sync_status = postgresql.ENUM("idle", "running", "completed", "failed", name="sync_status", create_type=False)
    document_status = postgresql.ENUM("pending", "processing", "indexed", "failed", "deleted", name="document_status", create_type=False)
    chunking_strategy = postgresql.ENUM("fixed", "recursive", "semantic", "sentence", name="chunking_strategy", create_type=False)
    retrieval_mode = postgresql.ENUM("vector", "bm25", "hybrid", name="retrieval_mode", create_type=False)
    deployment_env = postgresql.ENUM("staging", "production", name="deployment_env", create_type=False)
    deployment_status = postgresql.ENUM("active", "inactive", "rolling_back", name="deployment_status", create_type=False)
    eval_status = postgresql.ENUM("pending", "running", "completed", "failed", name="eval_status", create_type=False)
    experiment_status = postgresql.ENUM("draft", "running", "completed", "cancelled", name="experiment_status", create_type=False)

    for enum in [org_role, kb_status, source_type, sync_status, document_status,
                 chunking_strategy, retrieval_mode, deployment_env, deployment_status,
                 eval_status, experiment_status]:
        enum.create(op.get_bind(), checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- organizations ---
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- organization_members ---
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", org_role, nullable=False, server_default="developer"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )

    # --- knowledge_bases ---
    op.create_table(
        "knowledge_bases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", kb_status, nullable=False, server_default="active"),
        sa.Column("document_count", sa.Integer(), default=0),
        sa.Column("chunk_count", sa.Integer(), default=0),
        sa.Column("collection_name", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- data_sources ---
    op.create_table(
        "data_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("credentials", postgresql.JSONB(), nullable=True),
        sa.Column("sync_status", sync_status, nullable=False, server_default="idle"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("document_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- documents ---
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("data_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_url", sa.String(2000), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False, index=True),
        sa.Column("storage_path", sa.String(1000), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("status", document_status, nullable=False, server_default="pending"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), default=0),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- chunks ---
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("token_count", sa.Integer(), default=0),
        sa.Column("embedding_model", sa.String(100), nullable=True),
        sa.Column("vector_id", sa.String(100), nullable=True, index=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- rag_configs ---
    op.create_table(
        "rag_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), default=1),
        sa.Column("is_active", sa.Boolean(), default=False),
        # Chunking
        sa.Column("chunking_strategy", chunking_strategy, nullable=False, server_default="recursive"),
        sa.Column("chunk_size", sa.Integer(), default=800),
        sa.Column("chunk_overlap", sa.Integer(), default=100),
        # Embedding
        sa.Column("embedding_provider", sa.String(50), server_default="openai"),
        sa.Column("embedding_model", sa.String(100), server_default="text-embedding-3-small"),
        sa.Column("embedding_dimensions", sa.Integer(), default=1536),
        # Retrieval
        sa.Column("retrieval_mode", retrieval_mode, nullable=False, server_default="hybrid"),
        sa.Column("top_k", sa.Integer(), default=10),
        sa.Column("similarity_threshold", sa.Float(), default=0.7),
        # Reranking
        sa.Column("reranker_enabled", sa.Boolean(), default=True),
        sa.Column("reranker_provider", sa.String(50), nullable=True),
        sa.Column("reranker_model", sa.String(100), nullable=True),
        sa.Column("reranker_top_k", sa.Integer(), default=5),
        # LLM
        sa.Column("llm_provider", sa.String(50), server_default="openai"),
        sa.Column("llm_model", sa.String(100), server_default="gpt-4o"),
        sa.Column("temperature", sa.Float(), default=0.1),
        sa.Column("max_tokens", sa.Integer(), default=2048),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        # Advanced
        sa.Column("query_rewrite_enabled", sa.Boolean(), default=False),
        sa.Column("context_compression_enabled", sa.Boolean(), default=False),
        sa.Column("extra_config", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- deployments ---
    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("rag_config_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("environment", deployment_env, nullable=False),
        sa.Column("status", deployment_status, nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("traffic_percentage", sa.Integer(), default=100),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- evaluation_datasets ---
    op.create_table(
        "evaluation_datasets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_count", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- evaluation_items ---
    op.create_table(
        "evaluation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=True),
        sa.Column("expected_contexts", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- evaluation_runs ---
    op.create_table(
        "evaluation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rag_config_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", eval_status, nullable=False, server_default="pending"),
        sa.Column("recall_at_k", sa.Float(), nullable=True),
        sa.Column("precision_at_k", sa.Float(), nullable=True),
        sa.Column("mrr", sa.Float(), nullable=True),
        sa.Column("ndcg", sa.Float(), nullable=True),
        sa.Column("faithfulness", sa.Float(), nullable=True),
        sa.Column("answer_relevance", sa.Float(), nullable=True),
        sa.Column("citation_accuracy", sa.Float(), nullable=True),
        sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        sa.Column("avg_cost", sa.Float(), nullable=True),
        sa.Column("total_items", sa.Integer(), default=0),
        sa.Column("completed_items", sa.Integer(), default=0),
        sa.Column("detailed_results", postgresql.JSONB(), server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- experiments ---
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", experiment_status, nullable=False, server_default="draft"),
        sa.Column("variant_a_config_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_b_config_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_configs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_a_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("variant_b_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("winner", sa.String(1), nullable=True),
        sa.Column("results", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- api_keys ---
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- usage_records ---
    op.create_table(
        "usage_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("knowledge_base_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False, index=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("input_tokens", sa.Integer(), default=0),
        sa.Column("output_tokens", sa.Integer(), default=0),
        sa.Column("embedding_tokens", sa.Integer(), default=0),
        sa.Column("total_tokens", sa.Integer(), default=0),
        sa.Column("latency_ms", sa.Float(), default=0.0),
        sa.Column("cost_usd", sa.Float(), default=0.0),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("usage_records")
    op.drop_table("api_keys")
    op.drop_table("experiments")
    op.drop_table("evaluation_runs")
    op.drop_table("evaluation_items")
    op.drop_table("evaluation_datasets")
    op.drop_table("deployments")
    op.drop_table("rag_configs")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("data_sources")
    op.drop_table("knowledge_bases")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    op.drop_table("users")

    for enum_name in [
        "experiment_status", "eval_status", "deployment_status", "deployment_env",
        "retrieval_mode", "chunking_strategy", "document_status", "sync_status",
        "source_type", "kb_status", "org_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
