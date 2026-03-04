from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.memory import Memory
from app.schemas.memory import MemoryCreate
from app.services.embedder import embedder
from app.services.reranker import rerank

NUMERIC_OPS = {
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}
VALID_FILTER_TYPES = {"equals", "string_contains", "array_contains", "numeric", "exists", "in"}


def validate_filters(filters: dict | None) -> None:
    if not filters:
        return
    if "AND" in filters:
        for x in filters["AND"]:
            validate_filters(x)
        return
    if "OR" in filters:
        for x in filters["OR"]:
            validate_filters(x)
        return
    ftype = filters.get("filterType", "equals")
    if ftype not in VALID_FILTER_TYPES:
        raise ValueError(f"Unsupported filterType: {ftype}")
    if ftype == "numeric":
        op = filters.get("numericOperator", "==")
        if op not in NUMERIC_OPS:
            raise ValueError(f"Unsupported numericOperator: {op}")


def _redact_pii(text: str) -> tuple[str, bool]:
    out = text
    changed = False
    for token in ["@", "+34", "+1"]:
        if token in out:
            changed = True
            out = out.replace(token, "[redacted]")
    return out, changed


def _namespace_ttl(meta: dict) -> datetime | None:
    ttl_days = int(meta.get("ttl_days", 0) or settings.default_namespace_ttl_days)
    if ttl_days <= 0:
        return None
    return datetime.now(UTC).replace(microsecond=0) + timedelta(days=ttl_days)


def create_memory(db: Session, tenant_id: str, payload: MemoryCreate) -> Memory:
    content = payload.content
    pii_redacted = False
    if payload.meta.get("pii_redact", settings.pii_redaction_enabled):
        content, pii_redacted = _redact_pii(content)
    vec = embedder.embed(content)
    item = Memory(
        tenant_id=tenant_id,
        namespace=payload.namespace,
        content=content,
        meta=payload.meta,
        embedding=vec,
        pii_redacted=pii_redacted,
        expires_at=_namespace_ttl(payload.meta),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_memories_batch(db: Session, tenant_id: str, payloads: list[MemoryCreate]) -> list[Memory]:
    return [create_memory(db, tenant_id, payload) for payload in payloads]


def delete_memory(db: Session, tenant_id: str, memory_id: str, hard: bool = False) -> bool:
    item = db.query(Memory).filter(Memory.id == memory_id, Memory.tenant_id == tenant_id).first()
    if not item:
        return False
    if hard:
        db.delete(item)
    else:
        item.is_deleted = True
        item.deleted_at = datetime.now(UTC)
    db.commit()
    return True


def _eval_leaf(meta: dict, flt: dict) -> bool:
    key = flt.get("key")
    value = flt.get("value")
    if key is None:
        return True

    actual = meta.get(key)
    ftype = flt.get("filterType", "equals")

    if ftype == "exists":
        return key in meta
    if ftype == "in":
        vals = value if isinstance(value, list) else []
        return actual in vals
    if ftype == "string_contains":
        return str(value).lower() in str(actual or "").lower()
    if ftype == "array_contains":
        arr = actual if isinstance(actual, list) else []
        return str(value) in [str(x) for x in arr]
    if ftype == "numeric":
        op = flt.get("numericOperator", "==")
        fn = NUMERIC_OPS.get(op, NUMERIC_OPS["=="])
        try:
            return fn(float(actual), float(value))
        except Exception:
            return False

    return str(actual) == str(value)


def _passes_filters(meta: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    if "AND" in filters:
        return all(_passes_filters(meta, x) for x in filters["AND"])
    if "OR" in filters:
        return any(_passes_filters(meta, x) for x in filters["OR"])
    matched = _eval_leaf(meta, filters)
    return (not matched) if filters.get("negate") is True else matched


def _vector_search_memories(db: Session, tenant_id: str, namespace: str, qvec: list[float], limit: int):
    sql = text(
        """
        SELECT id, content, meta, 1 - (embedding <=> CAST(:qvec AS vector)) AS score
        FROM memories
        WHERE tenant_id = :tenant_id AND namespace = :namespace
          AND is_deleted = false
          AND (expires_at IS NULL OR expires_at > now())
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :top_k
        """
    )
    rows = db.execute(sql, {"qvec": str(qvec), "tenant_id": tenant_id, "namespace": namespace, "top_k": limit}).mappings().all()
    return [{**dict(r), "source": "memory"} for r in rows]


def _vector_search_chunks(db: Session, tenant_id: str, namespace: str, qvec: list[float], limit: int):
    sql = text(
        """
        SELECT c.id, c.content, c.meta, 1 - (c.embedding <=> CAST(:qvec AS vector)) AS score
        FROM document_chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.tenant_id = :tenant_id AND c.namespace = :namespace AND d.is_deleted = false
        ORDER BY c.embedding <=> CAST(:qvec AS vector)
        LIMIT :top_k
        """
    )
    rows = db.execute(sql, {"qvec": str(qvec), "tenant_id": tenant_id, "namespace": namespace, "top_k": limit}).mappings().all()
    return [{**dict(r), "source": "document_chunk"} for r in rows]


def _apply_hybrid_weights(rows: list[dict], memory_weight: float, chunk_weight: float) -> list[dict]:
    out: list[dict] = []
    for r in rows:
        w = memory_weight if r.get("source") == "memory" else chunk_weight
        row = dict(r)
        row["raw_score"] = float(row.get("score", 0.0))
        row["score"] = float(row.get("score", 0.0)) * float(w)
        row["source_weight"] = float(w)
        out.append(row)
    return out


def _mmr(rows: list[dict], top_k: int, lambda_mult: float = 0.75) -> list[dict]:
    if len(rows) <= top_k:
        return rows
    selected: list[dict] = []
    remaining = [dict(r) for r in rows]
    remaining.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    while remaining and len(selected) < top_k:
        if not selected:
            selected.append(remaining.pop(0))
            continue
        best_idx = 0
        best_score = -1e9
        for idx, cand in enumerate(remaining):
            sim = float(cand.get("score", 0.0))
            max_novelty_penalty = max(
                1.0 if (cand.get("meta") or {}).get("document_id") == (s.get("meta") or {}).get("document_id") else 0.0
                for s in selected
            )
            mmr_score = lambda_mult * sim - (1 - lambda_mult) * max_novelty_penalty
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
        selected.append(remaining.pop(best_idx))
    return selected


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
    memory_weight: float | None = None,
    chunk_weight: float | None = None,
    use_mmr: bool = True,
):
    validate_filters(filters)
    qvec = embedder.embed(query)
    candidate_pool = max(top_k * 3, settings.rerank_candidate_pool)

    memory_rows = _vector_search_memories(db, tenant_id, namespace, qvec, candidate_pool)
    chunk_rows = _vector_search_chunks(db, tenant_id, namespace, qvec, candidate_pool) if search_mode == "hybrid" else []

    mw = settings.hybrid_memory_weight if memory_weight is None else memory_weight
    cw = settings.hybrid_chunk_weight if chunk_weight is None else chunk_weight

    rows = _apply_hybrid_weights(memory_rows + chunk_rows, mw, cw)
    rows = [r for r in rows if float(r.get("score", 0.0)) >= threshold and _passes_filters(r.get("meta") or {}, filters)]

    if rerank_enabled:
        rows = rerank(query=query, rows=[dict(r) for r in rows], top_k=min(len(rows), candidate_pool))
    else:
        rows.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)

    rows = _mmr(rows, top_k=top_k) if use_mmr else rows[:top_k]
    return rows[:top_k]
