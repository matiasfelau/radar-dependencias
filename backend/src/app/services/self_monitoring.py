from __future__ import annotations

import importlib.metadata
import json
import logging
import secrets
import tomllib
from pathlib import Path

from packaging.requirements import Requirement
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.dependency import Dependency
from app.models.environment import Environment
from app.models.project import Project
from app.parsers.base import DependencyEcosystem, ParsedDependency
from app.services.alert_notification_service import process_scan_notifications
from app.services.vulnerability_scanner import scan_vulnerabilities

logger = logging.getLogger(__name__)

BACKEND_PROJECT_NAME = "dependency-radar-backend"
FRONTEND_PROJECT_NAME = "dependency-radar-frontend"
SELF_ENVIRONMENT_NAME = "Production"


def is_self_monitoring_project(project_name: str) -> bool:
    normalized_name = project_name.strip().lower()
    return normalized_name in {
        BACKEND_PROJECT_NAME.lower(),
        FRONTEND_PROJECT_NAME.lower(),
    }


def seed_self_monitoring_projects(db: Session) -> None:
    settings = get_settings()
    repo_root = Path(settings.repository_root)

    project_snapshots: list[tuple[str, list[ParsedDependency]]] = []

    backend_dependencies = _collect_backend_dependencies(repo_root / "backend" / "pyproject.toml")
    if backend_dependencies:
        project_snapshots.append((BACKEND_PROJECT_NAME, backend_dependencies))
    else:
        logger.warning("Self-monitoring backend dependencies were not found")

    frontend_dependencies = _collect_frontend_dependencies(repo_root / "frontend" / "package-lock.json")
    if frontend_dependencies:
        project_snapshots.append((FRONTEND_PROJECT_NAME, frontend_dependencies))
    else:
        logger.warning("Self-monitoring frontend dependencies were not found")

    if not project_snapshots:
        return

    for project_name, dependencies in project_snapshots:
        _upsert_project_snapshot(db, project_name, dependencies)

    scan_result = scan_vulnerabilities(db)
    notification_result = process_scan_notifications(
        db,
        new_findings=scan_result.get("new_findings", []),
    )
    logger.info(
        "Self-monitoring scan completed: activated=%s resolved=%s scanned_pairs=%s telegram_vulnerabilities=%s telegram_updates=%s",
        scan_result.get("activated"),
        scan_result.get("resolved"),
        scan_result.get("scanned_pairs"),
        notification_result.get("vulnerabilities_sent"),
        notification_result.get("updates_sent"),
    )


def _upsert_project_snapshot(db: Session, project_name: str, dependencies: list[ParsedDependency]) -> None:
    project = db.scalar(select(Project).where(Project.name == project_name))
    if project is None:
        project = Project(name=project_name, api_key=secrets.token_urlsafe(32))
        db.add(project)
        db.flush()

    environment = db.scalar(
        select(Environment).where(
            Environment.project_id == project.id,
            Environment.name == SELF_ENVIRONMENT_NAME,
        )
    )
    if environment is None:
        environment = Environment(project_id=project.id, name=SELF_ENVIRONMENT_NAME)
        db.add(environment)
        db.flush()

    deduplicated: dict[str, ParsedDependency] = {}
    for dependency in dependencies:
        package_name = dependency.package_name.strip().lower()
        if package_name:
            deduplicated[package_name] = dependency

    db.execute(delete(Dependency).where(Dependency.environment_id == environment.id))
    db.add_all(
        [
            Dependency(
                environment_id=environment.id,
                package_name=package_name,
                installed_version=dependency.installed_version.strip() or "unspecified",
                ecosystem=dependency.ecosystem.value,
            )
            for package_name, dependency in sorted(deduplicated.items())
        ]
    )
    db.commit()


def _collect_backend_dependencies(pyproject_path: Path) -> list[ParsedDependency]:
    if not pyproject_path.exists():
        return []

    with pyproject_path.open("rb") as pyproject_file:
        pyproject_data = tomllib.load(pyproject_file)

    project_data = pyproject_data.get("project", {})
    raw_dependencies = project_data.get("dependencies", [])

    dependencies: list[ParsedDependency] = []
    for raw_dependency in raw_dependencies:
        requirement = Requirement(raw_dependency)
        try:
            installed_version = importlib.metadata.version(requirement.name)
        except importlib.metadata.PackageNotFoundError:
            installed_version = str(requirement.specifier) or "unspecified"
        dependencies.append(
            ParsedDependency(
                package_name=requirement.name,
                installed_version=installed_version,
                ecosystem=DependencyEcosystem.PYPI,
            )
        )

    return dependencies


def _collect_frontend_dependencies(package_lock_path: Path) -> list[ParsedDependency]:
    if not package_lock_path.exists():
        return []

    with package_lock_path.open("r", encoding="utf-8") as package_lock_file:
        package_lock_data = json.load(package_lock_file)

    root_packages = package_lock_data.get("packages", {}).get("", {})
    direct_dependencies = {
        **root_packages.get("dependencies", {}),
        **root_packages.get("devDependencies", {}),
    }

    package_entries = package_lock_data.get("packages", {})
    dependencies: list[ParsedDependency] = []

    for package_name in sorted(direct_dependencies):
        entry = package_entries.get(f"node_modules/{package_name}", {})
        installed_version = entry.get("version") or direct_dependencies[package_name]
        dependencies.append(
            ParsedDependency(
                package_name=package_name,
                installed_version=installed_version,
                ecosystem=DependencyEcosystem.NPM,
            )
        )

    return dependencies