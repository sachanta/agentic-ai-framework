"""
Tool schemas.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ToolCreate(BaseModel):
    """Schema for creating a tool."""

    name: str
    description: str
    type: str
    schema: Dict[str, Any] = {}
    enabled: bool = True
    config: Dict[str, Any] = {}


class ToolUpdate(BaseModel):
    """Schema for updating a tool."""

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    schema: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class ToolResponse(BaseModel):
    """Schema for tool response."""

    id: str
    name: str
    description: str
    type: str
    schema: Dict[str, Any]
    enabled: bool
    config: Dict[str, Any]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True
