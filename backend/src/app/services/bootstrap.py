from __future__ import annotations

from app.db.session import SessionLocal
from app.services.auth_service import announce_admin_seed_password, seed_admin_user
from app.services.database_migration import upgrade_database
from app.services.self_monitoring import seed_self_monitoring_projects


def bootstrap_application() -> None:
    upgrade_database()
    with SessionLocal() as db:
        seed_admin_user(db)
        announce_admin_seed_password(db)
        seed_self_monitoring_projects(db)