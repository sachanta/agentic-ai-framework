"""
Authentication schemas.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    expires_at: str


class UserCreate(BaseModel):
    """Schema for creating a user."""

    username: str
    email: EmailStr
    password: str
    role: str = "user"


class UserResponse(BaseModel):
    """Schema for user response (excludes password)."""

    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True
