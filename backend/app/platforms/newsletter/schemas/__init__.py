"""
Newsletter Platform schemas.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr


class NewsletterStatus(str, Enum):
    """Newsletter status values."""
    DRAFT = "draft"
    GENERATING = "generating"
    PENDING_REVIEW = "pending_review"
    READY = "ready"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class Tone(str, Enum):
    """Newsletter tone options."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FORMAL = "formal"
    ENTHUSIASTIC = "enthusiastic"


class Frequency(str, Enum):
    """Newsletter frequency options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


# Request schemas
class GenerateNewsletterRequest(BaseModel):
    """Request schema for newsletter generation."""
    topics: List[str]
    tone: Tone = Tone.PROFESSIONAL
    max_articles: int = 10
    custom_prompt: Optional[str] = None
    include_mindmap: bool = True


class CustomPromptRequest(BaseModel):
    """Request schema for custom prompt newsletter generation."""
    prompt: str
    include_mindmap: bool = True


# Response schemas
class GenerateNewsletterResponse(BaseModel):
    """Response schema for newsletter generation initiation."""
    workflow_id: str
    status: str
    message: str


class NewsletterResponse(BaseModel):
    """Response schema for a newsletter."""
    id: str
    title: str
    content: Optional[str] = None
    html_content: Optional[str] = None
    plain_text: Optional[str] = None
    status: NewsletterStatus
    topics_covered: List[str] = []
    tone: Tone
    word_count: int = 0
    read_time_minutes: int = 0
    mindmap_markdown: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None


class PlatformStatusResponse(BaseModel):
    """Response schema for platform status."""
    platform_id: str
    name: str
    status: str
    agents: List[str]
    version: str
    llm_provider: str
    llm_model: str


class AgentInfo(BaseModel):
    """Schema for agent information."""
    id: str
    name: str
    description: str
    status: str


class WorkflowStatusResponse(BaseModel):
    """Response schema for workflow status."""
    workflow_id: str
    status: str  # running, awaiting_approval, completed, cancelled, failed
    current_checkpoint: Optional[str] = None
    checkpoint_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CheckpointResponse(BaseModel):
    """Response schema for checkpoint details."""
    checkpoint_id: str
    checkpoint_type: str
    title: str
    description: str
    data: Dict[str, Any]
    actions: List[str]
    metadata: Dict[str, Any] = {}


class ApproveCheckpointRequest(BaseModel):
    """Request schema for checkpoint approval."""
    checkpoint_id: str
    action: str  # approve, edit, reject
    modifications: Optional[Dict[str, Any]] = None
    feedback: Optional[str] = None


from app.platforms.newsletter.schemas.research import (
    ResearchRequest,
    CustomResearchRequest,
    TrendingRequest,
    ArticleResponse,
    ResearchMetadata,
    ResearchResponse,
)

__all__ = [
    "NewsletterStatus",
    "Tone",
    "Frequency",
    "GenerateNewsletterRequest",
    "CustomPromptRequest",
    "GenerateNewsletterResponse",
    "NewsletterResponse",
    "PlatformStatusResponse",
    "AgentInfo",
    "WorkflowStatusResponse",
    "CheckpointResponse",
    "ApproveCheckpointRequest",
    # Research schemas (Phase 6A)
    "ResearchRequest",
    "CustomResearchRequest",
    "TrendingRequest",
    "ArticleResponse",
    "ResearchMetadata",
    "ResearchResponse",
]
