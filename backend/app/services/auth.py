"""
Authentication service.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from jose import JWTError, jwt

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
        status: str = "approved",
        is_active: bool = True,
        platforms: Optional[List[str]] = None,
    ) -> dict:
        """
        Create a new user.

        Args:
            username: The username
            email: The email address
            password: The plain text password
            role: The user role (default: "user")
            status: Approval status (default: "approved")
            is_active: Whether the user is active (default: True)
            platforms: Platform access list (default: None = unrestricted)

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
            is_active=is_active,
            status=status,
            platforms=platforms,
        )

        logger.info(f"Created new user: {username} ({role}, status={status})")

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

    async def approve_user(self, user_id: str) -> Optional[dict]:
        """
        Approve a pending user account.

        Sets status to 'approved' and is_active to True.

        Args:
            user_id: The user ID

        Returns:
            The updated user document or None
        """
        user = await self.user_repository.set_status(user_id, "approved")
        if user:
            user = await self.user_repository.set_active(user_id, True)
            logger.info(f"User approved: {user_id} ({user.get('email')})")
        return user

    async def reject_user(self, user_id: str) -> Optional[dict]:
        """
        Reject a pending user account.

        Sets status to 'rejected'.

        Args:
            user_id: The user ID

        Returns:
            The updated user document or None
        """
        user = await self.user_repository.set_status(user_id, "rejected")
        if user:
            logger.info(f"User rejected: {user_id} ({user.get('email')})")
        return user

    async def list_users_by_status(self, status: str) -> List[dict]:
        """
        List users filtered by approval status.

        Args:
            status: The status to filter by (pending, approved, rejected)

        Returns:
            List of user documents
        """
        return await self.user_repository.find_by_status(status)

    def _create_approval_token(self, user_id: str, action: str) -> str:
        """
        Create a signed JWT for email-based approve/reject links.

        Args:
            user_id: The user ID to approve/reject
            action: The action ('approve' or 'reject')

        Returns:
            Signed JWT string
        """
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS
        )
        payload = {
            "sub": user_id,
            "action": action,
            "type": "approval",
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def approve_user_by_token(self, token: str) -> Optional[dict]:
        """
        Decode a signed approval token and approve the user.

        Args:
            token: The signed JWT approval token

        Returns:
            The approved user document or None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "approval" or payload.get("action") != "approve":
                return None
            user_id = payload.get("sub")
            if not user_id:
                return None
            return await self.approve_user(user_id)
        except JWTError as e:
            logger.warning(f"Invalid approval token: {e}")
            return None

    async def reject_user_by_token(self, token: str) -> Optional[dict]:
        """
        Decode a signed rejection token and reject the user.

        Args:
            token: The signed JWT rejection token

        Returns:
            The rejected user document or None if invalid/expired
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "approval" or payload.get("action") != "reject":
                return None
            user_id = payload.get("sub")
            if not user_id:
                return None
            return await self.reject_user(user_id)
        except JWTError as e:
            logger.warning(f"Invalid rejection token: {e}")
            return None

    async def send_approval_email(self, user: dict) -> None:
        """
        Send an approval request email to the admin.

        Creates signed approve/reject tokens and sends an HTML email
        with one-click links to the configured admin email.

        Args:
            user: The newly registered user document
        """
        try:
            from app.services.email import get_system_email_service

            email_service = get_system_email_service()

            user_id = user.get("id", "")
            user_email = user.get("email", "")
            user_platforms = ", ".join(user.get("platforms", [])) or "none specified"

            approve_token = self._create_approval_token(user_id, "approve")
            reject_token = self._create_approval_token(user_id, "reject")

            base_url = settings.APP_BASE_URL.rstrip("/")
            approve_url = f"{base_url}{settings.API_V1_PREFIX}/auth/approve?token={approve_token}"
            reject_url = f"{base_url}{settings.API_V1_PREFIX}/auth/reject?token={reject_token}"

            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">New Signup Request</h2>
                <p>A new user has requested access to the Agentic AI Framework.</p>
                <table style="border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px 16px; font-weight: bold; color: #555;">Email:</td>
                        <td style="padding: 8px 16px;">{user_email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 16px; font-weight: bold; color: #555;">Platform(s):</td>
                        <td style="padding: 8px 16px;">{user_platforms}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 16px; font-weight: bold; color: #555;">Requested:</td>
                        <td style="padding: 8px 16px;">{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</td>
                    </tr>
                </table>
                <div style="margin: 30px 0;">
                    <a href="{approve_url}"
                       style="display: inline-block; padding: 12px 24px; background-color: #22c55e; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin-right: 12px;">
                        Approve
                    </a>
                    <a href="{reject_url}"
                       style="display: inline-block; padding: 12px 24px; background-color: #ef4444; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        Reject
                    </a>
                </div>
                <p style="color: #888; font-size: 13px; margin-top: 30px;">
                    You can also manage pending users from the admin panel:<br>
                    <a href="{base_url}/settings">{base_url}/settings</a>
                </p>
                <p style="color: #aaa; font-size: 11px;">
                    These links expire in {settings.SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS} days.
                </p>
            </body>
            </html>
            """

            plain_text = f"""New Signup Request

A new user has requested access to the Agentic AI Framework.

Email: {user_email}
Platform(s): {user_platforms}
Requested: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

Approve: {approve_url}
Reject: {reject_url}

You can also manage pending users from the admin panel:
{base_url}/settings

These links expire in {settings.SIGNUP_APPROVAL_TOKEN_EXPIRY_DAYS} days.
"""

            result = await email_service.send_email(
                to=settings.SIGNUP_APPROVAL_EMAIL,
                subject=f"New signup request — {user_email}",
                html_content=html_content,
                plain_text=plain_text,
                tags=["signup-approval"],
            )

            if result["success"]:
                logger.info(f"Approval email sent for user {user_email}")
            else:
                logger.error(f"Failed to send approval email for {user_email}: {result['error']}")

        except Exception as e:
            logger.error(f"Error sending approval email: {e}")


# Service instance
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """Get the auth service instance."""
    return auth_service
