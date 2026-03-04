from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

SENSITIVE_ACTIONS = {
    "memory.delete",
    "memory.forget",
    "memory.hard_delete",
    "apikey.create",
    "apikey.revoke",
    "tenant.export",
    "connector.sync",
}


def log_audit(
    db: Session,
    tenant_id: str,
    key_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> None:
    if action not in SENSITIVE_ACTIONS and not action.startswith("admin."):
        return
    row = AuditLog(
        tenant_id=tenant_id,
        key_id=key_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
    )
    db.add(row)
    db.commit()
