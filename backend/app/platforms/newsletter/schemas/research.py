"""
Research API schemas for Newsletter Platform.

Phase 6A: Backend API for testing Research Agent.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """Request schema for topic-based research."""
    topics: List[str] = Field(..., min_length=1, description="Topics to research")
    max_results: int = Field(10, ge=1, le=50, description="Maximum articles to return")
    include_summaries: bool = Field(True, description="Generate AI summaries")
    days_back: int = Field(3, ge=1, le=30, description="Search articles from last N days")


class CustomResearchRequest(BaseModel):
    """Request schema for custom prompt research."""
    prompt: str = Field(..., min_length=3, description="Natural language search prompt")
    max_results: int = Field(10, ge=1, le=50)
    include_summaries: bool = True


class TrendingRequest(BaseModel):
    """Request schema for trending content."""
    topics: List[str] = Field(..., min_length=1)
    max_results: int = Field(10, ge=1, le=50)


class ArticleResponse(BaseModel):
    """Schema for a single article in research results."""
    title: str
    url: str
    source: str
    content: Optional[str] = None
    summary: Optional[str] = None
    key_takeaway: Optional[str] = None
    published_date: Optional[datetime] = None
    score: float = Field(0.0, description="Relevance score from search")
    relevance_score: float = Field(0.0, description="Calculated relevance score")
    quality_score: float = Field(0.0, description="Content quality score")
    recency_boost: float = Field(0.0, description="Recency boost applied")

    model_config = {
        "from_attributes": True,
    }


class ResearchMetadata(BaseModel):
    """Metadata about the research results."""
    topics: List[str]
    total_found: int = 0
    after_filter: int = 0
    source: str = "tavily"
    cached: bool = False
    message: Optional[str] = None


class ResearchResponse(BaseModel):
    """Response schema for research endpoints."""
    success: bool
    articles: List[ArticleResponse] = []
    metadata: ResearchMetadata
    error: Optional[str] = None


__all__ = [
    "ResearchRequest",
    "CustomResearchRequest",
    "TrendingRequest",
    "ArticleResponse",
    "ResearchMetadata",
    "ResearchResponse",
]
