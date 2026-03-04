from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.deps import get_auth_context
from app.core.security import hash_api_key


class _FakeQuery:
    def __init__(self, key_obj):
        self.key_obj = key_obj

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.key_obj


class _FakeDB:
    def __init__(self, key_obj):
        self.key_obj = key_obj

    def query(self, _model):
        return _FakeQuery(self.key_obj)


def test_get_auth_context_missing_key_raises_401():
    db = _FakeDB(None)

    with pytest.raises(HTTPException) as exc:
        get_auth_context(db=db, x_api_key=None)

    assert exc.value.status_code == 401
    assert exc.value.detail == "Missing X-API-Key"


def test_get_auth_context_invalid_key_raises_401():
    db = _FakeDB(None)

    with pytest.raises(HTTPException) as exc:
        get_auth_context(db=db, x_api_key="wrong")

    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid API key"


def test_get_auth_context_returns_tenant_and_key_id():
    key_obj = SimpleNamespace(
        id="kid-1",
        tenant_id="tenant-42",
        key_hash=hash_api_key("secret"),
        is_active=True,
        rate_limit_per_minute=None,
        daily_quota=None,
    )
    db = _FakeDB(key_obj)

    ctx = get_auth_context(db=db, x_api_key="secret")

    assert ctx.tenant_id == "tenant-42"
    assert ctx.key_id == "kid-1"
