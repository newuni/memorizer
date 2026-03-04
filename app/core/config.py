from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://memorizer:memorizer@localhost:5432/memorizer"
    embedding_dim: int = 384
    embedding_provider: str = "local"  # local | gemini
    local_embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    gemini_api_key: str = ""
    gemini_embed_model: str = "models/text-embedding-004"
    bootstrap_api_key: str = "dev-secret-change-me"
    bootstrap_tenant_id: str = "default"

    rerank_enabled: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_candidate_pool: int = 25

    hybrid_memory_weight: float = 1.0
    hybrid_chunk_weight: float = 0.9

    redis_url: str = "redis://redis:6379/0"
    app_env: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
