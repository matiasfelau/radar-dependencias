from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthUserResponse,
    CreateUserRequest,
    CreateUserResponse,
    ResetPasswordResponse,
    UpdateUserRequest,
    UserSummaryResponse,
)
from app.services.auth_service import (
    create_user,
    parse_permissions,
    require_admin_user,
    reset_user_password,
    update_user_permissions,
    user_summary_to_response,
)

router = APIRouter(prefix="/admin")
logger = logging.getLogger(__name__)


@router.get("/users", response_model=list[UserSummaryResponse], summary="List users")
def list_users(db: Session = Depends(get_db), _admin=Depends(require_admin_user)) -> list[UserSummaryResponse]:
    users = db.scalars(select(User).order_by(User.username)).all()
    return [UserSummaryResponse(**user_summary_to_response(user)) for user in users]


@router.post("/users", response_model=CreateUserResponse, summary="Create user")
def create_new_user(
    payload: CreateUserRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin_user),
) -> CreateUserResponse:
    user, temp_password = create_user(db, payload.username, payload.is_admin, payload.permissions)
    logger.info("Created user %s (admin=%s)", user.username, user.is_admin)
    return CreateUserResponse(user=UserSummaryResponse(**user_summary_to_response(user)), temp_password=temp_password)


@router.patch("/users/{user_id}", response_model=UserSummaryResponse, summary="Update user permissions")
def update_existing_user(
    user_id: int,
    payload: UpdateUserRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin_user),
) -> UserSummaryResponse:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated = update_user_permissions(db, user, payload.is_admin, payload.permissions)
    return UserSummaryResponse(**user_summary_to_response(updated))


@router.post("/users/{user_id}/reset-password", response_model=ResetPasswordResponse, summary="Reset user password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin_user),
) -> ResetPasswordResponse:
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    temp_password = reset_user_password(db, user)
    logger.warning("Password reset for user %s", user.username)
    return ResetPasswordResponse(temp_password=temp_password)