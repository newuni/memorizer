from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.admin_deps import (
    AdminAuthContext,
    ensure_admin_role,
    ensure_admin_write,
    get_admin_auth_context,
    require_tenant_scope,
    resolve_tenant_scope,
)
from app.db.session import get_db
from app.schemas.admin import (
    AdminApiKeyCreateRequest,
    AdminApiKeyCreateResponse,
    AdminApiKeyOut,
    AdminApiKeyQuotaUpdateRequest,
    AdminAuditOut,
    AdminJobOut,
    EventOut,
    GovernanceTaskOut,
    NamespaceCreateRequest,
    NamespaceOut,
    NamespaceUpdateRequest,
    QueueHealthOut,
    RetentionEnforceRequest,
    RetentionPolicyOut,
    RetentionPolicyRequest,
    TenantCreateRequest,
    TenantDeleteRequest,
    TenantDeleteResponse,
    TenantExportPageOut,
    TenantOut,
    TenantUpdateRequest,
)
from app.services.admin_service import (
    create_namespace,
    create_tenant,
    create_tenant_api_key,
    enforce_retention_policies,
    export_tenant_page,
    forget_or_delete_tenant,
    get_namespace,
    get_queue_health,
    iter_tenant_export,
    list_audit_logs_admin,
    list_event_feed,
    list_jobs_admin,
    list_namespaces,
    list_tenant_api_keys,
    list_tenants,
    record_event,
    set_retention_policy,
    update_api_key_quotas,
    update_namespace,
    update_tenant,
    ensure_tenant,
)
from app.services.audit_service import log_audit

admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@admin_router.get("/tenants", response_model=list[TenantOut])
def get_tenants(
    tenant_id: str | None = None,
    include_inactive: bool = True,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = resolve_tenant_scope(auth, tenant_id)
    rows = list_tenants(db, tenant_id=scoped_tenant, include_inactive=include_inactive)
    return [TenantOut.model_validate(row, from_attributes=True) for row in rows]


@admin_router.post("/tenants", response_model=TenantOut)
def post_tenant(
    payload: TenantCreateRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_role(auth, {"owner"})
    try:
        row = create_tenant(
            db,
            tenant_id=payload.tenant_id,
            name=payload.name,
            daily_quota=payload.daily_quota,
            rate_limit_per_minute=payload.rate_limit_per_minute,
            retention_days=payload.retention_days,
            purge_after_forget_days=payload.purge_after_forget_days,
            meta=payload.meta,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    log_audit(db, payload.tenant_id, f"admin:{auth.token_id}", "admin.tenant.create", "tenant", payload.tenant_id)
    record_event(db, "tenant.created", f"Tenant {payload.tenant_id} created", tenant_id=payload.tenant_id)
    return TenantOut.model_validate(row, from_attributes=True)


@admin_router.patch("/tenants/{tenant_id}", response_model=TenantOut)
def patch_tenant(
    tenant_id: str,
    payload: TenantUpdateRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    row = update_tenant(
        db,
        scoped_tenant,
        name=payload.name,
        daily_quota=payload.daily_quota,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        retention_days=payload.retention_days,
        purge_after_forget_days=payload.purge_after_forget_days,
        is_active=payload.is_active,
        status=payload.status,
        meta=payload.meta,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.tenant.update", "tenant", scoped_tenant)
    record_event(db, "tenant.updated", f"Tenant {scoped_tenant} updated", tenant_id=scoped_tenant)
    return TenantOut.model_validate(row, from_attributes=True)


@admin_router.get("/namespaces", response_model=list[NamespaceOut])
def get_namespaces(
    tenant_id: str | None = None,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    rows = list_namespaces(db, scoped_tenant)
    return [NamespaceOut.model_validate(row, from_attributes=True) for row in rows]


@admin_router.post("/namespaces", response_model=NamespaceOut)
def post_namespace(
    payload: NamespaceCreateRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, payload.tenant_id)
    ensure_tenant(db, scoped_tenant)
    try:
        row = create_namespace(
            db,
            tenant_id=scoped_tenant,
            name=payload.name,
            retention_days=payload.retention_days,
            daily_quota=payload.daily_quota,
            meta=payload.meta,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.namespace.create", "namespace", str(row.id))
    record_event(
        db,
        "namespace.created",
        f"Namespace {payload.name} created for tenant {scoped_tenant}",
        tenant_id=scoped_tenant,
        payload={"namespace_id": str(row.id), "name": payload.name},
    )
    return NamespaceOut.model_validate(row, from_attributes=True)


@admin_router.patch("/namespaces/{namespace_id}", response_model=NamespaceOut)
def patch_namespace(
    namespace_id: str,
    payload: NamespaceUpdateRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    existing = get_namespace(db, namespace_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Namespace not found")
    scoped_tenant = require_tenant_scope(auth, existing.tenant_id)
    if scoped_tenant != existing.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant scope violation")

    row = update_namespace(
        db,
        namespace_id,
        retention_days=payload.retention_days,
        daily_quota=payload.daily_quota,
        is_active=payload.is_active,
        meta=payload.meta,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Namespace not found")

    log_audit(db, row.tenant_id, f"admin:{auth.token_id}", "admin.namespace.update", "namespace", str(row.id))
    record_event(db, "namespace.updated", f"Namespace {row.name} updated", tenant_id=row.tenant_id)
    return NamespaceOut.model_validate(row, from_attributes=True)


@admin_router.get("/api-keys", response_model=list[AdminApiKeyOut])
def get_admin_api_keys(
    tenant_id: str | None = None,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    rows = list_tenant_api_keys(db, tenant_id=scoped_tenant)
    return [AdminApiKeyOut.model_validate(row, from_attributes=True) for row in rows]


@admin_router.post("/api-keys", response_model=AdminApiKeyCreateResponse)
def post_admin_api_key(
    payload: AdminApiKeyCreateRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, payload.tenant_id)
    ensure_tenant(db, scoped_tenant)
    row, raw = create_tenant_api_key(
        db,
        tenant_id=scoped_tenant,
        name=payload.name,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        daily_quota=payload.daily_quota,
    )
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.apikey.create", "api_key", str(row.id))
    record_event(db, "apikey.created", f"API key {row.name} created", tenant_id=scoped_tenant, payload={"key_id": str(row.id)})
    return AdminApiKeyCreateResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        name=row.name,
        api_key=raw,
        rate_limit_per_minute=row.rate_limit_per_minute,
        daily_quota=row.daily_quota,
    )


@admin_router.patch("/api-keys/{key_id}", response_model=AdminApiKeyOut)
def patch_admin_api_key(
    key_id: str,
    payload: AdminApiKeyQuotaUpdateRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, payload.tenant_id)
    row = update_api_key_quotas(
        db,
        tenant_id=scoped_tenant,
        key_id=key_id,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        daily_quota=payload.daily_quota,
        is_active=payload.is_active,
    )
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.apikey.update", "api_key", key_id)
    record_event(db, "apikey.updated", f"API key {key_id} updated", tenant_id=scoped_tenant)
    return AdminApiKeyOut.model_validate(row, from_attributes=True)


@admin_router.delete("/api-keys/{key_id}")
def delete_admin_api_key(
    key_id: str,
    tenant_id: str | None = None,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    row = update_api_key_quotas(db, tenant_id=scoped_tenant, key_id=key_id, is_active=False)
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.apikey.revoke", "api_key", key_id)
    record_event(db, "apikey.revoked", f"API key {key_id} revoked", tenant_id=scoped_tenant)
    return {"revoked": True}


@admin_router.get("/jobs", response_model=list[AdminJobOut])
def get_admin_jobs(
    tenant_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = resolve_tenant_scope(auth, tenant_id)
    rows = list_jobs_admin(db, tenant_id=scoped_tenant, status=status, limit=limit)
    return [AdminJobOut.model_validate(row, from_attributes=True) for row in rows]


@admin_router.get("/audit-logs", response_model=list[AdminAuditOut])
def get_admin_audit_logs(
    tenant_id: str | None = None,
    action: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = resolve_tenant_scope(auth, tenant_id)
    rows = list_audit_logs_admin(db, tenant_id=scoped_tenant, action=action, limit=limit)
    return [AdminAuditOut.model_validate(row, from_attributes=True) for row in rows]


@admin_router.get("/observability/queue-health", response_model=QueueHealthOut)
def get_admin_queue_health(
    tenant_id: str | None = None,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = resolve_tenant_scope(auth, tenant_id)
    payload = get_queue_health(db, tenant_id=scoped_tenant)
    return QueueHealthOut(**payload)


@admin_router.get("/observability/events", response_model=list[EventOut])
def get_admin_events(
    tenant_id: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = resolve_tenant_scope(auth, tenant_id)
    rows = list_event_feed(db, tenant_id=scoped_tenant, event_type=event_type, limit=limit)
    return [
        EventOut(
            id=row.id,
            tenant_id=row.tenant_id,
            event_type=row.event_type,
            severity=row.severity,
            message=row.message,
            payload=row.payload,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


@admin_router.get("/tenants/{tenant_id}/export", response_model=TenantExportPageOut)
def get_admin_tenant_export(
    tenant_id: str,
    cursor: str | None = None,
    page_size: int = 100,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    page = export_tenant_page(db, tenant_id=scoped_tenant, cursor=cursor, page_size=page_size)
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.tenant.export.page", "tenant", scoped_tenant)
    record_event(db, "tenant.export.page", f"Tenant export page generated for {scoped_tenant}", tenant_id=scoped_tenant)
    return TenantExportPageOut(**page)


@admin_router.get("/tenants/{tenant_id}/export/stream")
def stream_admin_tenant_export(
    tenant_id: str,
    page_size: int = 200,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.tenant.export.stream", "tenant", scoped_tenant)
    record_event(db, "tenant.export.stream", f"Tenant export stream opened for {scoped_tenant}", tenant_id=scoped_tenant)
    return StreamingResponse(iter_tenant_export(db, tenant_id=scoped_tenant, page_size=page_size), media_type="application/x-ndjson")


@admin_router.post("/tenants/{tenant_id}/forget", response_model=TenantDeleteResponse)
def post_admin_forget_tenant(
    tenant_id: str,
    payload: TenantDeleteRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    if payload.hard_delete and auth.role != "owner":
        raise HTTPException(status_code=403, detail="Hard delete requires owner role")

    task, counts = forget_or_delete_tenant(
        db,
        tenant_id=scoped_tenant,
        dry_run=payload.dry_run,
        hard_delete=payload.hard_delete,
    )
    log_audit(
        db,
        scoped_tenant,
        f"admin:{auth.token_id}",
        "admin.tenant.hard_delete" if payload.hard_delete else "admin.tenant.forget",
        "tenant",
        scoped_tenant,
        {"dry_run": payload.dry_run, "hard_delete": payload.hard_delete, "counts": counts},
    )
    record_event(
        db,
        "tenant.hard_delete" if payload.hard_delete else "tenant.forget",
        f"Tenant workflow executed for {scoped_tenant}",
        tenant_id=scoped_tenant,
        payload={"dry_run": payload.dry_run, "hard_delete": payload.hard_delete, "counts": counts},
    )
    return TenantDeleteResponse(
        task_id=task.id,
        tenant_id=scoped_tenant,
        action=task.action,
        dry_run=payload.dry_run,
        hard_delete=payload.hard_delete,
        counts=counts,
    )


@admin_router.put("/tenants/{tenant_id}/retention", response_model=RetentionPolicyOut)
def put_tenant_retention(
    tenant_id: str,
    payload: RetentionPolicyRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = require_tenant_scope(auth, tenant_id)
    row = set_retention_policy(
        db,
        tenant_id=scoped_tenant,
        retention_days=payload.retention_days,
        purge_after_forget_days=payload.purge_after_forget_days,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")
    log_audit(db, scoped_tenant, f"admin:{auth.token_id}", "admin.retention.update", "tenant", scoped_tenant)
    record_event(db, "retention.updated", f"Retention policy updated for {scoped_tenant}", tenant_id=scoped_tenant)
    return RetentionPolicyOut(
        tenant_id=scoped_tenant,
        retention_days=row.retention_days,
        purge_after_forget_days=row.purge_after_forget_days,
    )


@admin_router.post("/governance/retention/enforce", response_model=GovernanceTaskOut)
def post_retention_enforcement(
    payload: RetentionEnforceRequest,
    db: Session = Depends(get_db),
    auth: AdminAuthContext = Depends(get_admin_auth_context),
):
    ensure_admin_write(auth)
    scoped_tenant = resolve_tenant_scope(auth, payload.tenant_id)
    task, details = enforce_retention_policies(db, tenant_id=scoped_tenant, dry_run=payload.dry_run)
    audit_tenant = scoped_tenant or "global"
    log_audit(
        db,
        audit_tenant,
        f"admin:{auth.token_id}",
        "admin.retention.enforce",
        "tenant",
        scoped_tenant,
        {"dry_run": payload.dry_run, "details": details},
    )
    record_event(
        db,
        "retention.enforced",
        "Retention enforcement task executed",
        tenant_id=scoped_tenant,
        payload={"dry_run": payload.dry_run, "details": details},
    )
    return GovernanceTaskOut(task_id=task.id, action=task.action, tenant_id=scoped_tenant, dry_run=payload.dry_run, details=details)
