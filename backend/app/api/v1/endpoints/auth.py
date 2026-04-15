"""
Authentication endpoints.
"""
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.core.security import get_current_user, require_admin
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
    status: str = "approved"
    platforms: List[str] = []

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
    email: EmailStr
    password: str
    platforms: List[str] = []


class RegisterResponse(BaseModel):
    """Register response schema."""
    message: str
    status: str


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
        status=user.get("status", "approved"),
        platforms=user.get("platforms", []),
    )


async def _check_user_status_on_login_failure(
    username: str,
    auth_service: AuthService,
) -> None:
    """Check if login failed due to pending/rejected status and raise appropriate error."""
    existing = await auth_service.get_user_by_username(username)
    if existing:
        user_status = existing.get("status", "approved")
        if user_status == "pending":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending admin approval.",
            )
        if user_status == "rejected":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account request was not approved.",
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
        await _check_user_status_on_login_failure(form_data.username, auth_service)
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
        await _check_user_status_on_login_failure(request.username, auth_service)
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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user account.

    Creates the account in pending status. An approval email
    is sent to the admin. The user cannot log in until approved.
    """
    # Validate platform IDs
    valid_platforms = [
        p.strip()
        for p in settings.SIGNUP_AVAILABLE_PLATFORMS.split(",")
        if p.strip()
    ]
    for p in request.platforms:
        if p not in valid_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid platform: {p}. Valid platforms: {', '.join(valid_platforms)}",
            )

    try:
        user = await auth_service.create_user(
            username=request.email,
            email=request.email,
            password=request.password,
            role="user",
            status="pending",
            is_active=False,
            platforms=request.platforms,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Send approval email to admin (non-blocking — don't fail registration if email fails)
    try:
        await auth_service.send_approval_email(user)
    except Exception as e:
        logger.error(f"Failed to send approval email: {e}")

    return RegisterResponse(
        message="Account created. Awaiting admin approval.",
        status="pending",
    )


# --- Email-based one-click approval (public, signed token) ---


@router.get("/approve", response_model=MessageResponse)
async def approve_via_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    One-click approval from email link.

    Token is a signed JWT containing the user_id and action.
    """
    user = await auth_service.approve_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired approval link",
        )
    return MessageResponse(message=f"User {user.get('email', '')} has been approved.")


@router.get("/reject", response_model=MessageResponse)
async def reject_via_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    One-click rejection from email link.

    Token is a signed JWT containing the user_id and action.
    """
    user = await auth_service.reject_user_by_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired rejection link",
        )
    return MessageResponse(message=f"User {user.get('email', '')} has been rejected.")


# --- Admin user management endpoints ---


@router.get("/admin/users/pending", response_model=List[UserResponse])
async def list_pending_users(
    _current_user: dict = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service),
):
    """List all users awaiting approval. Admin only."""
    users = await auth_service.list_users_by_status("pending")
    return [_user_to_response(u) for u in users]


@router.post("/admin/users/{user_id}/approve", response_model=MessageResponse)
async def approve_user(
    user_id: str,
    _current_user: dict = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Approve a pending user account. Admin only."""
    user = await auth_service.approve_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return MessageResponse(message=f"User {user.get('email', '')} approved")


@router.post("/admin/users/{user_id}/reject", response_model=MessageResponse)
async def reject_user(
    user_id: str,
    _current_user: dict = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reject a pending user account. Admin only."""
    user = await auth_service.reject_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return MessageResponse(message=f"User {user.get('email', '')} rejected")


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
