from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dependency import Dependency
from app.models.environment import Environment
from app.models.project import Project
from app.models.setting import Setting
from app.services.npm_client import get_latest_npm_version, has_npm_update
from app.services.pypi_client import get_latest_pypi_version, has_pypi_update
from app.services.settings_management import upsert_setting
from app.services.settings_service import get_telegram_chat_id, get_telegram_bot_token
from app.services.telegram_notifier import escape_telegram_html, send_telegram_message
from app.services.vulnerability_scanner import NewVulnerabilityFinding

logger = logging.getLogger(__name__)
NOTIFIED_UPDATES_KEY = "telegram_notified_update_keys"


@dataclass(frozen=True)
class DependencyLocation:
    project_name: str
    environment_name: str


def process_scan_notifications(
    db: Session,
    *,
    new_findings: list[NewVulnerabilityFinding],
) -> dict[str, int]:
    bot_token = get_telegram_bot_token(db)
    chat_id = get_telegram_chat_id(db)
    if not bot_token or not chat_id:
        logger.debug("Telegram notifications skipped: bot token or chat id not configured")
        return {"vulnerabilities_sent": 0, "updates_sent": 0}

    vulnerabilities_sent = _notify_new_vulnerabilities(db, bot_token, chat_id, new_findings)
    updates_sent = _notify_available_updates(db, bot_token, chat_id)

    if vulnerabilities_sent or updates_sent:
        logger.info(
            "Telegram notifications sent: vulnerabilities=%s updates=%s",
            vulnerabilities_sent,
            updates_sent,
        )

    return {
        "vulnerabilities_sent": vulnerabilities_sent,
        "updates_sent": updates_sent,
    }


def _notify_new_vulnerabilities(
    db: Session,
    bot_token: str,
    chat_id: str,
    new_findings: list[NewVulnerabilityFinding],
) -> int:
    sent_count = 0

    for finding in new_findings:
        locations = _find_dependency_locations(db, finding.package_name, finding.affected_version)
        if not locations:
            locations = [
                DependencyLocation(
                    project_name="Desconocido",
                    environment_name="Desconocido",
                )
            ]

        for location in locations:
            message = _format_vulnerability_message(finding, location)
            if send_telegram_message(bot_token, chat_id, message):
                sent_count += 1

    return sent_count


def _notify_available_updates(db: Session, bot_token: str, chat_id: str) -> int:
    records = db.execute(
        select(
            Dependency.package_name,
            Dependency.installed_version,
            Dependency.ecosystem,
            Project.name,
            Environment.name,
        )
        .join(Environment, Environment.id == Dependency.environment_id)
        .join(Project, Project.id == Environment.project_id)
        .order_by(Project.name, Environment.name, Dependency.package_name)
    ).all()

    latest_version_cache: dict[tuple[str, str], str | None] = {}
    active_update_keys: set[str] = set()
    pending_notifications: list[tuple[str, str]] = []

    for package_name, installed_version, ecosystem, project_name, environment_name in records:
        cache_key = (ecosystem, package_name)
        if cache_key not in latest_version_cache:
            if ecosystem == "npm":
                latest_version_cache[cache_key] = get_latest_npm_version(package_name)
            else:
                latest_version_cache[cache_key] = get_latest_pypi_version(package_name)

        latest_version = latest_version_cache[cache_key]
        has_update = (
            has_npm_update(installed_version, latest_version)
            if ecosystem == "npm"
            else has_pypi_update(installed_version, latest_version)
        )
        if not has_update or not latest_version:
            continue

        update_key = _build_update_key(
            project_name,
            environment_name,
            package_name,
            installed_version,
            latest_version,
        )
        active_update_keys.add(update_key)
        pending_notifications.append(
            (
                update_key,
                _format_update_message(
                    project_name=project_name,
                    environment_name=environment_name,
                    package_name=package_name,
                    installed_version=installed_version,
                    latest_version=latest_version,
                    dependency_source=ecosystem,
                ),
            )
        )

    notified_keys = _load_notified_update_keys(db)
    sent_count = 0
    keys_to_store = active_update_keys.intersection(notified_keys)

    for update_key, message in pending_notifications:
        if update_key in notified_keys:
            continue
        if send_telegram_message(bot_token, chat_id, message):
            sent_count += 1
            keys_to_store.add(update_key)

    _save_notified_update_keys(db, keys_to_store)
    return sent_count


def _find_dependency_locations(
    db: Session,
    package_name: str,
    installed_version: str,
) -> list[DependencyLocation]:
    rows = db.execute(
        select(Project.name, Environment.name)
        .join(Environment, Environment.project_id == Project.id)
        .join(Dependency, Dependency.environment_id == Environment.id)
        .where(
            Dependency.package_name == package_name,
            Dependency.installed_version == installed_version,
        )
        .order_by(Project.name, Environment.name)
    ).all()

    return [
        DependencyLocation(project_name=project_name, environment_name=environment_name)
        for project_name, environment_name in rows
    ]


def _format_vulnerability_message(
    finding: NewVulnerabilityFinding,
    location: DependencyLocation,
) -> str:
    exploit_label = "Sí" if finding.has_exploit else "No"
    lines = [
        "🚨 <b>Nueva vulnerabilidad detectada</b>",
        "",
        f"<b>Proyecto:</b> {escape_telegram_html(location.project_name)} / {escape_telegram_html(location.environment_name)}",
        f"<b>Paquete:</b> {escape_telegram_html(finding.package_name)}@{escape_telegram_html(finding.affected_version)}",
        f"<b>CVE:</b> {escape_telegram_html(finding.cve_id)}",
        f"<b>Severidad:</b> {escape_telegram_html(finding.severity)}",
        f"<b>Exploit público:</b> {exploit_label}",
    ]

    if finding.exploit_url:
        lines.append(f"<b>Exploit:</b> {escape_telegram_html(finding.exploit_url)}")

    if finding.description:
        lines.extend(["", escape_telegram_html(finding.description)])

    return "\n".join(lines)


def _format_update_message(
    *,
    project_name: str,
    environment_name: str,
    package_name: str,
    installed_version: str,
    latest_version: str,
    dependency_source: str,
) -> str:
    return "\n".join(
        [
            "📦 <b>Actualización disponible</b>",
            "",
            f"<b>Proyecto:</b> {escape_telegram_html(project_name)} / {escape_telegram_html(environment_name)}",
            f"<b>Paquete:</b> {escape_telegram_html(package_name)}@{escape_telegram_html(installed_version)}",
            f"<b>Última versión:</b> {escape_telegram_html(latest_version)}",
            f"<b>Origen:</b> {escape_telegram_html(dependency_source)}",
        ]
    )


def _build_update_key(
    project_name: str,
    environment_name: str,
    package_name: str,
    installed_version: str,
    latest_version: str,
) -> str:
    return (
        f"{project_name}/{environment_name}/"
        f"{package_name}@{installed_version}->{latest_version}"
    )


def _load_notified_update_keys(db: Session) -> set[str]:
    raw_value = db.scalar(select(Setting.value).where(Setting.key == NOTIFIED_UPDATES_KEY))
    if not raw_value:
        return set()

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        logger.warning("Invalid telegram update notification cache, resetting")
        return set()

    if not isinstance(parsed, list):
        return set()

    return {str(item) for item in parsed}


def _save_notified_update_keys(db: Session, keys: set[str]) -> None:
    upsert_setting(db, NOTIFIED_UPDATES_KEY, json.dumps(sorted(keys)))
    db.commit()
