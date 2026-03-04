from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://memorizer:memorizer@localhost:5432/memorizer"
    embedding_dim: int = 384
    app_env: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
