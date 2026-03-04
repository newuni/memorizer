from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.admin_service import ADMIN_ROLES, authenticate_admin_token
from app.services.ops_service import inc_metric


@dataclass
class AdminAuthContext:
    token_id: str
    role: str
    tenant_id: str | None


def ensure_admin_role(auth: AdminAuthContext, allowed_roles: set[str]) -> None:
    if auth.role not in allowed_roles:
        inc_metric("admin.auth.forbidden")
        raise HTTPException(status_code=403, detail="Insufficient admin role")


def ensure_admin_write(auth: AdminAuthContext) -> None:
    if auth.role == "viewer":
        inc_metric("admin.auth.forbidden")
        raise HTTPException(status_code=403, detail="Viewer role is read-only")


def resolve_tenant_scope(auth: AdminAuthContext, tenant_id: str | None) -> str | None:
    if auth.role != "owner" and auth.tenant_id is None:
        raise HTTPException(status_code=403, detail="Unscoped admin token is not permitted for non-owner roles")

    if tenant_id is None:
        return auth.tenant_id

    # Owner may explicitly target any tenant. Other roles are constrained to their scoped tenant.
    if auth.role != "owner" and auth.tenant_id and tenant_id != auth.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant scope violation")
    return tenant_id


def require_tenant_scope(auth: AdminAuthContext, tenant_id: str | None) -> str:
    scoped = resolve_tenant_scope(auth, tenant_id)
    if not scoped:
        raise HTTPException(status_code=422, detail="tenant_id is required for unscoped admin token")
    return scoped


def get_admin_auth_context(
    db: Session = Depends(get_db),
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> AdminAuthContext:
    if not x_admin_token:
        inc_metric("admin.auth.missing")
        raise HTTPException(status_code=401, detail="Missing X-Admin-Token")

    token = authenticate_admin_token(db, x_admin_token)
    if not token:
        inc_metric("admin.auth.invalid")
        raise HTTPException(status_code=401, detail="Invalid admin token")

    role = (token.role or "").lower().strip()
    if role not in ADMIN_ROLES:
        inc_metric("admin.auth.invalid_role")
        raise HTTPException(status_code=403, detail="Invalid admin role")

    inc_metric("admin.auth.ok")
    return AdminAuthContext(token_id=str(token.id), role=role, tenant_id=token.tenant_id)
