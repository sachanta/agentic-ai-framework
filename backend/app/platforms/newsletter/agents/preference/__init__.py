"""
Preference Agent package.

Manages user preferences and learns from engagement patterns.
"""
from app.platforms.newsletter.agents.preference.agent import PreferenceAgent
from app.platforms.newsletter.agents.preference.schemas import (
    UserPreferences,
    PreferenceUpdate,
    EngagementData,
    PreferenceInsight,
    PreferenceRecommendation,
    PreferenceAnalysisResult,
)
from app.platforms.newsletter.agents.preference.llm import (
    get_preference_llm,
    get_preference_config,
    get_analysis_config,
    get_recommendation_config,
)
from app.platforms.newsletter.agents.preference.prompts import (
    PREFERENCE_SYSTEM_PROMPT,
    ANALYZE_PREFERENCES_PROMPT,
    RECOMMEND_PREFERENCES_PROMPT,
    LEARN_FROM_ENGAGEMENT_PROMPT,
    format_preferences_for_prompt,
    format_engagement_history,
)

__all__ = [
    # Agent
    "PreferenceAgent",
    # Schemas
    "UserPreferences",
    "PreferenceUpdate",
    "EngagementData",
    "PreferenceInsight",
    "PreferenceRecommendation",
    "PreferenceAnalysisResult",
    # LLM
    "get_preference_llm",
    "get_preference_config",
    "get_analysis_config",
    "get_recommendation_config",
    # Prompts
    "PREFERENCE_SYSTEM_PROMPT",
    "ANALYZE_PREFERENCES_PROMPT",
    "RECOMMEND_PREFERENCES_PROMPT",
    "LEARN_FROM_ENGAGEMENT_PROMPT",
    "format_preferences_for_prompt",
    "format_engagement_history",
]
