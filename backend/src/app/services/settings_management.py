from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import Setting


def upsert_setting(db: Session, key: str, value: str) -> None:
    row = db.scalar(select(Setting).where(Setting.key == key))
    if row is None:
        db.add(Setting(key=key, value=value))
        return
    row.value = value


def delete_setting(db: Session, key: str) -> None:
    row = db.scalar(select(Setting).where(Setting.key == key))
    if row is not None:
        db.delete(row)
