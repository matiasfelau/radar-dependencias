from pydantic import BaseModel, Field


class AuthUserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    permissions: list[str]
    must_change_password: bool


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=128)
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    user: AuthUserResponse


class ChangePasswordRequest(BaseModel):
    current_password: str | None = Field(default=None, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class UserSummaryResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    permissions: list[str]
    must_change_password: bool
    created_at: str


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=2, max_length=128)
    is_admin: bool = False
    permissions: list[str] = Field(default_factory=list)


class CreateUserResponse(BaseModel):
    user: UserSummaryResponse
    temp_password: str


class UpdateUserRequest(BaseModel):
    is_admin: bool = False
    permissions: list[str] = Field(default_factory=list)


class ResetPasswordResponse(BaseModel):
    temp_password: str
