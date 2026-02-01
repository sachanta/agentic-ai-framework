"""
Log API schemas.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class LogEntry(BaseModel):
    """Log entry response schema."""
    id: str
    timestamp: datetime
    level: str
    source: str
    message: str
    details: Dict[str, Any] = {}
    user_id: Optional[str] = None
    platform_id: Optional[str] = None
    agent_id: Optional[str] = None
    execution_id: Optional[str] = None
    trace_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class LogListResponse(BaseModel):
    """Paginated log list response."""
    items: List[LogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int


class LogStatsResponse(BaseModel):
    """Log statistics response."""
    total: int
    by_level: Dict[str, int]
    by_source: Dict[str, int]
    recent_errors: List[LogEntry] = []


class CreateLogRequest(BaseModel):
    """Request to create a log entry."""
    level: str = "info"
    source: str = "system"
    message: str
    details: Dict[str, Any] = {}
    platform_id: Optional[str] = None
    agent_id: Optional[str] = None
    execution_id: Optional[str] = None


class LogFilterParams(BaseModel):
    """Parameters for filtering logs."""
    page: int = 1
    page_size: int = 50
    level: Optional[str] = None
    source: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    platform_id: Optional[str] = None
    agent_id: Optional[str] = None
    search: Optional[str] = None
