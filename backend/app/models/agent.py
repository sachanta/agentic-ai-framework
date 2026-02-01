"""
Agent model.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Agent model representing an AI agent."""

    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: str
    type: str  # "assistant", "researcher", "coder", etc.
    status: str = "inactive"  # "active", "inactive", "error"
    model: str = "gpt-4"
    system_prompt: Optional[str] = None
    tools: List[str] = []
    capabilities: List[str] = []
    config: Dict[str, Any] = {}
    platform_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
