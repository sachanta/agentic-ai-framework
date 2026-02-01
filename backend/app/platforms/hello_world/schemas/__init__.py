"""
Hello World Platform schemas.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class GreetRequest(BaseModel):
    """Request schema for greeting generation."""

    name: str
    style: str = "friendly"  # friendly, formal, casual, enthusiastic


class GreetResponse(BaseModel):
    """Response schema for greeting generation."""

    greeting: str
    agent: str
    metadata: Dict[str, Any] = {}


class PlatformStatusResponse(BaseModel):
    """Response schema for platform status."""

    platform_id: str
    name: str
    status: str
    agents: List[str]
    version: str


class AgentInfo(BaseModel):
    """Schema for agent information."""

    id: str
    name: str
    description: str
    status: str


__all__ = [
    "GreetRequest",
    "GreetResponse",
    "PlatformStatusResponse",
    "AgentInfo",
]
