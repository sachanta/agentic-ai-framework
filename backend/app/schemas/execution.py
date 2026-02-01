"""
Execution schemas.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ExecutionStepResponse(BaseModel):
    """Schema for execution step response."""

    step_id: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    input: Dict[str, Any]
    output: Dict[str, Any]
    error: Optional[str]


class ExecutionResponse(BaseModel):
    """Schema for execution response."""

    id: str
    workflow_id: Optional[str]
    agent_id: Optional[str]
    platform_id: Optional[str]
    status: str
    input: Dict[str, Any]
    output: Dict[str, Any]
    steps: List[ExecutionStepResponse]
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True
