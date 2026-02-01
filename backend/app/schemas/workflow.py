"""
Workflow schemas.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class WorkflowStepSchema(BaseModel):
    """Schema for a workflow step."""

    id: str
    name: str
    type: str
    config: Dict[str, Any] = {}
    next_steps: List[str] = []


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""

    name: str
    description: str
    steps: List[WorkflowStepSchema] = []
    trigger: Dict[str, Any] = {}
    config: Dict[str, Any] = {}


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    steps: Optional[List[WorkflowStepSchema]] = None
    trigger: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""

    id: str
    name: str
    description: str
    status: str
    steps: List[WorkflowStepSchema]
    trigger: Dict[str, Any]
    config: Dict[str, Any]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True
