"""
Platform API schemas.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Agent response schema."""
    id: str
    name: str
    description: str
    status: str
    capabilities: List[str] = []


class PlatformResponse(BaseModel):
    """Platform response schema."""
    id: str
    name: str
    description: str
    version: str
    status: str
    agents: List[str]
    enabled: bool = True


class PlatformDetailResponse(BaseModel):
    """Detailed platform response schema."""
    id: str
    name: str
    description: str
    version: str
    status: str
    agents: List[AgentResponse]
    config: Dict[str, Any] = {}
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PlatformListResponse(BaseModel):
    """List of platforms response."""
    items: List[PlatformResponse]
    total: int


class PlatformExecuteRequest(BaseModel):
    """Platform execution request schema."""
    input: Dict[str, Any]
    options: Dict[str, Any] = {}


class PlatformExecuteResponse(BaseModel):
    """Platform execution response schema."""
    success: bool
    result: Dict[str, Any]
    execution_id: Optional[str] = None
    duration_ms: Optional[float] = None
