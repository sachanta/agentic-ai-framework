"""
Tool model.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Tool model representing a callable tool for agents."""

    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: str
    type: str  # "api", "function", "system"
    schema: Dict[str, Any] = {}  # JSON schema for parameters
    enabled: bool = True
    config: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
