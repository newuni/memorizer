from dataclasses import dataclass

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.security import hash_api_key
from app.db.session import get_db
from app.models.api_key import ApiKey


@dataclass
class AuthContext:
    tenant_id: str
    key_id: str


def get_auth_context(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> AuthContext:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    hashed = hash_api_key(x_api_key)
    key = db.query(ApiKey).filter(ApiKey.key_hash == hashed, ApiKey.is_active.is_(True)).first()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return AuthContext(tenant_id=key.tenant_id, key_id=str(key.id))
