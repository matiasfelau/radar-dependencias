import secrets
from datetime import UTC

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project
from app.parsers.factory import ParserNotSupportedError, get_parser_for_filename
from app.schemas.projects import (
    CreateProjectRequest,
    DependencySnapshotResponse,
    ProjectApiKeyResponse,
    ProjectCreatedResponse,
)
from app.services.project_registration import (
    normalize_environment,
    register_dependency_snapshot,
    rotate_project_api_key,
    delete_project,
)
from app.services.auth_service import get_current_user
from app.schemas.inventory import ProjectsInventoryResponse
from app.services.inventory_service import get_projects_inventory

router = APIRouter(prefix="/projects")


@router.post(
    "",
    response_model=ProjectCreatedResponse,
    summary="Create a new project",
)
def create_project(
    request: CreateProjectRequest,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> ProjectCreatedResponse:
    # Check if project already exists
    existing = db.scalar(select(Project).where(Project.name == request.project_name.strip()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project already exists")

    # Create new project with auto-generated API key
    new_project = Project(
        name=request.project_name.strip(),
        api_key=secrets.token_urlsafe(32),
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return ProjectCreatedResponse(
        project_name=new_project.name,
        api_key=new_project.api_key,
        created_at=new_project.created_at,
    )


@router.post(
    "/register",
    response_model=DependencySnapshotResponse,
    summary="Register dependency snapshot from CI/CD",
)
def register_project_dependencies(
    project_name: str = Form(..., min_length=2, max_length=255),
    environment: str = Form(...),
    dependency_file: UploadFile = File(...),
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> DependencySnapshotResponse:
    if not dependency_file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="file name is required")

    try:
        parser = get_parser_for_filename(dependency_file.filename)
    except ParserNotSupportedError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc)) from exc

    file_bytes = dependency_file.file.read()
    dependencies = parser.parse(file_bytes)

    try:
        normalized_environment = normalize_environment(environment)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    try:
        env, count = register_dependency_snapshot(
            db=db,
            project_name=project_name.strip(),
            environment=normalized_environment,
            api_key=api_key.strip(),
            dependencies=dependencies,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return DependencySnapshotResponse(
        project_name=project_name.strip(),
        environment=env.name,
        dependencies_count=count,
        updated_at=env.updated_at,
    )


@router.get("", response_model=ProjectsInventoryResponse, summary="List all projects inventory")
def list_projects_inventory(
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> ProjectsInventoryResponse:
    projects = get_projects_inventory(db)
    return ProjectsInventoryResponse(total_projects=len(projects), projects=projects)


@router.post(
    "/{project_name}/api-key/rotate",
    response_model=ProjectApiKeyResponse,
    summary="Rotate API key for an existing project",
)
def rotate_api_key_for_project(
    project_name: str,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> ProjectApiKeyResponse:
    try:
        project, api_key, rotated_at = rotate_project_api_key(db=db, project_name=project_name.strip())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return ProjectApiKeyResponse(project_name=project.name, api_key=api_key, rotated_at=rotated_at)


@router.delete("/{project_name}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a project and its data")
def delete_project_endpoint(
    project_name: str,
    db: Session = Depends(get_db),
    _current_user=Depends(get_current_user),
) -> None:
    try:
        delete_project(db=db, project_name=project_name.strip())
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return None
