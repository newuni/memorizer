from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api.admin_routes import admin_router
from app.api.routes import router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.admin_service import bootstrap_admin_token, ensure_namespace, ensure_tenant
from app.services.api_key_service import bootstrap_api_key
from app.services.ops_service import get_metrics_text


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.app_env != "test" and settings.bootstrap_api_key:
        db = SessionLocal()
        try:
            ensure_tenant(db, tenant_id=settings.bootstrap_tenant_id, name=settings.bootstrap_tenant_id)
            ensure_namespace(db, tenant_id=settings.bootstrap_tenant_id, namespace="default")
            bootstrap_api_key(
                db,
                tenant_id=settings.bootstrap_tenant_id,
                raw_api_key=settings.bootstrap_api_key,
                name="bootstrap",
            )
            if settings.bootstrap_admin_token:
                bootstrap_admin_token(
                    db,
                    raw_token=settings.bootstrap_admin_token,
                    name="bootstrap-admin",
                    role=settings.bootstrap_admin_role,
                    tenant_id=settings.bootstrap_admin_tenant_id or None,
                )
        finally:
            db.close()
    yield


app = FastAPI(title="memorizer", version="0.5.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    return get_metrics_text()


app.include_router(router)
app.include_router(admin_router)
