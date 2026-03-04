from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context
from app.db.session import get_db
from app.schemas.api_key import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyOut,
    ApiKeyRevokeResponse,
)
from app.schemas.job import JobOut
from app.schemas.memory import (
    ContextRequest,
    ContextResponse,
    MemoryBatchCreate,
    MemoryCreate,
    MemoryOut,
    SearchResult,
)
from app.services.api_key_service import create_api_key, list_api_keys, revoke_api_key
from app.services.ingestion_service import create_job, get_job
from app.services.memory_service import (
    create_memories_batch,
    create_memory,
    delete_memory,
    search_memories,
)
from app.tasks import ingest_batch_task

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


@router.post("/memories/batch/async", response_model=JobOut)
def add_memories_batch_async(
    payload: MemoryBatchCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    job = create_job(db, tenant_id=auth.tenant_id, total_items=len(payload.items))
    ingest_batch_task.delay(str(job.id), auth.tenant_id, [x.model_dump() for x in payload.items])
    return JobOut.model_validate(job, from_attributes=True)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_ingestion_job(job_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    job = get_job(db, tenant_id=auth.tenant_id, job_id=job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut.model_validate(job, from_attributes=True)


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
    rows = search_memories(
        db,
        tenant_id=auth.tenant_id,
        namespace=payload.namespace,
        query=payload.prompt,
        top_k=payload.top_k,
    )
    items = [SearchResult(**r) for r in rows]
    context_text = "\n\n".join([f"- {x.content}" for x in items])
    return ContextResponse(context=context_text, items=items)


@router.delete("/memories/{memory_id}")
def remove(memory_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = delete_memory(db, tenant_id=auth.tenant_id, memory_id=memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}


@router.get("/api-keys", response_model=list[ApiKeyOut])
def get_api_keys(db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    keys = list_api_keys(db, tenant_id=auth.tenant_id)
    return [ApiKeyOut.model_validate(k, from_attributes=True) for k in keys]


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
def post_api_key(
    payload: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    key, raw = create_api_key(db, tenant_id=auth.tenant_id, name=payload.name)
    return ApiKeyCreateResponse(id=key.id, name=key.name, api_key=raw)


@router.delete("/api-keys/{key_id}", response_model=ApiKeyRevokeResponse)
def delete_api_key(key_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = revoke_api_key(db, tenant_id=auth.tenant_id, key_id=key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyRevokeResponse(revoked=True)
