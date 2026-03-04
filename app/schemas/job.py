from uuid import UUID
from pydantic import BaseModel


class JobOut(BaseModel):
    id: UUID
    status: str
    total_items: int
    processed_items: int
    error: str | None = None
