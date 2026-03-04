from types import SimpleNamespace
from uuid import uuid4

from app.api import routes


def test_profile_without_query(client, monkeypatch):
    monkeypatch.setattr(routes, "build_user_profile", lambda db, tenant_id, namespace: (["a"], ["b"]))

    resp = client.get("/api/v1/profile", params={"namespace": "default"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["static"] == ["a"]
    assert body["dynamic"] == ["b"]
    assert body["search_results"] is None


def test_profile_with_query_runs_search(client, monkeypatch):
    monkeypatch.setattr(routes, "build_user_profile", lambda db, tenant_id, namespace: (["a"], ["b"]))
    monkeypatch.setattr(
        routes,
        "search_memories",
        lambda *args, **kwargs: [{"id": str(uuid4()), "content": "x", "meta": {}, "score": 0.9, "source": "memory"}],
    )

    resp = client.get("/api/v1/profile", params={"namespace": "default", "q": "hello"})
    assert resp.status_code == 200
    assert len(resp.json()["search_results"]) == 1


def test_documents_flow_routes(client, monkeypatch):
    doc_id = uuid4()
    fake_doc = SimpleNamespace(
        id=doc_id,
        namespace="default",
        content_type="text",
        title="t",
        text_content="hello",
        source_url=None,
        meta={},
        status="queued",
        error=None,
    )
    monkeypatch.setattr(routes, "create_document", lambda db, tenant_id, payload: fake_doc)
    monkeypatch.setattr(routes, "list_documents", lambda db, tenant_id, namespace: [fake_doc])
    monkeypatch.setattr(routes, "get_document", lambda db, tenant_id, doc_id: fake_doc)
    monkeypatch.setattr(routes, "delete_document", lambda db, tenant_id, doc_id, hard=False: True)

    class _DelayStub:
        @staticmethod
        def delay(*_args, **_kwargs):
            return None

    monkeypatch.setattr(routes, "process_document_task", _DelayStub)

    r1 = client.post("/api/v1/documents", json={"namespace": "default", "content_type": "text", "text_content": "hello"})
    assert r1.status_code == 200

    r2 = client.get("/api/v1/documents", params={"namespace": "default"})
    assert r2.status_code == 200
    assert len(r2.json()["items"]) == 1

    r3 = client.get(f"/api/v1/documents/{doc_id}")
    assert r3.status_code == 200

    r4 = client.post(f"/api/v1/documents/{doc_id}/process")
    assert r4.status_code == 200
    assert r4.json()["queued"] is True

    r5 = client.delete(f"/api/v1/documents/{doc_id}")
    assert r5.status_code == 200


def test_connectors_routes(client, monkeypatch):
    cid = uuid4()
    fake = SimpleNamespace(id=cid, namespace="default", provider="github", config={"repo_url": "x"}, status="active", error=None)

    monkeypatch.setattr(routes, "create_connector", lambda db, tenant_id, payload: fake)
    monkeypatch.setattr(routes, "list_connectors", lambda db, tenant_id, namespace: [fake])

    class _TaskResult:
        id = "abc"

    class _DelayStub:
        @staticmethod
        def delay(*_args, **_kwargs):
            return _TaskResult()

    monkeypatch.setattr(routes, "sync_connector_task", _DelayStub)

    r1 = client.post("/api/v1/connectors", json={"namespace": "default", "provider": "github", "config": {"repo_url": "https://github.com/newuni/memorizer"}})
    assert r1.status_code == 200

    r2 = client.get("/api/v1/connectors", params={"namespace": "default"})
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    r3 = client.post(f"/api/v1/connectors/{cid}/sync")
    assert r3.status_code == 200
    assert r3.json()["queued_documents"] == 1
