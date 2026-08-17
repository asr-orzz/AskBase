"""add api key columns to users

Revision ID: 003
Revises: 002
Create Date: 2026-08-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("custom_api_key", sa.String(500), nullable=True))
    op.add_column("users", sa.Column("use_custom_key", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("users", "use_custom_key")
    op.drop_column("users", "custom_api_key")
