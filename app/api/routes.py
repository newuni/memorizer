from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context
from app.db.session import get_db
from app.schemas.memory import MemoryCreate, MemoryBatchCreate, MemoryOut, SearchResult, ContextRequest, ContextResponse
from app.services.memory_service import create_memory, create_memories_batch, search_memories, delete_memory

router = APIRouter(prefix="/api/v1", tags=["memorizer"])


@router.post("/memories", response_model=MemoryOut)
def add_memory(
    payload: MemoryCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    item = create_memory(db, tenant_id=auth.tenant_id, payload=payload)
    return MemoryOut.model_validate(item, from_attributes=True)


@router.post("/memories/batch", response_model=list[MemoryOut])
def add_memories_batch(
    payload: MemoryBatchCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    items = create_memories_batch(db, tenant_id=auth.tenant_id, payloads=payload.items)
    return [MemoryOut.model_validate(item, from_attributes=True) for item in items]


@router.get("/memories/search", response_model=list[SearchResult])
def search(
    namespace: str = "default",
    q: str = "",
    top_k: int = 5,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    rows = search_memories(db, tenant_id=auth.tenant_id, namespace=namespace, query=q, top_k=top_k)
    return [SearchResult(**r) for r in rows]


@router.post("/context", response_model=ContextResponse)
def context(
    payload: ContextRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    rows = search_memories(db, tenant_id=auth.tenant_id, namespace=payload.namespace, query=payload.prompt, top_k=payload.top_k)
    items = [SearchResult(**r) for r in rows]
    context_text = "\n\n".join([f"- {x.content}" for x in items])
    return ContextResponse(context=context_text, items=items)


@router.delete("/memories/{memory_id}")
def remove(memory_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = delete_memory(db, tenant_id=auth.tenant_id, memory_id=memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}
