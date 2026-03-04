"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "memories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("namespace", sa.String(length=100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memories_tenant_namespace", "memories", ["tenant_id", "namespace"])


def downgrade() -> None:
    op.drop_index("ix_memories_tenant_namespace", table_name="memories")
    op.drop_table("memories")
