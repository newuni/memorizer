from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.document import DocumentChunk
from app.models.memory import Memory


def build_user_profile(db: Session, tenant_id: str, namespace: str) -> tuple[list[str], list[str]]:
    memories = (
        db.query(Memory)
        .filter(Memory.tenant_id == tenant_id, Memory.namespace == namespace)
        .order_by(desc(Memory.updated_at))
        .limit(50)
        .all()
    )

    static_candidates: list[str] = []
    dynamic_candidates: list[str] = []

    for m in memories:
        content = (m.content or "").strip()
        if not content:
            continue
        mtype = str((m.meta or {}).get("type", "")).lower()
        is_static = mtype in {"preference", "fact", "profile"} or any(
            x in content.lower() for x in ["prefers", "likes", "is ", "usually"]
        )
        if is_static:
            static_candidates.append(content)
        else:
            dynamic_candidates.append(content)

    recent_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.tenant_id == tenant_id, DocumentChunk.namespace == namespace)
        .order_by(desc(DocumentChunk.created_at))
        .limit(10)
        .all()
    )
    for c in recent_chunks:
        dynamic_candidates.append(c.content)

    def _uniq(items: list[str], limit: int) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for it in items:
            key = it.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(key)
            if len(out) >= limit:
                break
        return out

    return _uniq(static_candidates, 8), _uniq(dynamic_candidates, 8)
