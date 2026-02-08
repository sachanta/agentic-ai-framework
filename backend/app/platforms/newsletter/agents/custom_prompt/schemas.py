"""
Custom Prompt Agent schemas.

Defines prompt analysis and extracted parameters.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PromptAnalysis(BaseModel):
    """Analysis of a natural language prompt."""

    original_prompt: str = Field(..., description="The original user prompt")
    intent: str = Field(
        "research",
        description="Detected intent: research, summarize, analyze, compare, generate"
    )
    topics: List[str] = Field(default_factory=list, description="Extracted topics")
    tone: Optional[str] = Field(None, description="Detected tone preference")
    constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detected constraints (max_words, format, etc.)"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Specific aspects to emphasize"
    )
    exclusions: List[str] = Field(
        default_factory=list,
        description="Things to avoid or exclude"
    )
    time_range: Optional[str] = Field(
        None,
        description="Time range mentioned (e.g., 'this week', 'last month')"
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the analysis"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "original_prompt": "Write about AI in healthcare, keep it professional",
                    "intent": "research",
                    "topics": ["AI", "healthcare"],
                    "tone": "professional",
                    "constraints": {},
                    "focus_areas": ["medical AI"],
                    "exclusions": [],
                    "confidence": 0.9,
                }
            ]
        }
    }


class ExtractedParameters(BaseModel):
    """Parameters extracted from prompt for research/writing."""

    topics: List[str] = Field(default_factory=list, description="Topics to research")
    tone: str = Field("professional", description="Writing tone")
    max_articles: int = Field(10, ge=1, le=30, description="Max articles to find")
    max_word_count: Optional[int] = Field(None, description="Max newsletter words")
    focus_areas: List[str] = Field(default_factory=list, description="Focus areas")
    time_range_days: int = Field(7, ge=1, le=30, description="Days to look back")
    include_summaries: bool = Field(True, description="Include AI summaries")
    source_preferences: List[str] = Field(
        default_factory=list,
        description="Preferred sources"
    )
    exclusions: List[str] = Field(default_factory=list, description="Topics to exclude")

    def to_research_params(self) -> Dict[str, Any]:
        """Convert to ResearchAgent parameters."""
        return {
            "topics": self.topics,
            "max_results": self.max_articles,
            "include_summaries": self.include_summaries,
            "days_back": self.time_range_days,
        }

    def to_writing_params(self) -> Dict[str, Any]:
        """Convert to WritingAgent parameters."""
        return {
            "tone": self.tone,
            "max_word_count": self.max_word_count,
            "focus_areas": self.focus_areas,
        }


class ValidationResult(BaseModel):
    """Result of parameter validation."""

    valid: bool = Field(..., description="Whether parameters are valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improvement"
    )


class EnhancedPrompt(BaseModel):
    """Prompt enhanced with user context."""

    original_prompt: str = Field(..., description="Original prompt")
    enhanced_prompt: str = Field(..., description="Enhanced prompt with context")
    added_context: List[str] = Field(
        default_factory=list,
        description="Context items added"
    )
    user_preferences_applied: bool = Field(
        False,
        description="Whether user preferences were applied"
    )


__all__ = [
    "PromptAnalysis",
    "ExtractedParameters",
    "ValidationResult",
    "EnhancedPrompt",
]
