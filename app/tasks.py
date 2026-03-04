from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.connector import Connector
from app.models.ingestion_job import IngestionJob
from app.schemas.document import DocumentCreate
from app.schemas.memory import MemoryCreate
from app.services.connector_service import mark_synced
from app.services.document_service import create_document, process_document
from app.services.memory_service import create_memories_batch
from app.worker import celery_app


@celery_app.task(name="app.tasks.ingest_batch_task")
def ingest_batch_task(job_id: str, tenant_id: str, items: list[dict]) -> None:
    db: Session = SessionLocal()
    try:
        job = db.get(IngestionJob, job_id)
        if not job:
            return
        job.status = "running"
        db.commit()

        payloads = [MemoryCreate(**x) for x in items]
        created = create_memories_batch(db, tenant_id=tenant_id, payloads=payloads)

        job.processed_items = len(created)
        job.total_items = len(items)
        job.status = "done"
        db.commit()
    except Exception as exc:
        job = db.get(IngestionJob, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)
            db.commit()
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_document_task")
def process_document_task(document_id: str) -> None:
    db: Session = SessionLocal()
    try:
        process_document(db, document_id=document_id)
    finally:
        db.close()


@celery_app.task(name="app.tasks.sync_connector_task")
def sync_connector_task(connector_id: str, tenant_id: str) -> int:
    db: Session = SessionLocal()
    try:
        connector = db.get(Connector, connector_id)
        if not connector:
            return 0

        cfg = connector.config or {}
        urls: list[str] = []
        if connector.provider == "github":
            repo_url = cfg.get("repo_url")
            if repo_url:
                urls = [repo_url]
        elif connector.provider == "web_crawler":
            urls = list(cfg.get("seed_urls", []))

        created = 0
        for url in urls:
            doc = create_document(
                db,
                tenant_id=tenant_id,
                payload=DocumentCreate(
                    namespace=connector.namespace,
                    content_type="url",
                    source_url=url,
                    meta={"connector_id": str(connector.id), "provider": connector.provider},
                ),
            )
            process_document_task.delay(str(doc.id))
            created += 1

        mark_synced(db, connector_id)
        return created
    finally:
        db.close()
