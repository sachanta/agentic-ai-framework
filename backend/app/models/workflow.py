"""
Workflow model.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    """A step in a workflow."""

    id: str
    name: str
    type: str  # "agent", "tool", "condition", "parallel"
    config: Dict[str, Any] = {}
    next_steps: List[str] = []


class Workflow(BaseModel):
    """Workflow model representing a sequence of agent/tool operations."""

    id: Optional[str] = Field(None, alias="_id")
    name: str
    description: str
    status: str = "draft"  # "draft", "active", "archived"
    steps: List[WorkflowStep] = []
    trigger: Dict[str, Any] = {}  # "manual", "scheduled", "event"
    config: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
