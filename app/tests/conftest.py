from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.admin_deps import AdminAuthContext, get_admin_auth_context
from app.api.deps import AuthContext, get_auth_context
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(tenant_id="t1", key_id="k1")
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(tenant_id="t1", key_id="k1")
    app.dependency_overrides[get_admin_auth_context] = lambda: AdminAuthContext(
        token_id="adm1",
        role="owner",
        tenant_id=None,
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
