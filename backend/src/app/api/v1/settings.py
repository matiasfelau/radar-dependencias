from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.services.settings_management import upsert_setting
from app.services.settings_service import get_scan_interval_seconds, get_webhook_url

router = APIRouter(prefix="/settings")


@router.get("", response_model=SettingsResponse, summary="Get scanner settings")
def get_settings_snapshot(db: Session = Depends(get_db)) -> SettingsResponse:
    return SettingsResponse(
        scan_interval_seconds=get_scan_interval_seconds(db, default=43200),
        webhook_url=get_webhook_url(db),
    )


@router.put("", response_model=SettingsResponse, summary="Update scanner settings")
def update_settings(payload: SettingsUpdateRequest, db: Session = Depends(get_db)) -> SettingsResponse:
    if payload.scan_interval_seconds is not None:
        upsert_setting(db, "scan_interval_seconds", str(payload.scan_interval_seconds))

    if payload.webhook_url is not None:
        upsert_setting(db, "webhook_url", payload.webhook_url.strip())

    db.commit()

    return SettingsResponse(
        scan_interval_seconds=get_scan_interval_seconds(db, default=43200),
        webhook_url=get_webhook_url(db),
    )
