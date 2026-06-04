from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gee_service_account_key: str = "./secrets/gee-service-account.json"
    gee_service_account_email: str = ""
    gee_project: str = "907232950083"
    # Base64-encoded ~/.config/earthengine/credentials — set in Render env vars
    gee_credentials_b64: str = ""
    groq_api_key: str = ""
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://chronos:chronos@localhost:5432/chronos"
    wandb_api_key: str = ""
    sentry_dsn: str = ""
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    cache_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days
    tile_cache_ttl_seconds: int = 60 * 60 * 24 * 7  # 7 days


settings = Settings()
