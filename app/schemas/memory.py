from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    tenant_id: str = Field(..., min_length=1, max_length=100)
    namespace: str = Field(default="default", min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    meta: dict[str, Any] = Field(default_factory=dict)


class MemoryOut(BaseModel):
    id: UUID
    tenant_id: str
    namespace: str
    content: str
    meta: dict[str, Any]


class SearchResult(BaseModel):
    id: UUID
    content: str
    meta: dict[str, Any]
    score: float


class ContextRequest(BaseModel):
    tenant_id: str
    namespace: str = "default"
    prompt: str
    top_k: int = 5


class ContextResponse(BaseModel):
    context: str
    items: list[SearchResult]
