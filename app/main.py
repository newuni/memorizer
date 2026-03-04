from fastapi import FastAPI

from app.api.routes import router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.api_key_service import bootstrap_api_key

app = FastAPI(title="memorizer", version="0.3.0")


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


app.include_router(router)
