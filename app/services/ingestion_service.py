from sqlalchemy.orm import Session

from app.models.ingestion_job import IngestionJob


def create_job(db: Session, tenant_id: str, total_items: int) -> IngestionJob:
    job = IngestionJob(tenant_id=tenant_id, status="queued", total_items=total_items, processed_items=0)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, tenant_id: str, job_id: str) -> IngestionJob | None:
    return db.query(IngestionJob).filter(IngestionJob.id == job_id, IngestionJob.tenant_id == tenant_id).first()
