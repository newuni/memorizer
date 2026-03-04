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
