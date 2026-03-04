from uuid import uuid4

from app.api import routes


def test_search_passes_custom_weights_and_filters(client, monkeypatch):
    seen = {"kwargs": None}

    def _fake_search(**kwargs):
        seen["kwargs"] = kwargs
        return [{"id": str(uuid4()), "content": "x", "meta": {"type": "note"}, "score": 0.88, "source": "memory"}]

    monkeypatch.setattr(routes, "search_memories", lambda *args, **kwargs: _fake_search(**kwargs))

    resp = client.get(
        "/api/v1/memories/search",
        params={
            "namespace": "default",
            "q": "hello",
            "top_k": 3,
            "threshold": 0.5,
            "search_mode": "hybrid",
            "rerank": "false",
            "memory_weight": 1.3,
            "chunk_weight": 0.6,
            "filters": '{"key":"type","value":"note"}',
        },
    )

    assert resp.status_code == 200
    assert seen["kwargs"]["memory_weight"] == 1.3
    assert seen["kwargs"]["chunk_weight"] == 0.6
    assert seen["kwargs"]["filters"] == {"key": "type", "value": "note"}
