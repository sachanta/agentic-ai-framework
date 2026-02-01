"""
Authentication service.
"""
import logging
from datetime import timedelta
from typing import Optional

from app.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.repositories.user import get_user_repository, UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, user_repository: Optional[UserRepository] = None):
        self._user_repository = user_repository

    @property
    def user_repository(self) -> UserRepository:
        """Get user repository, lazy loading if needed."""
        if self._user_repository is None:
            self._user_repository = get_user_repository()
        return self._user_repository

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Authenticate a user by username and password.

        Args:
            username: The username
            password: The plain text password

        Returns:
            The user document if authentication succeeds, None otherwise
        """
        user = await self.user_repository.authenticate(username, password)

        if user:
            logger.info(f"User '{username}' authenticated successfully")
        else:
            logger.warning(f"Failed authentication attempt for user '{username}'")

        return user

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
    ) -> dict:
        """
        Create a new user.

        Args:
            username: The username
            email: The email address
            password: The plain text password
            role: The user role (default: "user")

        Returns:
            The created user document

        Raises:
            ValueError: If username or email already exists
        """
        user = await self.user_repository.create(
            username=username,
            email=email,
            password=password,
            role=role,
        )

        logger.info(f"Created new user: {username} ({role})")

        return user

    def create_tokens(self, user: dict) -> dict:
        """
        Create access token for a user.

        Args:
            user: The user document

        Returns:
            Dictionary with access token and expiration info
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        access_token = create_access_token(
            data={
                "sub": user["id"],
                "username": user["username"],
                "role": user.get("role", "user"),
            },
            expires_delta=expires_delta,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        }

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """
        Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            The user document or None
        """
        return await self.user_repository.find_by_id(user_id)

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """
        Get a user by username.

        Args:
            username: The username

        Returns:
            The user document or None
        """
        return await self.user_repository.find_by_username(username)

    async def update_user(self, user_id: str, **kwargs) -> Optional[dict]:
        """
        Update a user.

        Args:
            user_id: The user ID
            **kwargs: Fields to update

        Returns:
            The updated user document or None
        """
        return await self.user_repository.update(user_id, **kwargs)

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> bool:
        """
        Change a user's password.

        Args:
            user_id: The user ID
            current_password: The current password
            new_password: The new password

        Returns:
            True if password was changed, False otherwise
        """
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            return False

        if not verify_password(current_password, user.get("hashed_password", "")):
            return False

        await self.user_repository.update(user_id, password=new_password)
        logger.info(f"Password changed for user ID: {user_id}")

        return True

    async def deactivate_user(self, user_id: str) -> Optional[dict]:
        """
        Deactivate a user account.

        Args:
            user_id: The user ID

        Returns:
            The updated user document or None
        """
        result = await self.user_repository.set_active(user_id, False)
        if result:
            logger.info(f"User deactivated: {user_id}")
        return result

    async def activate_user(self, user_id: str) -> Optional[dict]:
        """
        Activate a user account.

        Args:
            user_id: The user ID

        Returns:
            The updated user document or None
        """
        result = await self.user_repository.set_active(user_id, True)
        if result:
            logger.info(f"User activated: {user_id}")
        return result


# Service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the auth service instance."""
    return auth_service
