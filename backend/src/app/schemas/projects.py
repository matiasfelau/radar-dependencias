from datetime import datetime

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    project_name: str = Field(..., min_length=2, max_length=255, description="Project name")


class ProjectCreatedResponse(BaseModel):
    project_name: str = Field(description="Project name")
    api_key: str = Field(description="Auto-generated API key")
    created_at: datetime = Field(description="Project creation timestamp")


class DependencySnapshotResponse(BaseModel):
    project_name: str = Field(description="Project name")
    environment: str = Field(description="Environment name")
    dependencies_count: int = Field(description="Total dependencies stored in snapshot")
    updated_at: datetime = Field(description="Snapshot update timestamp")


class ProjectApiKeyResponse(BaseModel):
    project_name: str = Field(description="Project name")
    api_key: str = Field(description="Generated API key")
    rotated_at: datetime = Field(description="When the key was rotated")


class ActiveAlertItem(BaseModel):
    project_name: str
    environment_name: str
    package_name: str
    installed_version: str
    dependency_source: str
    has_vulnerability: bool
    has_update: bool
    latest_version: str | None
    max_severity: str | None
    updated_at: datetime


class ActiveAlertsResponse(BaseModel):
    total: int
    items: list[ActiveAlertItem]
