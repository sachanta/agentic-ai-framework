"""
Preference API schemas for Newsletter Platform.

Pydantic models for preference endpoints.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PreferenceResponse(BaseModel):
    """User preferences response."""

    user_id: str = Field(..., description="User identifier")
    topics: List[str] = Field(default_factory=list, description="Preferred topics")
    tone: str = Field("professional", description="Preferred writing tone")
    frequency: str = Field("weekly", description="Newsletter frequency")
    max_articles: int = Field(10, description="Max articles per newsletter")
    preferred_sources: List[str] = Field(
        default_factory=list, description="Preferred sources"
    )
    excluded_sources: List[str] = Field(
        default_factory=list, description="Excluded sources"
    )
    include_summaries: bool = Field(True, description="Include AI summaries")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class PreferenceUpdateRequest(BaseModel):
    """Request to update user preferences."""

    topics: Optional[List[str]] = Field(None, description="Topics to set")
    tone: Optional[str] = Field(None, description="Tone to set")
    frequency: Optional[str] = Field(None, description="Frequency to set")
    max_articles: Optional[int] = Field(None, ge=1, le=30, description="Max articles")
    preferred_sources: Optional[List[str]] = Field(
        None, description="Preferred sources"
    )
    excluded_sources: Optional[List[str]] = Field(
        None, description="Excluded sources"
    )
    include_summaries: Optional[bool] = Field(None, description="Include summaries")


class EngagementRequest(BaseModel):
    """Request to record engagement data."""

    newsletter_id: str = Field(..., description="Newsletter identifier")
    opened: bool = Field(False, description="Was newsletter opened")
    clicked_links: List[str] = Field(
        default_factory=list, description="Links that were clicked"
    )
    read_time_seconds: int = Field(0, ge=0, description="Time spent reading")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating 1-5")
    feedback: Optional[str] = Field(None, description="Optional user feedback")


class InsightResponse(BaseModel):
    """A preference insight."""

    category: str = Field(..., description="Insight category")
    message: str = Field(..., description="Insight message")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
    action: Optional[str] = Field(None, description="Suggested action")


class AnalysisResponse(BaseModel):
    """Preference analysis response."""

    user_id: str = Field(..., description="User identifier")
    insights: List[InsightResponse] = Field(
        default_factory=list, description="Analysis insights"
    )
    engagement_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Engagement metrics summary"
    )


class RecommendationResponse(BaseModel):
    """A preference recommendation."""

    field: str = Field(..., description="Preference field")
    current_value: Optional[Any] = Field(None, description="Current value")
    recommended_value: Any = Field(..., description="Recommended value")
    reason: str = Field(..., description="Reason for recommendation")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")


class RecommendationsListResponse(BaseModel):
    """List of preference recommendations."""

    user_id: str = Field(..., description="User identifier")
    recommendations: List[RecommendationResponse] = Field(
        default_factory=list, description="Recommendations"
    )


class PreferenceActionResponse(BaseModel):
    """Generic response for preference actions."""

    success: bool = Field(..., description="Whether action succeeded")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if failed")
