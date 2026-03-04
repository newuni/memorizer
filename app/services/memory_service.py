from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import DocumentChunk
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate
from app.services.embedder import embedder
from app.services.reranker import rerank


def create_memory(db: Session, tenant_id: str, payload: MemoryCreate) -> Memory:
    vec = embedder.embed(payload.content)
    item = Memory(
        tenant_id=tenant_id,
        namespace=payload.namespace,
        content=payload.content,
        meta=payload.meta,
        embedding=vec,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_memories_batch(db: Session, tenant_id: str, payloads: list[MemoryCreate]) -> list[Memory]:
    items: list[Memory] = []
    for payload in payloads:
        vec = embedder.embed(payload.content)
        items.append(
            Memory(
                tenant_id=tenant_id,
                namespace=payload.namespace,
                content=payload.content,
                meta=payload.meta,
                embedding=vec,
            )
        )
    db.add_all(items)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


def delete_memory(db: Session, tenant_id: str, memory_id: str) -> bool:
    item = db.query(Memory).filter(Memory.id == memory_id, Memory.tenant_id == tenant_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def _passes_filters(meta: dict, filters: dict | None) -> bool:
    if not filters:
        return True

    if "AND" in filters:
        return all(_passes_filters(meta, x) for x in filters["AND"])
    if "OR" in filters:
        return any(_passes_filters(meta, x) for x in filters["OR"])

    key = filters.get("key")
    value = filters.get("value")
    if key is None:
        return True
    return str(meta.get(key)) == str(value)


def _vector_search_memories(db: Session, tenant_id: str, namespace: str, qvec: list[float], limit: int):
    sql = text(
        """
        SELECT id, content, meta, 1 - (embedding <=> CAST(:qvec AS vector)) AS score
        FROM memories
        WHERE tenant_id = :tenant_id AND namespace = :namespace
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :top_k
        """
    )
    rows = db.execute(
        sql,
        {"qvec": str(qvec), "tenant_id": tenant_id, "namespace": namespace, "top_k": limit},
    ).mappings().all()
    return [{**dict(r), "source": "memory"} for r in rows]


def _vector_search_chunks(db: Session, tenant_id: str, namespace: str, qvec: list[float], limit: int):
    sql = text(
        """
        SELECT id, content, meta, 1 - (embedding <=> CAST(:qvec AS vector)) AS score
        FROM document_chunks
        WHERE tenant_id = :tenant_id AND namespace = :namespace
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :top_k
        """
    )
    rows = db.execute(
        sql,
        {"qvec": str(qvec), "tenant_id": tenant_id, "namespace": namespace, "top_k": limit},
    ).mappings().all()
    return [{**dict(r), "source": "document_chunk"} for r in rows]


def search_memories(
    db: Session,
    tenant_id: str,
    namespace: str,
    query: str,
    top_k: int = 5,
    threshold: float = 0.0,
    search_mode: str = "hybrid",
    rerank_enabled: bool = True,
    filters: dict | None = None,
):
    qvec = embedder.embed(query)
    candidate_pool = max(top_k, settings.rerank_candidate_pool)

    memory_rows = _vector_search_memories(db, tenant_id, namespace, qvec, candidate_pool)
    chunk_rows = _vector_search_chunks(db, tenant_id, namespace, qvec, candidate_pool) if search_mode == "hybrid" else []

    rows = memory_rows + chunk_rows
    rows = [r for r in rows if float(r.get("score", 0.0)) >= threshold]
    rows = [r for r in rows if _passes_filters(r.get("meta") or {}, filters)]

    if rerank_enabled:
        rows = rerank(query=query, rows=[dict(r) for r in rows], top_k=top_k)
    else:
        rows.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        rows = rows[:top_k]

    return rows
