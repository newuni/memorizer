from types import SimpleNamespace
from uuid import uuid4

from app.api import routes


def test_list_api_keys(client, monkeypatch):
    k1 = SimpleNamespace(id=uuid4(), name="bootstrap", is_active=True)
    k2 = SimpleNamespace(id=uuid4(), name="agent", is_active=False)

    monkeypatch.setattr(routes, "list_api_keys", lambda db, tenant_id: [k1, k2])

    resp = client.get("/api/v1/api-keys")

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["name"] == "bootstrap"
    assert body[1]["is_active"] is False


def test_create_api_key_returns_plaintext_once(client, monkeypatch):
    kid = uuid4()

    def _fake_create(db, tenant_id, name):
        assert tenant_id == "t1"
        assert name == "ci-bot"
        return SimpleNamespace(id=kid, name=name), "plain-secret"

    monkeypatch.setattr(routes, "create_api_key", _fake_create)

    resp = client.post("/api/v1/api-keys", json={"name": "ci-bot"})

    assert resp.status_code == 200
    assert resp.json() == {"id": str(kid), "name": "ci-bot", "api_key": "plain-secret"}


def test_revoke_api_key_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(routes, "revoke_api_key", lambda db, tenant_id, key_id: False)

    resp = client.delete(f"/api/v1/api-keys/{uuid4()}")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "API key not found"


def test_revoke_api_key_ok(client, monkeypatch):
    monkeypatch.setattr(routes, "revoke_api_key", lambda db, tenant_id, key_id: True)

    resp = client.delete(f"/api/v1/api-keys/{uuid4()}")

    assert resp.status_code == 200
    assert resp.json() == {"revoked": True}
