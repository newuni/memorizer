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
