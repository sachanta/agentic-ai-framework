"""
Preference Agent schemas.

Defines user preferences, updates, and engagement tracking.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """User newsletter preferences."""

    user_id: str = Field(..., description="Unique user identifier")
    topics: List[str] = Field(default_factory=list, description="Interested topics")
    tone: str = Field("professional", description="Preferred writing tone")
    frequency: str = Field("weekly", description="Newsletter frequency")
    max_articles: int = Field(10, ge=1, le=30, description="Max articles per newsletter")
    include_summaries: bool = Field(True, description="Include AI summaries")
    include_mindmap: bool = Field(True, description="Include visual mindmap")
    sources_blacklist: List[str] = Field(default_factory=list, description="Blocked sources")
    sources_whitelist: List[str] = Field(default_factory=list, description="Preferred sources")
    language: str = Field("en", description="Content language")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserPreferences":
        """Create from dictionary."""
        return cls(**data)


class PreferenceUpdate(BaseModel):
    """Partial update for user preferences."""

    topics: Optional[List[str]] = None
    tone: Optional[str] = None
    frequency: Optional[str] = None
    max_articles: Optional[int] = Field(None, ge=1, le=30)
    include_summaries: Optional[bool] = None
    include_mindmap: Optional[bool] = None
    sources_blacklist: Optional[List[str]] = None
    sources_whitelist: Optional[List[str]] = None
    language: Optional[str] = None

    def get_updates(self) -> Dict[str, Any]:
        """Get non-None fields as dictionary."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class EngagementData(BaseModel):
    """Newsletter engagement tracking."""

    newsletter_id: str = Field(..., description="Newsletter identifier")
    user_id: str = Field(..., description="User identifier")
    opened: bool = Field(False, description="Was email opened")
    clicked_links: List[str] = Field(default_factory=list, description="Clicked article URLs")
    read_time_seconds: int = Field(0, ge=0, description="Time spent reading")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating 1-5")
    feedback: Optional[str] = Field(None, description="User feedback text")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }


class PreferenceInsight(BaseModel):
    """Insight from preference analysis."""

    category: str = Field(..., description="Insight category")
    message: str = Field(..., description="Human-readable insight")
    data: Dict[str, Any] = Field(default_factory=dict, description="Supporting data")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


class PreferenceRecommendation(BaseModel):
    """Recommendation for preference changes."""

    field: str = Field(..., description="Preference field to update")
    current_value: Any = Field(..., description="Current value")
    recommended_value: Any = Field(..., description="Recommended new value")
    reason: str = Field(..., description="Why this change is recommended")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


class PreferenceAnalysisResult(BaseModel):
    """Result of preference analysis."""

    user_id: str
    insights: List[PreferenceInsight] = Field(default_factory=list)
    recommendations: List[PreferenceRecommendation] = Field(default_factory=list)
    engagement_summary: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = [
    "UserPreferences",
    "PreferenceUpdate",
    "EngagementData",
    "PreferenceInsight",
    "PreferenceRecommendation",
    "PreferenceAnalysisResult",
]
