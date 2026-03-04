from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ConnectorCreate(BaseModel):
    namespace: str = Field(default="default", min_length=1, max_length=100)
    provider: str = Field(pattern="^(github|web_crawler)$")
    config: dict[str, Any] = Field(default_factory=dict)


class ConnectorOut(BaseModel):
    id: UUID
    namespace: str
    provider: str
    config: dict[str, Any]
    status: str
    error: str | None = None


class ConnectorSyncResponse(BaseModel):
    queued_documents: int
