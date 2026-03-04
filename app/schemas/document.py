from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCreate(BaseModel):
    namespace: str = Field(default="default", min_length=1, max_length=100)
    content_type: str = Field(default="text")  # text|url
    title: str | None = None
    text_content: str | None = None
    source_url: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class DocumentOut(BaseModel):
    id: UUID
    namespace: str
    content_type: str
    title: str | None = None
    text_content: str | None = None
    source_url: str | None = None
    meta: dict[str, Any]
    status: str
    error: str | None = None


class DocumentListResponse(BaseModel):
    items: list[DocumentOut]


class DocumentProcessResponse(BaseModel):
    queued: bool
    document_id: UUID
