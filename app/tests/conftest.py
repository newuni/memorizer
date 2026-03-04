from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.api.deps import AuthContext, get_auth_context
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(tenant_id="t1", key_id="k1")
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
