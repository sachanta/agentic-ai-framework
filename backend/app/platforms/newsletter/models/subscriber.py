"""
Subscriber model for the Newsletter Platform.

Represents an email subscriber with preferences and engagement data.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SubscriberStatus(str, Enum):
    """Subscriber status."""
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    PENDING = "pending"  # Awaiting confirmation


class SubscriberPreferences(BaseModel):
    """Subscriber preferences for newsletter content."""
    topics: List[str] = []
    tone: str = "professional"
    frequency: str = "weekly"  # daily, weekly, monthly
    include_mindmap: bool = True
    custom_prompt: Optional[str] = None


class EngagementMetrics(BaseModel):
    """Subscriber engagement metrics."""
    emails_received: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    last_opened_at: Optional[datetime] = None
    last_clicked_at: Optional[datetime] = None
    open_rate: float = 0.0
    click_rate: float = 0.0


class Subscriber(BaseModel):
    """
    Subscriber document model.

    Stores subscriber information, preferences, and engagement metrics.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str  # Owner of this subscriber list

    # Contact info
    email: str
    name: Optional[str] = None

    # Status
    status: str = SubscriberStatus.SUBSCRIBED

    # Preferences
    preferences: SubscriberPreferences = Field(default_factory=SubscriberPreferences)

    # Organization
    tags: List[str] = []
    groups: List[str] = []

    # Engagement
    engagement: EngagementMetrics = Field(default_factory=EngagementMetrics)

    # Metadata
    source: str = "manual"  # manual, import, api, signup
    metadata: Dict[str, Any] = {}

    # Timestamps
    subscribed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    unsubscribed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "use_enum_values": True,
    }
