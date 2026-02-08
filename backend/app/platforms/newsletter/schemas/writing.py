"""
Writing API schemas for Newsletter Platform.

Phase 7: Writing Agent API schemas.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .research import ArticleResponse


class GenerateRequest(BaseModel):
    """Request schema for newsletter generation."""
    articles: List[Dict[str, Any]] = Field(
        ...,
        min_length=1,
        description="Selected articles to include in newsletter"
    )
    tone: str = Field(
        "professional",
        description="Writing tone: professional, casual, formal, enthusiastic"
    )
    user_id: Optional[str] = Field(None, description="User ID for RAG personalization")
    include_rag: bool = Field(True, description="Use RAG for style examples")


class SubjectLine(BaseModel):
    """A single subject line option."""
    text: str = Field(..., description="The subject line text")
    style: str = Field(..., description="Style: curiosity, benefit, urgency, question, trend")


class NewsletterContent(BaseModel):
    """Generated newsletter content."""
    content: str = Field(..., description="Newsletter content in markdown")
    word_count: int = Field(0, description="Word count of content")


class NewsletterFormats(BaseModel):
    """Newsletter in multiple formats."""
    html: str = Field(..., description="HTML formatted newsletter")
    text: str = Field(..., description="Plain text version")
    markdown: str = Field(..., description="Markdown version")


class NewsletterSummary(BaseModel):
    """Newsletter summary with bullet points."""
    bullets: List[str] = Field(default_factory=list, description="Summary bullet points")
    raw: Optional[str] = Field(None, description="Raw summary text")


class GenerateMetadata(BaseModel):
    """Metadata about the generation."""
    article_count: int = Field(0, description="Number of articles used")
    topics: List[str] = Field(default_factory=list, description="Topics covered")
    tone: str = Field("professional", description="Tone used")
    generated_at: datetime = Field(default_factory=datetime.now)
    rag_examples_used: int = Field(0, description="Number of RAG examples used")


class GenerateResponse(BaseModel):
    """Response schema for newsletter generation."""
    success: bool
    newsletter: Optional[NewsletterContent] = None
    subject_lines: List[SubjectLine] = Field(default_factory=list)
    summary: Optional[NewsletterSummary] = None
    formats: Optional[NewsletterFormats] = None
    metadata: Optional[GenerateMetadata] = None
    error: Optional[str] = None


class RegenerateRequest(BaseModel):
    """Request to regenerate with feedback."""
    articles: List[Dict[str, Any]] = Field(..., min_length=1)
    tone: str = Field("professional")
    feedback: str = Field(..., description="User feedback for regeneration")
    previous_content: Optional[str] = Field(None, description="Previous content to improve")


__all__ = [
    "GenerateRequest",
    "SubjectLine",
    "NewsletterContent",
    "NewsletterFormats",
    "NewsletterSummary",
    "GenerateMetadata",
    "GenerateResponse",
    "RegenerateRequest",
]
