"""
Tool schemas.
"""
from typing import Optional, Dict, Any, List
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


# ---------------------------------------------------------------------------
# Tools Studio schemas
# ---------------------------------------------------------------------------


class ToolStudioParameter(BaseModel):
    """Schema for a single tool parameter."""

    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None


class ToolStudioSummary(BaseModel):
    """Lightweight summary for catalog grid cards."""

    tool_id: str
    name: str
    display_name: str
    category: str
    platform_id: str
    service_class: str
    description: str
    parameter_count: int
    status: str = "available"


class ToolStudioDetail(ToolStudioSummary):
    """Full detail for inspector page."""

    parameters: List[ToolStudioParameter] = []
    returns: Optional[str] = None
    requires: List[str] = []


class ToolStudioListResponse(BaseModel):
    """Response for listing tools."""

    tools: List[ToolStudioSummary]
    total: int
    categories: List[str]


class ToolStudioTryRequest(BaseModel):
    """Request body for trying a tool."""

    parameters: Dict[str, Any] = {}


class ToolStudioTryResponse(BaseModel):
    """Response from tool execution."""

    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float
    tool_id: str
