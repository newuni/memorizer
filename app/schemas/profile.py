from pydantic import BaseModel

from app.schemas.memory import SearchResult


class UserProfileResponse(BaseModel):
    static: list[str]
    dynamic: list[str]
    search_results: list[SearchResult] | None = None
