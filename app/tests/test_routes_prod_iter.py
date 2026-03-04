from uuid import uuid4

from app.api import routes
from app.main import app
from app.services import memory_service


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "memorizer_counter" in r.text


def test_search_invalid_filter_returns_422(client, monkeypatch):
    def _boom(*args, **kwargs):
        raise ValueError("Unsupported filterType: weird")

    monkeypatch.setattr(routes, "search_memories", _boom)
    r = client.get("/api/v1/memories/search", params={"q": "x", "filters": '{"filterType":"weird"}'})
    assert r.status_code == 422


def test_context_includes_citations(client, monkeypatch):
    monkeypatch.setattr(
        routes,
        "search_memories",
        lambda *args, **kwargs: [{"id": str(uuid4()), "content": "a", "meta": {"m": 1}, "score": 0.9, "source": "memory"}],
    )
    r = client.post("/api/v1/context", json={"namespace": "default", "prompt": "hello", "top_k": 1})
    assert r.status_code == 200
    body = r.json()
    assert len(body["citations"]) == 1


def test_memory_filter_validation_numeric_operator():
    memory_service.validate_filters({"filterType": "numeric", "numericOperator": ">"})
