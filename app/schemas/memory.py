from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    namespace: str = Field(default="default", min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    meta: dict[str, Any] = Field(default_factory=dict)


class MemoryBatchCreate(BaseModel):
    items: list[MemoryCreate] = Field(default_factory=list, min_length=1, max_length=200)


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
    source: str = "memory"
    rerank_score: float | None = None


class ContextRequest(BaseModel):
    namespace: str = "default"
    prompt: str
    top_k: int = 5
    threshold: float = 0.0
    search_mode: str = "hybrid"
    rerank: bool = True


class ContextResponse(BaseModel):
    context: str
    items: list[SearchResult]
