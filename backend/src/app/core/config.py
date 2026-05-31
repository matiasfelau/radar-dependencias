from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Dependency Radar", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    repository_root: str = Field(default="/workspace", alias="REPOSITORY_ROOT")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/dependency_radar",
        alias="DATABASE_URL",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = Field(default=None, alias="TELEGRAM_CHAT_ID")


@lru_cache
def get_settings() -> Settings:
    return Settings()
