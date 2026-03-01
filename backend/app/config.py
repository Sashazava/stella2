from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot
    bot_token: str = ""
    app_base_url: str = "http://localhost:8000"
    webhook_secret: str = "dev-secret"

    # Database
    database_url: str = "postgresql+psycopg://stella:stella_secret@localhost:5432/stella"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin_secret"
    minio_server_url: str = "http://localhost:9000"

    # Admin
    admin_telegram_ids: list[int] = []


settings = Settings()
