from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Space Debris Command API"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    environment: str = "dev"

    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/debris"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "debris-media"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    max_requests_per_minute: int = 100
    max_tracking_objects: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
