from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.request import urlopen

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentCreate
from app.services.embedder import embedder


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.out.append(data.strip())


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


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
        .filter(Document.tenant_id == tenant_id, Document.namespace == namespace, Document.is_deleted.is_(False))
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document(db: Session, tenant_id: str, doc_id: str) -> Document | None:
    return db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id, Document.is_deleted.is_(False)).first()


def delete_document(db: Session, tenant_id: str, doc_id: str, hard: bool = False) -> bool:
    doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == tenant_id).first()
    if not doc:
        return False
    if hard:
        db.delete(doc)
    else:
        doc.is_deleted = True
        doc.deleted_at = datetime.now(UTC)
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
        raw = resp.read(1_500_000)
    text = raw.decode("utf-8", errors="ignore")
    if "<html" in text.lower():
        parser = _HTMLText()
        parser.feed(text)
        return "\n".join(parser.out)
    return text


def _extract_pdf_text(raw: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
        import io

        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return raw.decode("utf-8", errors="ignore")


def _parse_document_content(doc: Document) -> str:
    if doc.content_type == "text":
        return doc.text_content or ""
    if doc.content_type == "url":
        if not doc.source_url:
            raise ValueError("source_url is required for url documents")
        return _fetch_url_text(doc.source_url)
    if doc.content_type == "pdf":
        if not doc.source_url:
            return doc.text_content or ""
        with urlopen(doc.source_url, timeout=20) as resp:
            raw = resp.read(4_000_000)
        return _extract_pdf_text(raw)
    if doc.content_type in {"markdown", "md", "html"}:
        text = doc.text_content or ""
        if doc.content_type == "html":
            parser = _HTMLText()
            parser.feed(text)
            return "\n".join(parser.out)
        return re.sub(r"[`#>*_\-]", " ", text)
    return doc.text_content or ""


def process_document(db: Session, document_id: str) -> None:
    doc = db.get(Document, document_id)
    if not doc:
        return

    doc.status = "processing"
    doc.attempts = int(doc.attempts or 0) + 1
    db.commit()

    try:
        text_content = _parse_document_content(doc)
        doc.content_hash = _sha256(text_content)
        # dedup by tenant + namespace + content_hash
        prev = (
            db.query(Document)
            .filter(
                Document.id != doc.id,
                Document.tenant_id == doc.tenant_id,
                Document.namespace == doc.namespace,
                Document.content_hash == doc.content_hash,
                Document.is_deleted.is_(False),
            )
            .first()
        )
        if prev:
            doc.status = "done"
            doc.meta = {**(doc.meta or {}), "dedup_of": str(prev.id)}
            db.commit()
            return

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
        doc.error = str(exc)
        if int(doc.attempts or 0) < int(doc.max_retries or 3):
            doc.status = "queued"
        else:
            doc.status = "failed"
        db.commit()
        raise
