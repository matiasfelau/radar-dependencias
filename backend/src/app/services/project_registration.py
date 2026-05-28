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
from app.parsers.base import ParsedDependency
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

    deduplicated = {
        dep.package_name.strip().lower(): dep.installed_version.strip()
        for dep in dependencies
        if dep.package_name.strip()
    }

    db.execute(delete(Dependency).where(Dependency.environment_id == env.id))

    db.add_all(
        [
            Dependency(
                environment_id=env.id,
                package_name=package_name,
                installed_version=installed_version or "unspecified",
            )
            for package_name, installed_version in sorted(deduplicated.items())
        ]
    )

    env.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(env)

    vulnerability_result = scan_vulnerabilities(db)

    # The first CI/CD commit should already populate vulnerability alerts.
    # Keep the dependency snapshot response unchanged, but log the scan result.
    logger.info(
        "Initial vulnerability scan after dependency snapshot: activated=%s resolved=%s scanned_pairs=%s",
        vulnerability_result.get("activated"),
        vulnerability_result.get("resolved"),
        vulnerability_result.get("scanned_pairs"),
    )

    return env, len(deduplicated)


def rotate_project_api_key(db: Session, project_name: str) -> tuple[Project, str, datetime]:
    project = db.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        raise LookupError("project not found")

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
    db.delete(project)
    db.commit()
