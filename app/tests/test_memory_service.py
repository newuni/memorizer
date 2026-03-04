from app.services import memory_service as ms


def test_passes_filters_simple_key_value():
    assert ms._passes_filters({"type": "note"}, {"key": "type", "value": "note"}) is True
    assert ms._passes_filters({"type": "note"}, {"key": "type", "value": "fact"}) is False


def test_passes_filters_and_or():
    meta = {"type": "note", "team": "ai", "lang": "es"}
    f_and = {"AND": [{"key": "type", "value": "note"}, {"key": "team", "value": "ai"}]}
    f_or = {"OR": [{"key": "lang", "value": "en"}, {"key": "lang", "value": "es"}]}
    assert ms._passes_filters(meta, f_and) is True
    assert ms._passes_filters(meta, f_or) is True


def test_passes_filters_advanced_types():
    meta = {"title": "Docker deploy guide", "priority": 7, "tags": ["ops", "prod"], "status": "draft"}
    assert ms._passes_filters(meta, {"filterType": "string_contains", "key": "title", "value": "deploy"}) is True
    assert ms._passes_filters(meta, {"filterType": "numeric", "key": "priority", "value": 5, "numericOperator": ">="}) is True
    assert ms._passes_filters(meta, {"filterType": "array_contains", "key": "tags", "value": "ops"}) is True
    assert ms._passes_filters(meta, {"key": "status", "value": "draft", "negate": True}) is False


def test_search_memories_threshold_and_mode(monkeypatch):
    monkeypatch.setattr(ms.embedder, "embed", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        ms,
        "_vector_search_memories",
        lambda db, tenant_id, namespace, qvec, limit: [
            {"id": "1", "content": "m1", "meta": {"type": "note"}, "score": 0.9, "source": "memory"},
            {"id": "2", "content": "m2", "meta": {"type": "fact"}, "score": 0.3, "source": "memory"},
        ],
    )
    monkeypatch.setattr(
        ms,
        "_vector_search_chunks",
        lambda db, tenant_id, namespace, qvec, limit: [
            {"id": "3", "content": "c1", "meta": {"type": "note"}, "score": 0.8, "source": "document_chunk"}
        ],
    )
    monkeypatch.setattr(ms, "rerank", lambda query, rows, top_k: rows[:top_k])

    rows = ms.search_memories(
        db=None,
        tenant_id="t1",
        namespace="default",
        query="hello",
        top_k=2,
        threshold=0.5,
        search_mode="hybrid",
        rerank_enabled=True,
        filters={"key": "type", "value": "note"},
    )

    assert len(rows) == 2
    assert rows[0]["source"] in {"memory", "document_chunk"}
    assert all(r["score"] >= 0.5 for r in rows)


def test_hybrid_weights_affect_ranking_when_no_rerank(monkeypatch):
    monkeypatch.setattr(ms.embedder, "embed", lambda _q: [0.1, 0.2])
    monkeypatch.setattr(
        ms,
        "_vector_search_memories",
        lambda db, tenant_id, namespace, qvec, limit: [
            {"id": "m", "content": "memory", "meta": {}, "score": 0.85, "source": "memory"},
        ],
    )
    monkeypatch.setattr(
        ms,
        "_vector_search_chunks",
        lambda db, tenant_id, namespace, qvec, limit: [
            {"id": "c", "content": "chunk", "meta": {}, "score": 0.9, "source": "document_chunk"},
        ],
    )

    rows = ms.search_memories(
        db=None,
        tenant_id="t1",
        namespace="default",
        query="hello",
        top_k=2,
        search_mode="hybrid",
        rerank_enabled=False,
        memory_weight=1.2,
        chunk_weight=0.7,
    )

    assert rows[0]["source"] == "memory"
    assert rows[0]["score"] > rows[1]["score"]
