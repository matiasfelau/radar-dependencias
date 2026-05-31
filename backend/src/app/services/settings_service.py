from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.setting import Setting


def get_setting_value(db: Session, key: str, default: str | None = None) -> str | None:
    value = db.scalar(select(Setting.value).where(Setting.key == key))
    return value if value is not None else default


def get_scan_interval_seconds(db: Session, default: int = 43200) -> int:
    raw_value = get_setting_value(db, "scan_interval_seconds")
    if raw_value is None:
        return default

    try:
        parsed = int(raw_value)
    except ValueError:
        return default

    return parsed if parsed > 0 else default


def get_webhook_url(db: Session) -> str | None:
    return get_setting_value(db, "webhook_url")


def get_telegram_bot_token(db: Session) -> str | None:
    db_value = get_setting_value(db, "telegram_bot_token")
    if db_value and db_value.strip():
        return db_value.strip()
    env_value = get_settings().telegram_bot_token
    return env_value.strip() if env_value and env_value.strip() else None


def get_telegram_chat_id(db: Session) -> str | None:
    db_value = get_setting_value(db, "telegram_chat_id")
    if db_value and db_value.strip():
        return db_value.strip()
    env_value = get_settings().telegram_chat_id
    return env_value.strip() if env_value and env_value.strip() else None
