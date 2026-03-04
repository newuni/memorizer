from __future__ import annotations

from urllib.request import urlopen

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentCreate
from app.services.embedder import embedder


def create_document(db: Session, tenant_id: str, payload: DocumentCreate) -> Document:
    item = Document(
        tenant_id=tenant_id,
        namespace=payload.namespace,
        content_type=payload.content_type,
        title=payload.title,
        text_content=payload.text_content,
        source_url=payload.source_url,
        meta=payload.meta,
        status="queued",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_documents(db: Session, tenant_id: str, namespace: str) -> list[Document]:
    return (
        db.query(Document)
        .filter(Document.tenant_id == tenant_id, Document.namespace == namespace)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document(db: Session, tenant_id: str, doc_id: str) -> Document | None:
    return db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()


def delete_document(db: Session, tenant_id: str, doc_id: str) -> bool:
    doc = get_document(db, tenant_id, doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 60) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    out: list[str] = []
    step = max(1, chunk_size - overlap)
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size].strip()
        if chunk:
            out.append(chunk)
    return out


def _fetch_url_text(url: str) -> str:
    with urlopen(url, timeout=20) as resp:
        raw = resp.read(200_000)
    return raw.decode("utf-8", errors="ignore")


def process_document(db: Session, document_id: str) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        return

    doc.status = "processing"
    db.commit()

    try:
        text_content = doc.text_content or ""
        if doc.content_type == "url":
            if not doc.source_url:
                raise ValueError("source_url is required for url documents")
            text_content = _fetch_url_text(doc.source_url)

        chunks = _chunk_text(text_content)
        db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
        for idx, chunk in enumerate(chunks):
            vec = embedder.embed(chunk)
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    tenant_id=doc.tenant_id,
                    namespace=doc.namespace,
                    position=idx,
                    content=chunk,
                    meta={"document_id": str(doc.id), **(doc.meta or {})},
                    embedding=vec,
                )
            )
        doc.status = "done"
        doc.error = None
        db.commit()
    except Exception as exc:
        doc.status = "failed"
        doc.error = str(exc)
        db.commit()
        raise
