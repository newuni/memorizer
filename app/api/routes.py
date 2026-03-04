from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.memory import MemoryCreate, MemoryOut, SearchResult, ContextRequest, ContextResponse
from app.services.memory_service import create_memory, search_memories, delete_memory

router = APIRouter(prefix="/api/v1", tags=["memorizer"])


@router.post("/memories", response_model=MemoryOut)
def add_memory(payload: MemoryCreate, db: Session = Depends(get_db)):
    item = create_memory(db, payload)
    return MemoryOut.model_validate(item, from_attributes=True)


@router.get("/memories/search", response_model=list[SearchResult])
def search(tenant_id: str, namespace: str = "default", q: str = "", top_k: int = 5, db: Session = Depends(get_db)):
    rows = search_memories(db, tenant_id=tenant_id, namespace=namespace, query=q, top_k=top_k)
    return [SearchResult(**r) for r in rows]


@router.post("/context", response_model=ContextResponse)
def context(payload: ContextRequest, db: Session = Depends(get_db)):
    rows = search_memories(db, tenant_id=payload.tenant_id, namespace=payload.namespace, query=payload.prompt, top_k=payload.top_k)
    items = [SearchResult(**r) for r in rows]
    context_text = "\n\n".join([f"- {x.content}" for x in items])
    return ContextResponse(context=context_text, items=items)


@router.delete("/memories/{memory_id}")
def remove(memory_id: str, db: Session = Depends(get_db)):
    ok = delete_memory(db, memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}
