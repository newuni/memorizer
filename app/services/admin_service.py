from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Iterator

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_api_key, hash_api_key
from app.models.admin_token import AdminToken
from app.models.api_key import ApiKey
from app.models.audit_log import AuditLog
from app.models.connector import Connector
from app.models.document import Document, DocumentChunk
from app.models.event_log import EventLog
from app.models.governance_task import GovernanceTask
from app.models.ingestion_job import IngestionJob
from app.models.memory import Memory
from app.models.tenant import Tenant
from app.models.tenant_namespace import TenantNamespace


ADMIN_ROLES = {"owner", "admin", "viewer"}


def _to_iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def ensure_tenant(db: Session, tenant_id: str, name: str | None = None) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if tenant:
        return tenant
    tenant = Tenant(
        tenant_id=tenant_id,
        name=name or tenant_id,
        status="active",
        rate_limit_per_minute=settings.rate_limit_per_minute,
        daily_quota=settings.default_daily_quota,
        retention_days=settings.default_retention_days,
        purge_after_forget_days=settings.default_purge_after_forget_days,
        is_active=True,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def ensure_namespace(db: Session, tenant_id: str, namespace: str = "default") -> TenantNamespace:
    row = (
        db.query(TenantNamespace)
        .filter(TenantNamespace.tenant_id == tenant_id, TenantNamespace.name == namespace)
        .first()
    )
    if row:
        return row
    row = TenantNamespace(tenant_id=tenant_id, name=namespace, retention_days=0, is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def bootstrap_admin_token(
    db: Session,
    raw_token: str,
    name: str = "bootstrap-owner",
    role: str = "owner",
    tenant_id: str | None = None,
) -> AdminToken:
    role = role.lower().strip()
    if role not in ADMIN_ROLES:
        role = "owner"

    hashed = hash_api_key(raw_token)
    existing = db.query(AdminToken).filter(AdminToken.token_hash == hashed).first()
    if existing:
        existing.is_active = True
        existing.role = role
        existing.tenant_id = tenant_id or existing.tenant_id
        db.commit()
        db.refresh(existing)
        return existing

    row = AdminToken(name=name, token_hash=hashed, role=role, tenant_id=tenant_id, is_active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def authenticate_admin_token(db: Session, raw_token: str) -> AdminToken | None:
    hashed = hash_api_key(raw_token)
    token = db.query(AdminToken).filter(AdminToken.token_hash == hashed, AdminToken.is_active.is_(True)).first()
    if not token:
        return None
    token.last_used_at = datetime.now(UTC)
    db.commit()
    db.refresh(token)
    return token


def record_event(
    db: Session,
    event_type: str,
    message: str,
    tenant_id: str | None = None,
    payload: dict[str, Any] | None = None,
    severity: str = "info",
) -> EventLog:
    row = EventLog(
        tenant_id=tenant_id,
        event_type=event_type,
        severity=severity,
        message=message,
        payload=payload or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_tenants(db: Session, tenant_id: str | None = None, include_inactive: bool = True) -> list[Tenant]:
    q = db.query(Tenant)
    if tenant_id:
        q = q.filter(Tenant.tenant_id == tenant_id)
    if not include_inactive:
        q = q.filter(Tenant.is_active.is_(True))
    return q.order_by(Tenant.created_at.desc()).all()


def create_tenant(
    db: Session,
    tenant_id: str,
    name: str,
    daily_quota: int,
    rate_limit_per_minute: int,
    retention_days: int,
    purge_after_forget_days: int,
    meta: dict[str, Any] | None = None,
) -> Tenant:
    existing = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if existing:
        raise ValueError("Tenant already exists")

    row = Tenant(
        tenant_id=tenant_id,
        name=name,
        status="active",
        daily_quota=daily_quota,
        rate_limit_per_minute=rate_limit_per_minute,
        retention_days=retention_days,
        purge_after_forget_days=purge_after_forget_days,
        meta=meta or {},
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    ensure_namespace(db, tenant_id=tenant_id, namespace="default")
    return row


def update_tenant(
    db: Session,
    tenant_id: str,
    *,
    name: str | None = None,
    daily_quota: int | None = None,
    rate_limit_per_minute: int | None = None,
    retention_days: int | None = None,
    purge_after_forget_days: int | None = None,
    is_active: bool | None = None,
    status: str | None = None,
    meta: dict[str, Any] | None = None,
) -> Tenant | None:
    row = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not row:
        return None
    if name is not None:
        row.name = name
    if daily_quota is not None:
        row.daily_quota = daily_quota
    if rate_limit_per_minute is not None:
        row.rate_limit_per_minute = rate_limit_per_minute
    if retention_days is not None:
        row.retention_days = retention_days
    if purge_after_forget_days is not None:
        row.purge_after_forget_days = purge_after_forget_days
    if is_active is not None:
        row.is_active = is_active
    if status is not None:
        row.status = status
    if meta is not None:
        row.meta = meta
    db.commit()
    db.refresh(row)
    return row


def list_namespaces(db: Session, tenant_id: str) -> list[TenantNamespace]:
    return (
        db.query(TenantNamespace)
        .filter(TenantNamespace.tenant_id == tenant_id)
        .order_by(TenantNamespace.created_at.desc())
        .all()
    )


def create_namespace(
    db: Session,
    tenant_id: str,
    name: str,
    retention_days: int = 0,
    daily_quota: int | None = None,
    meta: dict[str, Any] | None = None,
) -> TenantNamespace:
    existing = (
        db.query(TenantNamespace)
        .filter(TenantNamespace.tenant_id == tenant_id, TenantNamespace.name == name)
        .first()
    )
    if existing:
        raise ValueError("Namespace already exists")

    row = TenantNamespace(
        tenant_id=tenant_id,
        name=name,
        retention_days=retention_days,
        daily_quota=daily_quota,
        is_active=True,
        meta=meta or {},
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_namespace(
    db: Session,
    namespace_id: str,
    *,
    retention_days: int | None = None,
    daily_quota: int | None = None,
    is_active: bool | None = None,
    meta: dict[str, Any] | None = None,
) -> TenantNamespace | None:
    row = db.query(TenantNamespace).filter(TenantNamespace.id == namespace_id).first()
    if not row:
        return None
    if retention_days is not None:
        row.retention_days = retention_days
    if daily_quota is not None:
        row.daily_quota = daily_quota
    if is_active is not None:
        row.is_active = is_active
    if meta is not None:
        row.meta = meta
    db.commit()
    db.refresh(row)
    return row


def get_namespace(db: Session, namespace_id: str) -> TenantNamespace | None:
    return db.query(TenantNamespace).filter(TenantNamespace.id == namespace_id).first()


def list_tenant_api_keys(db: Session, tenant_id: str) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == tenant_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


def create_tenant_api_key(
    db: Session,
    tenant_id: str,
    name: str,
    rate_limit_per_minute: int,
    daily_quota: int,
) -> tuple[ApiKey, str]:
    raw = generate_api_key(prefix="adm")
    row = ApiKey(
        tenant_id=tenant_id,
        name=name,
        key_hash=hash_api_key(raw),
        is_active=True,
        rate_limit_per_minute=rate_limit_per_minute,
        daily_quota=daily_quota,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, raw


def update_api_key_quotas(
    db: Session,
    tenant_id: str,
    key_id: str,
    *,
    rate_limit_per_minute: int | None = None,
    daily_quota: int | None = None,
    is_active: bool | None = None,
) -> ApiKey | None:
    row = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id).first()
    if not row:
        return None
    if rate_limit_per_minute is not None:
        row.rate_limit_per_minute = rate_limit_per_minute
    if daily_quota is not None:
        row.daily_quota = daily_quota
    if is_active is not None:
        row.is_active = is_active
    db.commit()
    db.refresh(row)
    return row


def revoke_tenant_api_key(db: Session, tenant_id: str, key_id: str) -> bool:
    row = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id).first()
    if not row:
        return False
    row.is_active = False
    db.commit()
    return True


def list_jobs_admin(db: Session, tenant_id: str | None = None, status: str | None = None, limit: int = 100) -> list[IngestionJob]:
    q = db.query(IngestionJob)
    if tenant_id:
        q = q.filter(IngestionJob.tenant_id == tenant_id)
    if status:
        q = q.filter(IngestionJob.status == status)
    return q.order_by(IngestionJob.created_at.desc()).limit(min(max(limit, 1), 500)).all()


def list_audit_logs_admin(db: Session, tenant_id: str | None = None, action: str | None = None, limit: int = 100) -> list[AuditLog]:
    q = db.query(AuditLog)
    if tenant_id:
        q = q.filter(AuditLog.tenant_id == tenant_id)
    if action:
        q = q.filter(AuditLog.action == action)
    return q.order_by(AuditLog.created_at.desc()).limit(min(max(limit, 1), 500)).all()


def get_queue_health(db: Session, tenant_id: str | None = None) -> dict[str, Any]:
    q = db.query(IngestionJob.status, func.count(IngestionJob.id)).group_by(IngestionJob.status)
    if tenant_id:
        q = q.filter(IngestionJob.tenant_id == tenant_id)

    counts = {status: int(count) for status, count in q.all()}
    queued_q = db.query(func.min(IngestionJob.created_at)).filter(IngestionJob.status == "queued")
    running_q = db.query(func.min(IngestionJob.updated_at)).filter(IngestionJob.status == "running")
    if tenant_id:
        queued_q = queued_q.filter(IngestionJob.tenant_id == tenant_id)
        running_q = running_q.filter(IngestionJob.tenant_id == tenant_id)

    oldest_queued = queued_q.scalar()
    oldest_running = running_q.scalar()
    now = datetime.now(UTC)

    queued_age_seconds = int((now - oldest_queued).total_seconds()) if oldest_queued else 0
    running_age_seconds = int((now - oldest_running).total_seconds()) if oldest_running else 0

    return {
        "queued": counts.get("queued", 0),
        "running": counts.get("running", 0),
        "done": counts.get("done", 0),
        "failed": counts.get("failed", 0),
        "oldest_queued_age_seconds": queued_age_seconds,
        "oldest_running_age_seconds": running_age_seconds,
        "degraded": queued_age_seconds > 600 or running_age_seconds > 1800,
    }


def list_event_feed(
    db: Session,
    tenant_id: str | None = None,
    limit: int = 100,
    event_type: str | None = None,
) -> list[EventLog]:
    q = db.query(EventLog)
    if tenant_id:
        q = q.filter(EventLog.tenant_id == tenant_id)
    if event_type:
        q = q.filter(EventLog.event_type == event_type)
    return q.order_by(EventLog.created_at.desc()).limit(min(max(limit, 1), 500)).all()


def _memory_to_export_row(item: Memory) -> dict[str, Any]:
    return {
        "resource": "memory",
        "id": str(item.id),
        "tenant_id": item.tenant_id,
        "namespace": item.namespace,
        "content": item.content,
        "meta": item.meta,
        "is_deleted": bool(item.is_deleted),
        "created_at": _to_iso(item.created_at),
        "updated_at": _to_iso(item.updated_at),
    }


def export_tenant_page(db: Session, tenant_id: str, cursor: str | None = None, page_size: int = 100) -> dict[str, Any]:
    offset = int(cursor or "0")
    limit = min(max(page_size, 1), 1000)
    rows = (
        db.query(Memory)
        .filter(Memory.tenant_id == tenant_id)
        .order_by(Memory.created_at.asc(), Memory.id.asc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )
    has_more = len(rows) > limit
    page_rows = rows[:limit]
    next_cursor = str(offset + limit) if has_more else None
    return {
        "tenant_id": tenant_id,
        "cursor": str(offset),
        "next_cursor": next_cursor,
        "page_size": limit,
        "items": [_memory_to_export_row(row) for row in page_rows],
    }


def iter_tenant_export(db: Session, tenant_id: str, page_size: int = 200) -> Iterator[str]:
    cursor: str | None = "0"
    while True:
        page = export_tenant_page(db, tenant_id=tenant_id, cursor=cursor, page_size=page_size)
        items = page["items"]
        if not items:
            break
        for item in items:
            yield json.dumps(item) + "\n"
        cursor = page["next_cursor"]
        if not cursor:
            break


def _tenant_counts(db: Session, tenant_id: str) -> dict[str, int]:
    return {
        "memories": int(db.query(func.count(Memory.id)).filter(Memory.tenant_id == tenant_id).scalar() or 0),
        "documents": int(db.query(func.count(Document.id)).filter(Document.tenant_id == tenant_id).scalar() or 0),
        "document_chunks": int(db.query(func.count(DocumentChunk.id)).filter(DocumentChunk.tenant_id == tenant_id).scalar() or 0),
        "connectors": int(db.query(func.count(Connector.id)).filter(Connector.tenant_id == tenant_id).scalar() or 0),
        "api_keys": int(db.query(func.count(ApiKey.id)).filter(ApiKey.tenant_id == tenant_id).scalar() or 0),
        "jobs": int(db.query(func.count(IngestionJob.id)).filter(IngestionJob.tenant_id == tenant_id).scalar() or 0),
        "audit_logs": int(db.query(func.count(AuditLog.id)).filter(AuditLog.tenant_id == tenant_id).scalar() or 0),
        "event_logs": int(db.query(func.count(EventLog.id)).filter(EventLog.tenant_id == tenant_id).scalar() or 0),
        "namespaces": int(db.query(func.count(TenantNamespace.id)).filter(TenantNamespace.tenant_id == tenant_id).scalar() or 0),
    }


def forget_or_delete_tenant(
    db: Session,
    tenant_id: str,
    *,
    dry_run: bool = True,
    hard_delete: bool = False,
) -> tuple[GovernanceTask, dict[str, int]]:
    counts = _tenant_counts(db, tenant_id)
    action = "tenant.hard_delete" if hard_delete else "tenant.forget"
    task = GovernanceTask(
        tenant_id=tenant_id,
        action=action,
        status="done",
        dry_run=dry_run,
        hard_delete=hard_delete,
        details=counts,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    if dry_run:
        return task, counts

    now = datetime.now(UTC)
    if hard_delete:
        db.query(DocumentChunk).filter(DocumentChunk.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(Document).filter(Document.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(Memory).filter(Memory.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(Connector).filter(Connector.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(ApiKey).filter(ApiKey.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(IngestionJob).filter(IngestionJob.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(EventLog).filter(EventLog.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(TenantNamespace).filter(TenantNamespace.tenant_id == tenant_id).delete(synchronize_session=False)
        db.query(Tenant).filter(Tenant.tenant_id == tenant_id).delete(synchronize_session=False)
    else:
        db.query(Memory).filter(Memory.tenant_id == tenant_id, Memory.is_deleted.is_(False)).update(
            {Memory.is_deleted: True, Memory.deleted_at: now},
            synchronize_session=False,
        )
        db.query(Document).filter(Document.tenant_id == tenant_id, Document.is_deleted.is_(False)).update(
            {Document.is_deleted: True, Document.deleted_at: now},
            synchronize_session=False,
        )
        db.query(ApiKey).filter(ApiKey.tenant_id == tenant_id).update({ApiKey.is_active: False}, synchronize_session=False)
        db.query(Tenant).filter(Tenant.tenant_id == tenant_id).update(
            {Tenant.status: "forgetting", Tenant.is_active: False},
            synchronize_session=False,
        )
    db.commit()

    task.details = counts
    db.commit()
    db.refresh(task)
    return task, counts


def set_retention_policy(db: Session, tenant_id: str, retention_days: int, purge_after_forget_days: int) -> Tenant | None:
    return update_tenant(
        db,
        tenant_id,
        retention_days=retention_days,
        purge_after_forget_days=purge_after_forget_days,
    )


def enforce_retention_policies(
    db: Session,
    tenant_id: str | None = None,
    *,
    dry_run: bool = True,
) -> tuple[GovernanceTask, dict[str, Any]]:
    tenants_q = db.query(Tenant)
    if tenant_id:
        tenants_q = tenants_q.filter(Tenant.tenant_id == tenant_id)
    tenants = tenants_q.all()

    totals: dict[str, Any] = {
        "tenants_scanned": len(tenants),
        "soft_delete_memories": 0,
        "soft_delete_documents": 0,
        "hard_delete_memories": 0,
        "hard_delete_documents": 0,
    }

    now = datetime.now(UTC)
    for tenant in tenants:
        retention_days = max(int(tenant.retention_days or 0), 0)
        purge_days = max(int(tenant.purge_after_forget_days or 0), 0)

        if retention_days > 0:
            retention_cutoff = now - timedelta(days=retention_days)
            mem_q = db.query(Memory).filter(
                Memory.tenant_id == tenant.tenant_id,
                Memory.is_deleted.is_(False),
                Memory.created_at < retention_cutoff,
            )
            doc_q = db.query(Document).filter(
                Document.tenant_id == tenant.tenant_id,
                Document.is_deleted.is_(False),
                Document.created_at < retention_cutoff,
            )
            mem_count = int(mem_q.count())
            doc_count = int(doc_q.count())
            totals["soft_delete_memories"] += mem_count
            totals["soft_delete_documents"] += doc_count
            if not dry_run:
                mem_q.update({Memory.is_deleted: True, Memory.deleted_at: now}, synchronize_session=False)
                doc_q.update({Document.is_deleted: True, Document.deleted_at: now}, synchronize_session=False)

        if purge_days > 0:
            purge_cutoff = now - timedelta(days=purge_days)
            mem_purge_q = db.query(Memory).filter(
                Memory.tenant_id == tenant.tenant_id,
                Memory.is_deleted.is_(True),
                Memory.deleted_at.is_not(None),
                Memory.deleted_at < purge_cutoff,
            )
            doc_purge_q = db.query(Document).filter(
                Document.tenant_id == tenant.tenant_id,
                Document.is_deleted.is_(True),
                Document.deleted_at.is_not(None),
                Document.deleted_at < purge_cutoff,
            )
            mem_purge_count = int(mem_purge_q.count())
            doc_purge_count = int(doc_purge_q.count())
            totals["hard_delete_memories"] += mem_purge_count
            totals["hard_delete_documents"] += doc_purge_count
            if not dry_run:
                mem_purge_q.delete(synchronize_session=False)
                doc_purge_q.delete(synchronize_session=False)

    task = GovernanceTask(
        tenant_id=tenant_id,
        action="retention.enforce",
        status="done",
        dry_run=dry_run,
        hard_delete=False,
        details=totals,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    if not dry_run:
        db.commit()

    return task, totals
