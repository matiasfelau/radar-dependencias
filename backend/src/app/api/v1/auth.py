from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    AuthUserResponse,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
)
from app.services.auth_service import (
    authenticate_user,
    change_password,
    create_session,
    get_current_user,
    revoke_session,
    user_to_response,
)

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=LoginResponse, summary="Login with username and password")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = authenticate_user(db, payload.username, payload.password)
    token = create_session(db, user)
    return LoginResponse(
        access_token=token,
        must_change_password=user.must_change_password,
        user=AuthUserResponse(**user_to_response(user)),
    )


@router.post("/logout", summary="Logout and revoke current session")
def logout(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, str]:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization token")
    token = authorization.removeprefix("Bearer ").strip()
    revoke_session(db, token)
    return {"status": "ok"}


@router.get("/me", response_model=AuthUserResponse, summary="Get current user")
def me(current_user=Depends(get_current_user)) -> AuthUserResponse:
    return AuthUserResponse(**user_to_response(current_user))


@router.post("/change-password", response_model=AuthUserResponse, summary="Change the current password")
def change_current_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AuthUserResponse:
    if not current_user.must_change_password and not payload.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is required")

    if not current_user.must_change_password:
        from app.services.auth_service import verify_password

        if not verify_password(payload.current_password or "", current_user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")

    updated = change_password(db, current_user, payload.new_password)
    return AuthUserResponse(**user_to_response(updated))