import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, Boolean, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=settings.rate_limit_per_minute)
    daily_quota: Mapped[int] = mapped_column(Integer, default=settings.default_daily_quota)
    retention_days: Mapped[int] = mapped_column(Integer, default=settings.default_retention_days)
    purge_after_forget_days: Mapped[int] = mapped_column(Integer, default=settings.default_purge_after_forget_days)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
