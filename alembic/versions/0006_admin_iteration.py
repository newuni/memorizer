"""admin backend iteration

Revision ID: 0006_admin_iteration
Revises: 0005_prod_iteration
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_admin_iteration"
down_revision = "0005_prod_iteration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("daily_quota", sa.Integer(), nullable=False, server_default="5000"),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("purge_after_forget_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_index("ix_tenants_tenant_id", "tenants", ["tenant_id"])
    op.create_index("ix_tenants_status", "tenants", ["status"])

    op.create_table(
        "tenant_namespaces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("daily_quota", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_tenant_namespace"),
    )
    op.create_index("ix_tenant_namespaces_tenant_id", "tenant_namespaces", ["tenant_id"])
    op.create_index("ix_tenant_namespaces_name", "tenant_namespaces", ["name"])
    op.create_index("ix_tenant_namespaces_is_active", "tenant_namespaces", ["is_active"])

    op.create_table(
        "admin_tokens",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False, server_default="admin"),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_tokens_token_hash", "admin_tokens", ["token_hash"], unique=True)
    op.create_index("ix_admin_tokens_role", "admin_tokens", ["role"])
    op.create_index("ix_admin_tokens_tenant_id", "admin_tokens", ["tenant_id"])

    op.create_table(
        "governance_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="done"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("hard_delete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_governance_tasks_tenant_id", "governance_tasks", ["tenant_id"])
    op.create_index("ix_governance_tasks_action", "governance_tasks", ["action"])
    op.create_index("ix_governance_tasks_status", "governance_tasks", ["status"])

    op.create_table(
        "event_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_logs_tenant_id", "event_logs", ["tenant_id"])
    op.create_index("ix_event_logs_event_type", "event_logs", ["event_type"])
    op.create_index("ix_event_logs_severity", "event_logs", ["severity"])
    op.create_index("ix_event_logs_created_at", "event_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_event_logs_created_at", table_name="event_logs")
    op.drop_index("ix_event_logs_severity", table_name="event_logs")
    op.drop_index("ix_event_logs_event_type", table_name="event_logs")
    op.drop_index("ix_event_logs_tenant_id", table_name="event_logs")
    op.drop_table("event_logs")

    op.drop_index("ix_governance_tasks_status", table_name="governance_tasks")
    op.drop_index("ix_governance_tasks_action", table_name="governance_tasks")
    op.drop_index("ix_governance_tasks_tenant_id", table_name="governance_tasks")
    op.drop_table("governance_tasks")

    op.drop_index("ix_admin_tokens_tenant_id", table_name="admin_tokens")
    op.drop_index("ix_admin_tokens_role", table_name="admin_tokens")
    op.drop_index("ix_admin_tokens_token_hash", table_name="admin_tokens")
    op.drop_table("admin_tokens")

    op.drop_index("ix_tenant_namespaces_is_active", table_name="tenant_namespaces")
    op.drop_index("ix_tenant_namespaces_name", table_name="tenant_namespaces")
    op.drop_index("ix_tenant_namespaces_tenant_id", table_name="tenant_namespaces")
    op.drop_table("tenant_namespaces")

    op.drop_index("ix_tenants_status", table_name="tenants")
    op.drop_index("ix_tenants_tenant_id", table_name="tenants")
    op.drop_table("tenants")
