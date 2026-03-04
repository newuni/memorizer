from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ingestion_job import IngestionJob
from app.schemas.memory import MemoryCreate
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
