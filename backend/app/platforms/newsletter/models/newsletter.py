"""
Newsletter model for the Newsletter Platform.

Represents a generated newsletter with content, status, and metadata.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NewsletterStatus(str, Enum):
    """Newsletter generation and delivery status."""
    DRAFT = "draft"
    GENERATING = "generating"
    PENDING_REVIEW = "pending_review"
    READY = "ready"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class Newsletter(BaseModel):
    """
    Newsletter document model.

    Stores generated newsletter content, research data, and delivery status.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str

    # Content
    title: str
    content: str = ""  # Markdown content
    html_content: str = ""  # Rendered HTML
    plain_text: str = ""  # Plain text version
    subject_line: Optional[str] = None
    subject_line_options: List[str] = []

    # Status
    status: str = NewsletterStatus.DRAFT
    workflow_id: Optional[str] = None  # LangGraph workflow ID

    # Generation metadata
    topics_covered: List[str] = []
    tone_used: str = "professional"
    word_count: int = 0
    read_time_minutes: int = 0

    # Agent outputs
    research_data: Dict[str, Any] = {}
    writing_data: Dict[str, Any] = {}

    # Delivery
    sent_to_count: int = 0
    campaign_id: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "use_enum_values": True,
    }
