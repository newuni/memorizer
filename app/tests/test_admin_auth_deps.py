from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api import admin_deps
from app.api.admin_deps import AdminAuthContext, ensure_admin_write, get_admin_auth_context, resolve_tenant_scope


def test_get_admin_auth_context_missing_token_raises_401():
    with pytest.raises(HTTPException) as exc:
        get_admin_auth_context(db=None, x_admin_token=None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing X-Admin-Token"


def test_get_admin_auth_context_invalid_token_raises_401(monkeypatch):
    monkeypatch.setattr(admin_deps, "authenticate_admin_token", lambda db, raw_token: None)

    with pytest.raises(HTTPException) as exc:
        get_admin_auth_context(db=None, x_admin_token="bad")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid admin token"


def test_get_admin_auth_context_invalid_role_raises_403(monkeypatch):
    monkeypatch.setattr(
        admin_deps,
        "authenticate_admin_token",
        lambda db, raw_token: SimpleNamespace(id="a1", role="superuser", tenant_id=None),
    )

    with pytest.raises(HTTPException) as exc:
        get_admin_auth_context(db=None, x_admin_token="tok")

    assert exc.value.status_code == 403
    assert exc.value.detail == "Invalid admin role"


def test_get_admin_auth_context_success(monkeypatch):
    monkeypatch.setattr(
        admin_deps,
        "authenticate_admin_token",
        lambda db, raw_token: SimpleNamespace(id="a1", role="admin", tenant_id="tenant-1"),
    )

    ctx = get_admin_auth_context(db=None, x_admin_token="tok")

    assert ctx.token_id == "a1"
    assert ctx.role == "admin"
    assert ctx.tenant_id == "tenant-1"


def test_resolve_tenant_scope_defaults_to_scoped_tenant():
    auth = AdminAuthContext(token_id="a1", role="admin", tenant_id="tenant-42")

    assert resolve_tenant_scope(auth, None) == "tenant-42"


def test_resolve_tenant_scope_blocks_out_of_scope_tenant_for_non_owner():
    auth = AdminAuthContext(token_id="a1", role="admin", tenant_id="tenant-42")

    with pytest.raises(HTTPException) as exc:
        resolve_tenant_scope(auth, "tenant-99")

    assert exc.value.status_code == 403


def test_resolve_tenant_scope_allows_owner_global_target():
    auth = AdminAuthContext(token_id="a1", role="owner", tenant_id=None)

    assert resolve_tenant_scope(auth, "tenant-99") == "tenant-99"


def test_resolve_tenant_scope_blocks_unscoped_non_owner():
    auth = AdminAuthContext(token_id="a1", role="admin", tenant_id=None)

    with pytest.raises(HTTPException) as exc:
        resolve_tenant_scope(auth, "tenant-99")

    assert exc.value.status_code == 403


def test_ensure_admin_write_blocks_viewer():
    auth = AdminAuthContext(token_id="a1", role="viewer", tenant_id="tenant-1")

    with pytest.raises(HTTPException) as exc:
        ensure_admin_write(auth)

    assert exc.value.status_code == 403
    assert exc.value.detail == "Viewer role is read-only"
