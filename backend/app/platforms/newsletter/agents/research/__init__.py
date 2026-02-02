"""
Research Agent for Newsletter Platform.

Content discovery with three-stage pipeline:
1. Search (Tavily API - no LLM)
2. Filter/Score (rules + optional LLM)
3. Summarize (LLM)
"""
from app.platforms.newsletter.agents.research.agent import ResearchAgent
from app.platforms.newsletter.agents.research.llm import (
    get_research_llm,
    get_research_config,
    get_summarization_config,
    get_analysis_config,
)
from app.platforms.newsletter.agents.research.prompts import (
    RESEARCH_SYSTEM_PROMPT,
    SUMMARIZE_ARTICLE_PROMPT,
    BATCH_SUMMARIZE_PROMPT,
    SCORE_RELEVANCE_PROMPT,
    ENHANCE_QUERY_PROMPT,
)

__all__ = [
    "ResearchAgent",
    "get_research_llm",
    "get_research_config",
    "get_summarization_config",
    "get_analysis_config",
    "RESEARCH_SYSTEM_PROMPT",
    "SUMMARIZE_ARTICLE_PROMPT",
    "BATCH_SUMMARIZE_PROMPT",
    "SCORE_RELEVANCE_PROMPT",
    "ENHANCE_QUERY_PROMPT",
]
