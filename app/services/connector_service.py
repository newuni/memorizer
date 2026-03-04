from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.connector import Connector
from app.schemas.connector import ConnectorCreate


VALID_PROVIDERS = {"github", "web_crawler"}


def create_connector(db: Session, tenant_id: str, payload: ConnectorCreate) -> Connector:
    if payload.provider not in VALID_PROVIDERS:
        raise ValueError("Unsupported connector provider")
    item = Connector(
        tenant_id=tenant_id,
        namespace=payload.namespace,
        provider=payload.provider,
        config=payload.config,
        status="active",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_connectors(db: Session, tenant_id: str, namespace: str) -> list[Connector]:
    return (
        db.query(Connector)
        .filter(Connector.tenant_id == tenant_id, Connector.namespace == namespace)
        .order_by(Connector.created_at.desc())
        .all()
    )


def mark_synced(db: Session, connector_id: str) -> None:
    c = db.get(Connector, connector_id)
    if not c:
        return
    c.last_sync_at = datetime.now(timezone.utc)
    c.error = None
    db.commit()
