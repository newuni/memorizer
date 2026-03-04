from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.schemas.memory import MemoryCreate
from app.services.embedder import embedder


def create_memory(db: Session, payload: MemoryCreate) -> Memory:
    vec = embedder.embed(payload.content)
    item = Memory(
        tenant_id=payload.tenant_id,
        namespace=payload.namespace,
        content=payload.content,
        meta=payload.meta,
        embedding=vec,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_memory(db: Session, memory_id: str) -> bool:
    item = db.get(Memory, memory_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def search_memories(db: Session, tenant_id: str, namespace: str, query: str, top_k: int = 5):
    qvec = embedder.embed(query)
    sql = text(
        """
        SELECT id, content, meta, 1 - (embedding <=> CAST(:qvec AS vector)) AS score
        FROM memories
        WHERE tenant_id = :tenant_id AND namespace = :namespace
        ORDER BY embedding <=> CAST(:qvec AS vector)
        LIMIT :top_k
        """
    )
    rows = db.execute(sql, {
        "qvec": str(qvec),
        "tenant_id": tenant_id,
        "namespace": namespace,
        "top_k": top_k,
    }).mappings().all()
    return rows
