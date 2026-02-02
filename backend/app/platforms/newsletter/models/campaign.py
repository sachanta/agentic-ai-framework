"""
Campaign model for the Newsletter Platform.

Represents an email campaign with targeting, scheduling, and analytics.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CampaignStatus(str, Enum):
    """Campaign status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    FAILED = "failed"


class CampaignAnalytics(BaseModel):
    """Campaign delivery and engagement analytics."""
    recipient_count: int = 0
    delivered_count: int = 0
    bounced_count: int = 0
    open_count: int = 0
    unique_open_count: int = 0
    click_count: int = 0
    unique_click_count: int = 0
    unsubscribe_count: int = 0
    spam_count: int = 0

    # Rates (calculated)
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribe_rate: float = 0.0


class Campaign(BaseModel):
    """
    Campaign document model.

    Stores campaign configuration, targeting, and delivery analytics.
    """
    id: Optional[str] = Field(None, alias="_id")
    user_id: str

    # Campaign info
    name: str
    description: Optional[str] = None
    subject: str
    preview_text: Optional[str] = None

    # Content
    newsletter_id: Optional[str] = None  # Associated newsletter
    template_id: Optional[str] = None  # Template used

    # Status
    status: str = CampaignStatus.DRAFT

    # Targeting
    subscriber_tags: List[str] = []  # Send to subscribers with these tags
    subscriber_groups: List[str] = []  # Send to subscribers in these groups
    exclude_tags: List[str] = []  # Exclude subscribers with these tags

    # Scheduling
    scheduled_at: Optional[datetime] = None
    send_timezone: str = "UTC"

    # Delivery
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None

    # Analytics
    analytics: CampaignAnalytics = Field(default_factory=CampaignAnalytics)

    # Metadata
    metadata: Dict[str, Any] = {}

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {
        "populate_by_name": True,
        "json_encoders": {datetime: lambda v: v.isoformat()},
        "use_enum_values": True,
    }
