"""
Security utilities - authentication and authorization.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against

    Returns:
        True if the password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plain text password

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The JWT token to decode

    Returns:
        The decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        # Verify token type
        if payload.get("type") != "access":
            return None

        return payload
    except JWTError as e:
        logger.debug(f"Token decode error: {e}")
        return None


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    """
    Get the current authenticated user from the JWT token.

    Args:
        token: The JWT token from the Authorization header

    Returns:
        The user document

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    from app.db.repositories.user import get_user_repository

    user_repo = get_user_repository()
    user = await user_repo.find_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[dict]:
    """
    Get the current user if authenticated, otherwise return None.

    Args:
        token: The JWT token from the Authorization header

    Returns:
        The user document or None
    """
    if not token:
        return None

    try:
        return await get_current_user(token)
    except HTTPException:
        return None


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Require the current user to have admin role.

    Args:
        current_user: The current authenticated user

    Returns:
        The user document if admin

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_role(required_role: str):
    """
    Factory for role-based access control dependency.

    Args:
        required_role: The required role

    Returns:
        A dependency function that checks the role
    """
    async def check_role(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")

        # Admin has access to everything
        if user_role == "admin":
            return current_user

        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )

        return current_user

    return check_role


def require_platform(platform_id: str):
    """
    Factory for platform-based access control dependency.

    Checks if the current user has access to a specific platform.
    Admin users always have access. Users with an empty platforms
    list have unrestricted access (backward compatibility).

    Args:
        platform_id: The platform ID to check access for

    Returns:
        A dependency function that checks platform access
    """
    async def check_platform(current_user: dict = Depends(get_current_user)) -> dict:
        # Admin always has access
        if current_user.get("role") == "admin":
            return current_user

        user_platforms = current_user.get("platforms", [])

        # Empty list = unrestricted (backward compat for existing users)
        if not user_platforms:
            return current_user

        if platform_id not in user_platforms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have access to the {platform_id} platform",
            )

        return current_user

    return check_platform
