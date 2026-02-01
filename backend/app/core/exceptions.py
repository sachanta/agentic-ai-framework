"""
Custom exceptions for the application.
"""
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Resource not found error."""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id '{resource_id}' not found",
        )


class ValidationError(HTTPException):
    """Validation error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class AuthenticationError(HTTPException):
    """Authentication error."""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Authorization error."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class PlatformError(Exception):
    """Base exception for platform errors."""

    def __init__(self, message: str, platform: str):
        self.message = message
        self.platform = platform
        super().__init__(self.message)


class AgentError(Exception):
    """Base exception for agent errors."""

    def __init__(self, message: str, agent: str):
        self.message = message
        self.agent = agent
        super().__init__(self.message)
