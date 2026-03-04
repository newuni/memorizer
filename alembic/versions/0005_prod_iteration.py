"""production readiness iteration

Revision ID: 0005_prod_iteration
Revises: 0004_documents_connectors
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_prod_iteration"
down_revision = "0004_documents_connectors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="120"))
    op.add_column("api_keys", sa.Column("daily_quota", sa.Integer(), nullable=False, server_default="5000"))

    op.add_column("memories", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("memories", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("memories", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("memories", sa.Column("pii_redacted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index("ix_memories_is_deleted", "memories", ["is_deleted"])
    op.create_index("ix_memories_expires_at", "memories", ["expires_at"])

    op.add_column("documents", sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("documents", sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("documents", sa.Column("content_hash", sa.String(length=128), nullable=True))
    op.add_column("documents", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("documents", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])
    op.create_index("ix_documents_is_deleted", "documents", ["is_deleted"])

    op.add_column("connectors", sa.Column("last_cursor", sa.Text(), nullable=True))
    op.add_column("connectors", sa.Column("recrawl_minutes", sa.Integer(), nullable=False, server_default="1440"))

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("key_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=40), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_key_id", "audit_logs", ["key_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_key_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_column("connectors", "recrawl_minutes")
    op.drop_column("connectors", "last_cursor")

    op.drop_index("ix_documents_is_deleted", table_name="documents")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_column("documents", "deleted_at")
    op.drop_column("documents", "is_deleted")
    op.drop_column("documents", "content_hash")
    op.drop_column("documents", "max_retries")
    op.drop_column("documents", "attempts")

    op.drop_index("ix_memories_expires_at", table_name="memories")
    op.drop_index("ix_memories_is_deleted", table_name="memories")
    op.drop_column("memories", "pii_redacted")
    op.drop_column("memories", "deleted_at")
    op.drop_column("memories", "expires_at")
    op.drop_column("memories", "is_deleted")

    op.drop_column("api_keys", "daily_quota")
    op.drop_column("api_keys", "rate_limit_per_minute")
