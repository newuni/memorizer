from sqlalchemy.orm import Session

from app.core.security import hash_api_key, generate_api_key
from app.models.api_key import ApiKey


def create_api_key(db: Session, tenant_id: str, name: str = "default") -> tuple[ApiKey, str]:
    raw = generate_api_key()
    entity = ApiKey(tenant_id=tenant_id, name=name, key_hash=hash_api_key(raw), is_active=True)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity, raw


def list_api_keys(db: Session, tenant_id: str) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == tenant_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


def revoke_api_key(db: Session, tenant_id: str, key_id: str) -> bool:
    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.tenant_id == tenant_id).first()
    if not key:
        return False
    key.is_active = False
    db.commit()
    return True


def bootstrap_api_key(db: Session, tenant_id: str, raw_api_key: str, name: str = "bootstrap") -> ApiKey:
    hashed = hash_api_key(raw_api_key)
    existing = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            db.refresh(existing)
        return existing

    entity = ApiKey(tenant_id=tenant_id, name=name, key_hash=hashed, is_active=True)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity
