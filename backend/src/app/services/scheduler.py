from __future__ import annotations

import logging
from dataclasses import dataclass

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.alert_notification_service import process_scan_notifications
from app.services.settings_service import get_scan_interval_seconds
from app.services.vulnerability_scanner import scan_vulnerabilities

logger = logging.getLogger(__name__)
SCAN_JOB_ID = "dependency-radar-vulnerability-scan"


@dataclass
class ScanScheduler:
    scheduler: BackgroundScheduler
    current_interval_seconds: int


def create_scheduler(default_interval_hours: int = 12) -> ScanScheduler:
    default_interval_seconds = default_interval_hours * 3600
    with SessionLocal() as db:
        initial_interval = get_scan_interval_seconds(db, default=default_interval_seconds)

    scheduler = BackgroundScheduler(timezone="UTC")
    state = ScanScheduler(scheduler=scheduler, current_interval_seconds=initial_interval)

    scheduler.add_job(
        _scan_job,
        "interval",
        id=SCAN_JOB_ID,
        seconds=initial_interval,
        kwargs={"state": state},
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    logger.info("Scan scheduler started with interval=%s seconds", initial_interval)
    return state


def stop_scheduler(state: ScanScheduler) -> None:
    if state.scheduler.running:
        state.scheduler.shutdown(wait=False)
        logger.info("Scan scheduler stopped")


def _scan_job(state: ScanScheduler) -> None:
    with SessionLocal() as db:
        new_interval = get_scan_interval_seconds(db, default=state.current_interval_seconds)
        if new_interval != state.current_interval_seconds:
            state.scheduler.reschedule_job(SCAN_JOB_ID, trigger="interval", seconds=new_interval)
            state.current_interval_seconds = new_interval
            logger.info("Rescheduled scan job with interval=%s seconds", new_interval)

        logger.info("Running scheduled vulnerability scan (interval=%s seconds)", state.current_interval_seconds)
        result = scan_vulnerabilities(db)
        notification_result = process_scan_notifications(
            db,
            new_findings=result.get("new_findings", []),
        )
        logger.info(
            "Scheduled vulnerability scan finished: activated=%s resolved=%s scanned_pairs=%s telegram_vulnerabilities=%s telegram_updates=%s",
            result.get("activated"),
            result.get("resolved"),
            result.get("scanned_pairs"),
            notification_result.get("vulnerabilities_sent"),
            notification_result.get("updates_sent"),
        )
