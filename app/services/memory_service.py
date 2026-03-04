from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
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


def search_memories(db: Session, tenant_id: str, namespace: str, query: str, top_k: int = 5):
    qvec = embedder.embed(query)
    candidate_pool = max(top_k, settings.rerank_candidate_pool)
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
        {
            "qvec": str(qvec),
            "tenant_id": tenant_id,
            "namespace": namespace,
            "top_k": candidate_pool,
        },
    ).mappings().all()
    reranked = rerank(query=query, rows=[dict(r) for r in rows], top_k=top_k)
    return reranked
