from __future__ import annotations

import logging
import secrets
from collections.abc import Sequence
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.dependency import Dependency
from app.models.environment import Environment
from app.models.project import Project
from app.parsers.base import DependencyEcosystem, ParsedDependency
from app.services.alert_notification_service import process_scan_notifications
from app.services.self_monitoring import is_self_monitoring_project
from app.services.vulnerability_scanner import scan_vulnerabilities

logger = logging.getLogger(__name__)


class ProjectEnvironment(StrEnum):
    DEV = "Dev"
    STAGING = "Staging"
    PRODUCTION = "Production"


def normalize_environment(raw_value: str) -> ProjectEnvironment:
    normalized = raw_value.strip().lower()
    if normalized == "dev":
        return ProjectEnvironment.DEV
    if normalized == "staging":
        return ProjectEnvironment.STAGING
    if normalized == "production":
        return ProjectEnvironment.PRODUCTION
    raise ValueError("environment must be one of: Dev, Staging, Production")


def register_dependency_snapshot(
    db: Session,
    project_name: str,
    environment: ProjectEnvironment,
    api_key: str,
    dependencies: Sequence[ParsedDependency],
) -> tuple[Environment, int]:
    project = db.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        raise LookupError("project not found")
    if project.api_key != api_key:
        raise PermissionError("invalid api key for project")

    env = db.scalar(
        select(Environment).where(
            Environment.project_id == project.id,
            Environment.name == environment.value,
        )
    )

    if env is None:
        env = Environment(project_id=project.id, name=environment.value)
        db.add(env)
        db.flush()

    deduplicated: dict[str, ParsedDependency] = {}
    for dep in dependencies:
        package_name = dep.package_name.strip().lower()
        if package_name:
            deduplicated[package_name] = dep

    db.execute(delete(Dependency).where(Dependency.environment_id == env.id))

    db.add_all(
        [
            Dependency(
                environment_id=env.id,
                package_name=package_name,
                installed_version=dependency.installed_version.strip() or "unspecified",
                ecosystem=dependency.ecosystem.value,
            )
            for package_name, dependency in sorted(deduplicated.items())
        ]
    )

    env.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(env)

    vulnerability_result = scan_vulnerabilities(db)
    notification_result = process_scan_notifications(
        db,
        new_findings=vulnerability_result.get("new_findings", []),
    )

    # The first CI/CD commit should already populate vulnerability alerts.
    # Keep the dependency snapshot response unchanged, but log the scan result.
    logger.info(
        "Initial vulnerability scan after dependency snapshot: activated=%s resolved=%s scanned_pairs=%s telegram_vulnerabilities=%s telegram_updates=%s",
        vulnerability_result.get("activated"),
        vulnerability_result.get("resolved"),
        vulnerability_result.get("scanned_pairs"),
        notification_result.get("vulnerabilities_sent"),
        notification_result.get("updates_sent"),
    )

    return env, len(deduplicated)


def rotate_project_api_key(db: Session, project_name: str) -> tuple[Project, str, datetime]:
    project = db.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        raise LookupError("project not found")
    if is_self_monitoring_project(project.name):
        raise PermissionError("self-monitoring projects cannot rotate their API key")

    # token_urlsafe(32) gives a high-entropy key suitable for CI/CD secrets.
    new_api_key = secrets.token_urlsafe(32)
    project.api_key = new_api_key
    rotated_at = datetime.now(UTC)
    db.commit()
    db.refresh(project)
    return project, new_api_key, rotated_at


def delete_project(db: Session, project_name: str) -> None:
    project = db.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        raise LookupError("project not found")
    if is_self_monitoring_project(project.name):
        raise PermissionError("self-monitoring projects cannot be deleted")
    db.delete(project)
    db.commit()
