"""
LLM configuration for the Research Agent.

Uses platform-specific config with fallback to global settings.
"""
import logging
from typing import Any, Dict, Optional

from app.common.providers.llm import get_llm_provider, LLMProviderType
from app.platforms.newsletter.config import config

logger = logging.getLogger(__name__)


def get_research_llm():
    """
    Get the LLM provider for the Research Agent.

    Uses newsletter platform config with fallback to global settings.
    Uses a longer timeout (5 minutes) for batch operations like summarization.

    Returns:
        LLMProvider instance
    """
    provider_name = config.effective_provider.lower()

    provider_type = {
        "gemini": LLMProviderType.GEMINI,
        "perplexity": LLMProviderType.PERPLEXITY,
        "ollama": LLMProviderType.OLLAMA,
        "openai": LLMProviderType.OPENAI,
        "aws_bedrock": LLMProviderType.AWS_BEDROCK,
        "bedrock": LLMProviderType.AWS_BEDROCK,  # Alias
    }.get(provider_name, LLMProviderType.GEMINI)

    # Use longer timeout for batch summarization with local LLMs
    return get_llm_provider(
        provider_type=provider_type,
        default_model=config.effective_model,
        timeout=300.0,  # 5 minutes for batch operations
    )


def get_research_config() -> Dict[str, Any]:
    """
    Get the LLM configuration for the Research Agent.

    Returns:
        Dict with model, temperature, max_tokens
    """
    return {
        "provider": config.effective_provider,
        "model": config.effective_model,
        "temperature": config.effective_temperature,
        "max_tokens": config.effective_max_tokens,
    }


def get_summarization_config() -> Dict[str, Any]:
    """
    Get config specifically for summarization tasks.

    Summarization benefits from slightly lower temperature for consistency.

    Returns:
        Dict with model config optimized for summarization
    """
    base_config = get_research_config()
    return {
        **base_config,
        "temperature": min(base_config.get("temperature", 0.7), 0.5),
        "max_tokens": 500,  # Summaries should be concise
    }


def get_analysis_config() -> Dict[str, Any]:
    """
    Get config specifically for analysis/scoring tasks.

    Analysis benefits from lower temperature for consistent scoring.

    Returns:
        Dict with model config optimized for analysis
    """
    base_config = get_research_config()
    return {
        **base_config,
        "temperature": 0.3,  # More deterministic for scoring
        "max_tokens": 200,  # Short analysis outputs
    }
