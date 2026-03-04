from types import SimpleNamespace
from uuid import uuid4

from app.api import routes


def test_add_memory_returns_created_item(client, monkeypatch):
    mem_id = uuid4()

    def _fake_create_memory(db, tenant_id, payload):
        assert tenant_id == "t1"
        assert payload.content == "hello"
        return SimpleNamespace(
            id=mem_id,
            namespace=payload.namespace,
            content=payload.content,
            meta=payload.meta,
        )

    monkeypatch.setattr(routes, "create_memory", _fake_create_memory)

    resp = client.post(
        "/api/v1/memories",
        json={"namespace": "default", "content": "hello", "meta": {"source": "test"}},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(mem_id)
    assert body["content"] == "hello"
    assert body["meta"] == {"source": "test"}


def test_search_memories_returns_ranked_rows(client, monkeypatch):
    fake_rows = [
        {"id": str(uuid4()), "content": "alpha", "meta": {}, "score": 0.8, "rerank_score": 0.6},
        {"id": str(uuid4()), "content": "beta", "meta": {"tag": "x"}, "score": 0.7, "rerank_score": 0.55},
    ]

    def _fake_search(
        db,
        tenant_id,
        namespace,
        query,
        top_k,
        threshold,
        search_mode,
        rerank_enabled,
        filters=None,
        memory_weight=1.0,
        chunk_weight=0.9,
    ):
        assert tenant_id == "t1"
        assert namespace == "default"
        assert query == "what"
        assert top_k == 2
        assert threshold == 0.0
        assert search_mode == "hybrid"
        assert rerank_enabled is True
        assert memory_weight == 1.0
        assert chunk_weight == 0.9
        return fake_rows

    monkeypatch.setattr(routes, "search_memories", _fake_search)

    resp = client.get("/api/v1/memories/search", params={"namespace": "default", "q": "what", "top_k": 2})
    assert resp.status_code == 200
    assert resp.json() == fake_rows


def test_context_endpoint_builds_context_text(client, monkeypatch):
    fake_rows = [
        {"id": str(uuid4()), "content": "first memory", "meta": {}, "score": 0.9},
        {"id": str(uuid4()), "content": "second memory", "meta": {}, "score": 0.7},
    ]

    monkeypatch.setattr(routes, "search_memories", lambda *args, **kwargs: fake_rows)

    resp = client.post("/api/v1/context", json={"namespace": "default", "prompt": "hello", "top_k": 2})

    assert resp.status_code == 200
    body = resp.json()
    assert "- first memory" in body["context"]
    assert len(body["items"]) == 2
    assert len(body["citations"]) == 2
    assert body["trace_id"] is not None


def test_delete_memory_not_found_returns_404(client, monkeypatch):
    monkeypatch.setattr(routes, "delete_memory", lambda db, tenant_id, memory_id: False)

    resp = client.delete(f"/api/v1/memories/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Memory not found"


def test_delete_memory_ok_returns_deleted_true(client, monkeypatch):
    monkeypatch.setattr(routes, "delete_memory", lambda db, tenant_id, memory_id: True)

    resp = client.delete(f"/api/v1/memories/{uuid4()}")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
