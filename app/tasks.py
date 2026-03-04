from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

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


@celery_app.task(name="app.tasks.ingest_batch_task", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
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


@celery_app.task(name="app.tasks.process_document_task", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_document_task(document_id: str) -> None:
    db: Session = SessionLocal()
    try:
        process_document(db, document_id=document_id)
    finally:
        db.close()


def _github_urls(repo: str) -> list[str]:
    repo = repo.rstrip("/")
    parsed = urlparse(repo)
    path = parsed.path.strip("/")
    if path.count("/") < 1:
        return [repo]
    owner, name = path.split("/")[:2]
    base = f"https://raw.githubusercontent.com/{owner}/{name}/HEAD"
    return [
        f"{base}/README.md",
        f"{base}/docs/index.md",
        f"{base}/docs/README.md",
    ]


def _discover_sitemap(seed: str) -> list[str]:
    site = f"{urlparse(seed).scheme}://{urlparse(seed).netloc}"
    sitemap = urljoin(site, "/sitemap.xml")
    try:
        with urlopen(sitemap, timeout=15) as resp:
            xml = resp.read(500_000).decode("utf-8", errors="ignore")
        urls = re.findall(r"<loc>(.*?)</loc>", xml)
        return urls[:100]
    except Exception:
        return [seed]


@celery_app.task(name="app.tasks.sync_connector_task", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
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
                urls = _github_urls(repo_url)
        elif connector.provider == "web_crawler":
            seed = cfg.get("seed_url") or (cfg.get("seed_urls") or [None])[0]
            if seed:
                urls = _discover_sitemap(seed)

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
