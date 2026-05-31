from pydantic import BaseModel
from typing import List
from datetime import datetime


class InventoryDependency(BaseModel):
    package_name: str
    installed_version: str


class InventoryEnvironment(BaseModel):
    name: str
    updated_at: datetime | None
    dependencies: List[InventoryDependency]


class InventoryProject(BaseModel):
    name: str
    is_internal: bool = False
    environments: List[InventoryEnvironment]


class ProjectsInventoryResponse(BaseModel):
    total_projects: int
    projects: List[InventoryProject]
