from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    daily_quota: int = Field(default=5000, ge=1)
    rate_limit_per_minute: int = Field(default=120, ge=1)
    retention_days: int = Field(default=30, ge=0)
    purge_after_forget_days: int = Field(default=7, ge=0)
    meta: dict[str, Any] = Field(default_factory=dict)


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    daily_quota: int | None = Field(default=None, ge=1)
    rate_limit_per_minute: int | None = Field(default=None, ge=1)
    retention_days: int | None = Field(default=None, ge=0)
    purge_after_forget_days: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    status: str | None = Field(default=None, min_length=1, max_length=30)
    meta: dict[str, Any] | None = None


class TenantOut(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    status: str
    daily_quota: int
    rate_limit_per_minute: int
    retention_days: int
    purge_after_forget_days: int
    is_active: bool
    meta: dict[str, Any]


class NamespaceCreateRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    retention_days: int = Field(default=0, ge=0)
    daily_quota: int | None = Field(default=None, ge=1)
    meta: dict[str, Any] = Field(default_factory=dict)


class NamespaceUpdateRequest(BaseModel):
    retention_days: int | None = Field(default=None, ge=0)
    daily_quota: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    meta: dict[str, Any] | None = None


class NamespaceOut(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    retention_days: int
    daily_quota: int | None
    is_active: bool
    meta: dict[str, Any]


class AdminApiKeyCreateRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=100)
    name: str = Field(default="admin-managed", min_length=1, max_length=120)
    rate_limit_per_minute: int = Field(default=120, ge=1)
    daily_quota: int = Field(default=5000, ge=1)


class AdminApiKeyQuotaUpdateRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=100)
    rate_limit_per_minute: int | None = Field(default=None, ge=1)
    daily_quota: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class AdminApiKeyOut(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    is_active: bool
    rate_limit_per_minute: int
    daily_quota: int


class AdminApiKeyCreateResponse(BaseModel):
    id: UUID
    tenant_id: str
    name: str
    api_key: str
    rate_limit_per_minute: int
    daily_quota: int


class AdminJobOut(BaseModel):
    id: UUID
    tenant_id: str
    status: str
    total_items: int
    processed_items: int
    error: str | None = None


class AdminAuditOut(BaseModel):
    id: UUID
    tenant_id: str
    key_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]


class QueueHealthOut(BaseModel):
    queued: int
    running: int
    done: int
    failed: int
    oldest_queued_age_seconds: int
    oldest_running_age_seconds: int
    degraded: bool


class EventOut(BaseModel):
    id: UUID
    tenant_id: str | None
    event_type: str
    severity: str
    message: str
    payload: dict[str, Any]
    created_at: str


class TenantExportPageOut(BaseModel):
    tenant_id: str
    cursor: str
    next_cursor: str | None
    page_size: int
    items: list[dict[str, Any]]


class TenantDeleteRequest(BaseModel):
    dry_run: bool = True
    hard_delete: bool = False


class TenantDeleteResponse(BaseModel):
    task_id: UUID
    tenant_id: str
    action: str
    dry_run: bool
    hard_delete: bool
    counts: dict[str, int]


class RetentionPolicyRequest(BaseModel):
    retention_days: int = Field(ge=0)
    purge_after_forget_days: int = Field(ge=0)


class RetentionPolicyOut(BaseModel):
    tenant_id: str
    retention_days: int
    purge_after_forget_days: int


class RetentionEnforceRequest(BaseModel):
    tenant_id: str | None = Field(default=None, min_length=1, max_length=100)
    dry_run: bool = True


class GovernanceTaskOut(BaseModel):
    task_id: UUID
    action: str
    tenant_id: str | None
    dry_run: bool
    details: dict[str, Any]
