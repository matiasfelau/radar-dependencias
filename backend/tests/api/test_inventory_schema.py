from datetime import datetime, timezone

from app.schemas.inventory import (
    InventoryDependency,
    InventoryEnvironment,
    InventoryProject,
    ProjectsInventoryResponse,
)


def test_inventory_schema_accepts_datetime() -> None:
    dep = InventoryDependency(package_name="pkg", installed_version="1.2.3")
    env = InventoryEnvironment(name="Dev", updated_at=datetime.now(timezone.utc), dependencies=[dep])
    proj = InventoryProject(name="p", environments=[env])
    resp = ProjectsInventoryResponse(total_projects=1, projects=[proj])
    assert resp.total_projects == 1