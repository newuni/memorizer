import json
import uuid

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
from app.schemas.connector import ConnectorCreate, ConnectorOut, ConnectorSyncResponse
from app.schemas.document import DocumentCreate, DocumentListResponse, DocumentOut, DocumentProcessResponse
from app.schemas.job import JobOut
from app.schemas.memory import (
    ContextRequest,
    ContextResponse,
    MemoryBatchCreate,
    MemoryCreate,
    MemoryOut,
    SearchResult,
)
from app.schemas.profile import UserProfileResponse
from app.services.api_key_service import create_api_key, list_api_keys, revoke_api_key
from app.services.audit_service import log_audit
from app.services.connector_service import create_connector, list_connectors
from app.services.document_service import create_document, delete_document, get_document, list_documents
from app.services.ingestion_service import create_job, get_job
from app.services.memory_service import (
    create_memories_batch,
    create_memory,
    delete_memory,
    search_memories,
)
from app.services.profile_service import build_user_profile
from app.tasks import ingest_batch_task, process_document_task, sync_connector_task

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
    threshold: float = 0.0,
    search_mode: str = "hybrid",
    rerank: bool = True,
    filters: str | None = None,
    memory_weight: float = 1.0,
    chunk_weight: float = 0.9,
    use_mmr: bool = True,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    parsed_filters = json.loads(filters) if filters else None
    try:
        rows = search_memories(
            db,
            tenant_id=auth.tenant_id,
            namespace=namespace,
            query=q,
            top_k=top_k,
            threshold=threshold,
            search_mode=search_mode,
            rerank_enabled=rerank,
            filters=parsed_filters,
            memory_weight=memory_weight,
            chunk_weight=chunk_weight,
            use_mmr=use_mmr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
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
        threshold=payload.threshold,
        search_mode=payload.search_mode,
        rerank_enabled=payload.rerank,
        memory_weight=payload.memory_weight,
        chunk_weight=payload.chunk_weight,
        use_mmr=payload.use_mmr,
    )
    items = [SearchResult(**r) for r in rows]
    context_text = "\n\n".join([f"- {x.content}" for x in items])
    citations = []
    if payload.include_citations:
        for i, x in enumerate(items, start=1):
            citations.append({"index": i, "id": str(x.id), "source": x.source, "meta": x.meta})
            context_text += f" [{i}]"
    return ContextResponse(context=context_text, items=items, citations=citations, trace_id=str(uuid.uuid4()))


@router.get("/profile", response_model=UserProfileResponse)
def profile(
    namespace: str = "default",
    q: str | None = None,
    top_k: int = 5,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    static, dynamic = build_user_profile(db, tenant_id=auth.tenant_id, namespace=namespace)
    if q:
        rows = search_memories(
            db,
            tenant_id=auth.tenant_id,
            namespace=namespace,
            query=q,
            top_k=top_k,
            search_mode="hybrid",
        )
        return UserProfileResponse(static=static, dynamic=dynamic, search_results=[SearchResult(**r) for r in rows])
    return UserProfileResponse(static=static, dynamic=dynamic, search_results=None)


@router.delete("/memories/{memory_id}")
def remove(memory_id: str, hard: bool = False, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = delete_memory(db, tenant_id=auth.tenant_id, memory_id=memory_id, hard=hard)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    log_audit(db, auth.tenant_id, auth.key_id, "memory.hard_delete" if hard else "memory.delete", "memory", memory_id)
    return {"deleted": True, "hard": hard}


@router.post("/memories/{memory_id}/forget")
def forget(memory_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = delete_memory(db, tenant_id=auth.tenant_id, memory_id=memory_id, hard=False)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    log_audit(db, auth.tenant_id, auth.key_id, "memory.forget", "memory", memory_id)
    return {"forgotten": True}


@router.get("/tenants/export")
def export_tenant(namespace: str = "default", db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    rows = search_memories(db, tenant_id=auth.tenant_id, namespace=namespace, query="*", top_k=500, rerank_enabled=False)
    log_audit(db, auth.tenant_id, auth.key_id, "tenant.export", "tenant", auth.tenant_id, {"namespace": namespace})
    return {"tenant_id": auth.tenant_id, "namespace": namespace, "items": rows}


@router.post("/documents", response_model=DocumentOut)
def post_document(payload: DocumentCreate, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    doc = create_document(db, tenant_id=auth.tenant_id, payload=payload)
    process_document_task.delay(str(doc.id))
    return DocumentOut.model_validate(doc, from_attributes=True)


@router.get("/documents", response_model=DocumentListResponse)
def get_documents(namespace: str = "default", db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    docs = list_documents(db, tenant_id=auth.tenant_id, namespace=namespace)
    return DocumentListResponse(items=[DocumentOut.model_validate(d, from_attributes=True) for d in docs])


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document_by_id(doc_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    doc = get_document(db, tenant_id=auth.tenant_id, doc_id=doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc, from_attributes=True)


@router.post("/documents/{doc_id}/process", response_model=DocumentProcessResponse)
def process_document_endpoint(doc_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    doc = get_document(db, tenant_id=auth.tenant_id, doc_id=doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    process_document_task.delay(doc_id)
    return DocumentProcessResponse(queued=True, document_id=doc.id)


@router.delete("/documents/{doc_id}")
def delete_document_endpoint(doc_id: str, hard: bool = False, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = delete_document(db, tenant_id=auth.tenant_id, doc_id=doc_id, hard=hard)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "hard": hard}


@router.post("/connectors", response_model=ConnectorOut)
def post_connector(payload: ConnectorCreate, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    c = create_connector(db, tenant_id=auth.tenant_id, payload=payload)
    return ConnectorOut.model_validate(c, from_attributes=True)


@router.get("/connectors", response_model=list[ConnectorOut])
def get_connectors(namespace: str = "default", db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    rows = list_connectors(db, tenant_id=auth.tenant_id, namespace=namespace)
    return [ConnectorOut.model_validate(c, from_attributes=True) for c in rows]


@router.post("/connectors/{connector_id}/sync", response_model=ConnectorSyncResponse)
def sync_connector(connector_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    task = sync_connector_task.delay(connector_id, auth.tenant_id)
    log_audit(db, auth.tenant_id, auth.key_id, "connector.sync", "connector", connector_id)
    return ConnectorSyncResponse(queued_documents=int(task.id is not None))


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
    log_audit(db, auth.tenant_id, auth.key_id, "apikey.create", "api_key", str(key.id), {"name": payload.name})
    return ApiKeyCreateResponse(id=key.id, name=key.name, api_key=raw)


@router.delete("/api-keys/{key_id}", response_model=ApiKeyRevokeResponse)
def delete_api_key(key_id: str, db: Session = Depends(get_db), auth: AuthContext = Depends(get_auth_context)):
    ok = revoke_api_key(db, tenant_id=auth.tenant_id, key_id=key_id)
    if not ok:
        raise HTTPException(status_code=404, detail="API key not found")
    log_audit(db, auth.tenant_id, auth.key_id, "apikey.revoke", "api_key", key_id)
    return ApiKeyRevokeResponse(revoked=True)
