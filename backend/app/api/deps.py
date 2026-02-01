"""
Shared dependencies for API endpoints.

These dependencies are used across all endpoints and platforms.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.db.mongodb import get_database
from app.db.weaviate import get_weaviate_client
from app.core.security import get_current_user as _get_current_user

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


async def get_db():
    """
    Get MongoDB database instance.

    Usage:
        @router.get("/items")
        async def get_items(db = Depends(get_db)):
            return await db.items.find().to_list(100)
    """
    return get_database()


async def get_weaviate():
    """
    Get Weaviate client instance.

    Usage:
        @router.get("/search")
        async def search(client = Depends(get_weaviate)):
            return client.query.get("Collection").do()
    """
    return get_weaviate_client()


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current authenticated user.

    Usage:
        @router.get("/me")
        async def get_me(user = Depends(get_current_user)):
            return user
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await _get_current_user(token)


async def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme)):
    """
    Get the current user if authenticated, otherwise None.

    Usage:
        @router.get("/public")
        async def public_endpoint(user = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello, {user['username']}"}
            return {"message": "Hello, guest"}
    """
    if not token:
        return None
    try:
        return await _get_current_user(token)
    except HTTPException:
        return None


async def require_admin(user: dict = Depends(get_current_user)):
    """
    Require the current user to be an admin.

    Usage:
        @router.delete("/users/{id}")
        async def delete_user(id: str, admin = Depends(require_admin)):
            # Only admins can delete users
            pass
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_role(required_role: str):
    """
    Factory for role-based access control.

    Usage:
        @router.post("/reports")
        async def create_report(user = Depends(require_role("analyst"))):
            pass
    """
    async def check_role(user: dict = Depends(get_current_user)):
        if user.get("role") != required_role and user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user
    return check_role
