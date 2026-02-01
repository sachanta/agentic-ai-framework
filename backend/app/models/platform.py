"""
Platform model for database storage.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PlatformModel(BaseModel):
    """Platform document model for MongoDB."""

    id: Optional[str] = Field(default=None, alias="_id")
    platform_id: str
    name: str
    description: str
    version: str
    status: str = "active"  # active, inactive, maintenance
    agents: List[str] = []
    config: Dict[str, Any] = {}
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class AgentModel(BaseModel):
    """Agent document model for MongoDB."""

    id: Optional[str] = Field(default=None, alias="_id")
    agent_id: str
    platform_id: str
    name: str
    description: str
    status: str = "active"  # active, inactive, error
    config: Dict[str, Any] = {}
    capabilities: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
