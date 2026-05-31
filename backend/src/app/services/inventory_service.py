from __future__ import annotations

from collections.abc import Iterable
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.environment import Environment
from app.models.dependency import Dependency
from app.services.self_monitoring import is_self_monitoring_project


def get_projects_inventory(db: Session) -> list[dict]:
    projects = db.scalars(select(Project)).all()

    result: list[dict] = []
    for project in projects:
        envs = (
            db.scalars(select(Environment).where(Environment.project_id == project.id)).all()
        )
        env_list: list[dict] = []
        for env in envs:
            deps = (
                db.scalars(select(Dependency).where(Dependency.environment_id == env.id)).all()
            )
            deps_list = [
                {"package_name": d.package_name, "installed_version": d.installed_version}
                for d in deps
            ]
            env_list.append({"name": env.name, "updated_at": env.updated_at, "dependencies": deps_list})

        result.append({"name": project.name, "is_internal": is_self_monitoring_project(project.name), "environments": env_list})

    return result
