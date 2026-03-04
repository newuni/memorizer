from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from app.api.routes import router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.api_key_service import bootstrap_api_key
from app.services.ops_service import get_metrics_text

app = FastAPI(title="memorizer", version="0.4.0")


@app.on_event("startup")
def on_startup() -> None:
    if settings.bootstrap_api_key:
        db = SessionLocal()
        try:
            bootstrap_api_key(
                db,
                tenant_id=settings.bootstrap_tenant_id,
                raw_api_key=settings.bootstrap_api_key,
                name="bootstrap",
            )
        finally:
            db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics() -> str:
    return get_metrics_text()


app.include_router(router)
