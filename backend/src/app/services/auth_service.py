from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime
from typing import Final

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services.settings_management import delete_setting, upsert_setting

logger = logging.getLogger(__name__)

PBKDF2_ITERATIONS: Final = 390_000
DEFAULT_ADMIN_USERNAME: Final = "admin"
DEFAULT_ADMIN_PERMISSIONS: Final = ["view_dashboard", "manage_projects", "manage_settings", "manage_users", "run_scans"]
ADMIN_TEMP_PASSWORD_KEY: Final = "admin_seed_temp_password"


def normalize_permissions(permissions: list[str]) -> str:
    cleaned = sorted({permission.strip() for permission in permissions if permission.strip()})
    return ",".join(cleaned)


def parse_permissions(raw_permissions: str) -> list[str]:
    if not raw_permissions.strip():
        return []
    return [permission for permission in (part.strip() for part in raw_permissions.split(",")) if permission]


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt_bytes = salt or secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_bytes.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
      algorithm, iterations_text, salt_hex, hash_hex = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        iterations = int(iterations_text)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(derived, expected_hash)


def user_to_response(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "permissions": parse_permissions(user.permissions),
        "must_change_password": user.must_change_password,
    }


def user_summary_to_response(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "permissions": parse_permissions(user.permissions),
        "must_change_password": user.must_change_password,
        "created_at": user.created_at.isoformat() if isinstance(user.created_at, datetime) else datetime.now(UTC).isoformat(),
    }


def seed_admin_user(db: Session) -> None:
    existing_admin = db.scalar(select(User).where(User.username == DEFAULT_ADMIN_USERNAME))
    if existing_admin is not None:
        if existing_admin.must_change_password:
            temp_password = _get_setting_value(db, ADMIN_TEMP_PASSWORD_KEY)
            if not temp_password:
                temp_password = secrets.token_urlsafe(12)
                upsert_setting(db, ADMIN_TEMP_PASSWORD_KEY, temp_password)
            existing_admin.password_hash = hash_password(temp_password)
            db.commit()
        return

    temp_password = secrets.token_urlsafe(12)
    admin_user = User(
        username=DEFAULT_ADMIN_USERNAME,
        password_hash=hash_password(temp_password),
        is_admin=True,
        permissions=normalize_permissions(DEFAULT_ADMIN_PERMISSIONS),
        must_change_password=True,
    )
    db.add(admin_user)
    db.flush()
    upsert_setting(db, ADMIN_TEMP_PASSWORD_KEY, temp_password)
    db.commit()


def announce_admin_seed_password(db: Session) -> None:
    admin_user = db.scalar(select(User).where(User.username == DEFAULT_ADMIN_USERNAME))
    if admin_user is None or not admin_user.must_change_password:
        return

    temp_password = _get_setting_value(db, ADMIN_TEMP_PASSWORD_KEY)
    if not temp_password:
        return

    message = f"Default admin credentials -> username={DEFAULT_ADMIN_USERNAME} password={temp_password}"
    print(message, flush=True)
    logger.warning(message)


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username.strip()))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return user


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token=token, user_id=user.id))
    db.commit()
    return token


def revoke_session(db: Session, token: str) -> None:
    session = db.scalar(select(AuthSession).where(AuthSession.token == token))
    if session is not None:
        db.delete(session)
        db.commit()


def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")

    session = db.scalar(select(AuthSession).where(AuthSession.token == token))
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")

    user = db.scalar(select(User).where(User.id == session.user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session user")

    return user


def require_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    return current_user


def change_password(db: Session, user: User, new_password: str) -> User:
    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    db.commit()
    if user.username == DEFAULT_ADMIN_USERNAME:
        delete_setting(db, ADMIN_TEMP_PASSWORD_KEY)
        db.commit()
    db.refresh(user)
    return user


def create_user(
    db: Session,
    username: str,
    is_admin: bool,
    permissions: list[str],
) -> tuple[User, str]:
    existing = db.scalar(select(User).where(User.username == username.strip()))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    temp_password = secrets.token_urlsafe(12)
    user = User(
        username=username.strip(),
        password_hash=hash_password(temp_password),
        is_admin=is_admin,
        permissions=normalize_permissions(permissions),
        must_change_password=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, temp_password


def update_user_permissions(db: Session, user: User, is_admin: bool, permissions: list[str]) -> User:
    user.is_admin = is_admin
    user.permissions = normalize_permissions(permissions)
    db.commit()
    db.refresh(user)
    return user


def reset_user_password(db: Session, user: User) -> str:
    temp_password = secrets.token_urlsafe(12)
    user.password_hash = hash_password(temp_password)
    user.must_change_password = True
    db.commit()
    db.refresh(user)
    return temp_password


def _get_setting_value(db: Session, key: str) -> str | None:
    from app.services.settings_service import get_setting_value

    return get_setting_value(db, key)


def _has_admin_seed_password(db: Session) -> bool:
    return _get_setting_value(db, ADMIN_TEMP_PASSWORD_KEY) is not None