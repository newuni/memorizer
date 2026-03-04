from uuid import UUID
from pydantic import BaseModel, Field


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(default="default", min_length=1, max_length=120)


class ApiKeyOut(BaseModel):
    id: UUID
    name: str
    is_active: bool


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    name: str
    api_key: str


class ApiKeyRevokeResponse(BaseModel):
    revoked: bool
