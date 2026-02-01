"""
User model.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """User model for authentication and authorization."""

    id: Optional[str] = Field(None, alias="_id")
    username: str
    email: str
    hashed_password: str
    role: str = "user"  # "admin" or "user"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
