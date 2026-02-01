"""
Execution model.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    """A step execution result."""

    step_id: str
    status: str  # "pending", "running", "completed", "failed"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input: Dict[str, Any] = {}
    output: Dict[str, Any] = {}
    error: Optional[str] = None


class Execution(BaseModel):
    """Execution model representing a workflow/agent execution."""

    id: Optional[str] = Field(None, alias="_id")
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    platform_id: Optional[str] = None
    status: str = "pending"  # "pending", "running", "completed", "failed", "cancelled"
    input: Dict[str, Any] = {}
    output: Dict[str, Any] = {}
    steps: List[ExecutionStep] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
