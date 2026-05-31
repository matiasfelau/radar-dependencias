from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest, TelegramTestResponse
from app.services.auth_service import get_current_user
from app.services.settings_management import upsert_setting
from app.services.settings_service import (
    get_scan_interval_seconds,
    get_telegram_bot_token,
    get_telegram_chat_id,
    get_webhook_url,
)
from app.services.telegram_notifier import send_telegram_message

router = APIRouter(prefix="/settings")


@router.get("", response_model=SettingsResponse, summary="Get scanner settings")
def get_settings_snapshot(
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> SettingsResponse:
    return SettingsResponse(
        scan_interval_seconds=get_scan_interval_seconds(db, default=43200),
        webhook_url=get_webhook_url(db),
        telegram_bot_token=get_telegram_bot_token(db),
        telegram_chat_id=get_telegram_chat_id(db),
    )


@router.put("", response_model=SettingsResponse, summary="Update scanner settings")
def update_settings(
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> SettingsResponse:
    if payload.scan_interval_seconds is not None:
        upsert_setting(db, "scan_interval_seconds", str(payload.scan_interval_seconds))

    if payload.webhook_url is not None:
        upsert_setting(db, "webhook_url", payload.webhook_url.strip())

    if payload.telegram_bot_token is not None:
        upsert_setting(db, "telegram_bot_token", payload.telegram_bot_token.strip())

    if payload.telegram_chat_id is not None:
        upsert_setting(db, "telegram_chat_id", payload.telegram_chat_id.strip())

    db.commit()

    return SettingsResponse(
        scan_interval_seconds=get_scan_interval_seconds(db, default=43200),
        webhook_url=get_webhook_url(db),
        telegram_bot_token=get_telegram_bot_token(db),
        telegram_chat_id=get_telegram_chat_id(db),
    )


@router.post("/test-telegram", response_model=TelegramTestResponse, summary="Send a Telegram test message")
def test_telegram(
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> TelegramTestResponse:
    bot_token = get_telegram_bot_token(db)
    chat_id = get_telegram_chat_id(db)
    if not bot_token or not chat_id:
        raise HTTPException(
            status_code=400,
            detail="Configura telegram_bot_token y telegram_chat_id antes de probar.",
        )

    sent = send_telegram_message(
        bot_token,
        chat_id,
        "✅ <b>Dependency Radar</b>\n\nNotificación de prueba enviada correctamente.",
    )
    if not sent:
        raise HTTPException(
            status_code=502,
            detail="Telegram rechazó el mensaje. Revisa token, chat id y que el bot esté en el grupo.",
        )

    return TelegramTestResponse(ok=True, detail="Mensaje de prueba enviado.")
