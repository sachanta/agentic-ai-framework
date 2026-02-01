"""
Agent schemas.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class AgentCreate(BaseModel):
    """Schema for creating an agent."""

    name: str
    description: str
    type: str
    model: str = "gpt-4"
    system_prompt: Optional[str] = None
    tools: List[str] = []
    capabilities: List[str] = []
    config: Dict[str, Any] = {}


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""

    id: str
    name: str
    description: str
    type: str
    status: str
    model: str
    system_prompt: Optional[str]
    tools: List[str]
    capabilities: List[str]
    config: Dict[str, Any]
    platform_id: Optional[str]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True
