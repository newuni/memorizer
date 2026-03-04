from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import admin_routes
from app.api.admin_deps import AdminAuthContext, get_admin_auth_context
from app.main import app


def test_admin_list_tenants(admin_client, monkeypatch):
    tid = uuid4()
    monkeypatch.setattr(
        admin_routes,
        "list_tenants",
        lambda db, tenant_id=None, include_inactive=True: [
            SimpleNamespace(
                id=tid,
                tenant_id="tenant-1",
                name="Tenant 1",
                status="active",
                daily_quota=5000,
                rate_limit_per_minute=120,
                retention_days=30,
                purge_after_forget_days=7,
                is_active=True,
                meta={},
            )
        ],
    )

    resp = admin_client.get("/api/v1/admin/tenants")

    assert resp.status_code == 200
    assert resp.json()[0]["tenant_id"] == "tenant-1"


def test_admin_create_tenant_conflict_returns_409(admin_client, monkeypatch):
    def _boom(**_kwargs):
        raise ValueError("Tenant already exists")

    monkeypatch.setattr(admin_routes, "create_tenant", lambda *args, **kwargs: _boom())

    resp = admin_client.post(
        "/api/v1/admin/tenants",
        json={
            "tenant_id": "tenant-1",
            "name": "Tenant 1",
            "daily_quota": 5000,
            "rate_limit_per_minute": 120,
            "retention_days": 30,
            "purge_after_forget_days": 7,
        },
    )

    assert resp.status_code == 409


def test_admin_namespaces_defaults_to_scoped_tenant(monkeypatch):
    app.dependency_overrides[get_admin_auth_context] = lambda: AdminAuthContext(
        token_id="adm-scoped",
        role="admin",
        tenant_id="tenant-scoped",
    )
    seen = {"tenant_id": None}

    monkeypatch.setattr(admin_routes, "list_namespaces", lambda db, tenant_id: seen.update({"tenant_id": tenant_id}) or [])

    with TestClient(app) as client:
        resp = client.get("/api/v1/admin/namespaces")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert seen["tenant_id"] == "tenant-scoped"


def test_viewer_cannot_mutate_admin_resources(monkeypatch):
    app.dependency_overrides[get_admin_auth_context] = lambda: AdminAuthContext(
        token_id="adm-viewer",
        role="viewer",
        tenant_id="tenant-1",
    )

    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/admin/api-keys",
            json={"tenant_id": "tenant-1", "name": "ops", "daily_quota": 100, "rate_limit_per_minute": 10},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Viewer role is read-only"


def test_admin_create_api_key_returns_plaintext(admin_client, monkeypatch):
    key_id = uuid4()

    monkeypatch.setattr(admin_routes, "ensure_tenant", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        admin_routes,
        "create_tenant_api_key",
        lambda db, tenant_id, name, rate_limit_per_minute, daily_quota: (
            SimpleNamespace(
                id=key_id,
                tenant_id=tenant_id,
                name=name,
                rate_limit_per_minute=rate_limit_per_minute,
                daily_quota=daily_quota,
            ),
            "raw-admin-key",
        ),
    )

    resp = admin_client.post(
        "/api/v1/admin/api-keys",
        json={
            "tenant_id": "tenant-1",
            "name": "ops",
            "daily_quota": 1000,
            "rate_limit_per_minute": 90,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(key_id)
    assert body["api_key"] == "raw-admin-key"


def test_admin_jobs_list(admin_client, monkeypatch):
    job_id = uuid4()
    monkeypatch.setattr(
        admin_routes,
        "list_jobs_admin",
        lambda db, tenant_id=None, status=None, limit=100: [
            SimpleNamespace(id=job_id, tenant_id="tenant-1", status="queued", total_items=2, processed_items=0, error=None)
        ],
    )

    resp = admin_client.get("/api/v1/admin/jobs", params={"tenant_id": "tenant-1"})

    assert resp.status_code == 200
    assert resp.json()[0]["id"] == str(job_id)


def test_admin_audit_logs_list(admin_client, monkeypatch):
    audit_id = uuid4()
    monkeypatch.setattr(
        admin_routes,
        "list_audit_logs_admin",
        lambda db, tenant_id=None, action=None, limit=100: [
            SimpleNamespace(
                id=audit_id,
                tenant_id="tenant-1",
                key_id="admin:1",
                action="admin.tenant.update",
                resource_type="tenant",
                resource_id="tenant-1",
                details={},
            )
        ],
    )

    resp = admin_client.get("/api/v1/admin/audit-logs", params={"tenant_id": "tenant-1"})

    assert resp.status_code == 200
    assert resp.json()[0]["action"] == "admin.tenant.update"


def test_admin_queue_health(admin_client, monkeypatch):
    monkeypatch.setattr(
        admin_routes,
        "get_queue_health",
        lambda db, tenant_id=None: {
            "queued": 1,
            "running": 1,
            "done": 10,
            "failed": 0,
            "oldest_queued_age_seconds": 30,
            "oldest_running_age_seconds": 20,
            "degraded": False,
        },
    )

    resp = admin_client.get("/api/v1/admin/observability/queue-health")

    assert resp.status_code == 200
    assert resp.json()["queued"] == 1


def test_admin_event_feed(admin_client, monkeypatch):
    event_id = uuid4()
    monkeypatch.setattr(
        admin_routes,
        "list_event_feed",
        lambda db, tenant_id=None, event_type=None, limit=100: [
            SimpleNamespace(
                id=event_id,
                tenant_id="tenant-1",
                event_type="tenant.updated",
                severity="info",
                message="updated",
                payload={"x": 1},
                created_at=SimpleNamespace(isoformat=lambda: "2026-03-04T00:00:00+00:00"),
            )
        ],
    )

    resp = admin_client.get("/api/v1/admin/observability/events", params={"tenant_id": "tenant-1"})

    assert resp.status_code == 200
    assert resp.json()[0]["event_type"] == "tenant.updated"


def test_admin_tenant_export_paged(admin_client, monkeypatch):
    monkeypatch.setattr(
        admin_routes,
        "export_tenant_page",
        lambda db, tenant_id, cursor=None, page_size=100: {
            "tenant_id": tenant_id,
            "cursor": "0",
            "next_cursor": None,
            "page_size": 1,
            "items": [{"resource": "memory", "id": "m1"}],
        },
    )

    resp = admin_client.get("/api/v1/admin/tenants/tenant-1/export", params={"page_size": 1})

    assert resp.status_code == 200
    assert resp.json()["items"][0]["id"] == "m1"


def test_admin_tenant_export_stream(admin_client, monkeypatch):
    monkeypatch.setattr(admin_routes, "iter_tenant_export", lambda db, tenant_id, page_size=200: iter(['{"id":"m1"}\n']))

    resp = admin_client.get("/api/v1/admin/tenants/tenant-1/export/stream")

    assert resp.status_code == 200
    assert '"id":"m1"' in resp.text


def test_admin_forget_tenant_dry_run(admin_client, monkeypatch):
    task_id = uuid4()
    monkeypatch.setattr(
        admin_routes,
        "forget_or_delete_tenant",
        lambda db, tenant_id, dry_run=True, hard_delete=False: (
            SimpleNamespace(id=task_id, action="tenant.forget"),
            {"memories": 10, "documents": 2},
        ),
    )

    resp = admin_client.post("/api/v1/admin/tenants/tenant-1/forget", json={"dry_run": True, "hard_delete": False})

    assert resp.status_code == 200
    assert resp.json()["task_id"] == str(task_id)
    assert resp.json()["dry_run"] is True


def test_admin_retention_enforcement(admin_client, monkeypatch):
    task_id = uuid4()
    monkeypatch.setattr(
        admin_routes,
        "enforce_retention_policies",
        lambda db, tenant_id=None, dry_run=True: (
            SimpleNamespace(id=task_id, action="retention.enforce"),
            {"tenants_scanned": 1, "soft_delete_memories": 2, "soft_delete_documents": 1, "hard_delete_memories": 0, "hard_delete_documents": 0},
        ),
    )

    resp = admin_client.post("/api/v1/admin/governance/retention/enforce", json={"tenant_id": "tenant-1", "dry_run": True})

    assert resp.status_code == 200
    assert resp.json()["task_id"] == str(task_id)
    assert resp.json()["details"]["tenants_scanned"] == 1
