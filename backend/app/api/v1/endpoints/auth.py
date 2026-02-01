"""
Authentication endpoints.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.core.security import get_current_user
from app.services.auth import get_auth_service, AuthService

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response schemas
class UserResponse(BaseModel):
    """User response schema (excludes password)."""
    id: str
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Register request schema."""
    username: str
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema."""
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


def _user_to_response(user: dict) -> UserResponse:
    """Convert user dict to response model."""
    return UserResponse(
        id=user.get("id", ""),
        username=user.get("username", ""),
        email=user.get("email", ""),
        role=user.get("role", "user"),
        is_active=user.get("is_active", False),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return access token.

    Uses OAuth2 password flow. Send username and password as form data.
    """
    user = await auth_service.authenticate_user(
        username=form_data.username,
        password=form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = auth_service.create_tokens(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=_user_to_response(user),
    )


@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return access token.

    Alternative to OAuth2 form login - accepts JSON body.
    """
    user = await auth_service.authenticate_user(
        username=request.username,
        password=request.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tokens = auth_service.create_tokens(user)

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=_user_to_response(user),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.

    Note: JWT tokens are stateless, so this is a no-op on the server side.
    The client should discard the token.
    """
    logger.info(f"User '{current_user.get('username')}' logged out")
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return _user_to_response(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token.

    Returns a new access token for the authenticated user.
    """
    tokens = auth_service.create_tokens(current_user)

    return TokenResponse(
        access_token=tokens["access_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
        user=_user_to_response(current_user),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user.

    Creates a new user account with the "user" role.
    """
    try:
        user = await auth_service.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            role="user",
        )
        return _user_to_response(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change current user's password.

    Requires the current password for verification.
    """
    success = await auth_service.change_password(
        user_id=current_user["id"],
        current_password=request.current_password,
        new_password=request.new_password,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    return MessageResponse(message="Password changed successfully")
