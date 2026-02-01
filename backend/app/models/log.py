"""
Log model for database storage.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogSource(str, Enum):
    """Log source enumeration."""
    SYSTEM = "system"
    API = "api"
    AGENT = "agent"
    ORCHESTRATOR = "orchestrator"
    PLATFORM = "platform"
    AUTH = "auth"
    DATABASE = "database"
    LLM = "llm"


class LogModel(BaseModel):
    """Log document model for MongoDB."""

    id: Optional[str] = Field(default=None, alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = LogLevel.INFO
    source: str = LogSource.SYSTEM
    message: str
    details: Dict[str, Any] = {}
    user_id: Optional[str] = None
    platform_id: Optional[str] = None
    agent_id: Optional[str] = None
    execution_id: Optional[str] = None
    trace_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    stack_trace: Optional[str] = None

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class LogStats(BaseModel):
    """Log statistics model."""

    total: int = 0
    by_level: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    recent_errors: List[Dict[str, Any]] = []
