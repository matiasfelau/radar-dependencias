from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    scan_interval_seconds: int = Field(default=43200, ge=1)
    webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


class SettingsUpdateRequest(BaseModel):
    scan_interval_seconds: int | None = Field(default=None, ge=1)
    webhook_url: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None


class TelegramTestResponse(BaseModel):
    ok: bool
    detail: str
