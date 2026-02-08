"""
LLM configuration for Preference Agent.

Provides factory functions for LLM provider and configuration.
"""
from typing import Dict, Any

from app.common.providers.llm import get_llm_provider, LLMProviderType
from app.platforms.newsletter.config import config


# Provider type mapping
PROVIDER_MAP = {
    "ollama": LLMProviderType.OLLAMA,
    "openai": LLMProviderType.OPENAI,
    "gemini": LLMProviderType.GEMINI,
    "aws_bedrock": LLMProviderType.AWS_BEDROCK,
}


def get_preference_llm():
    """
    Get LLM provider for Preference Agent.

    Uses platform config with 2-minute timeout for analysis operations.
    """
    provider_name = config.effective_provider.lower()
    provider_type = PROVIDER_MAP.get(provider_name, LLMProviderType.GEMINI)

    return get_llm_provider(
        provider_type=provider_type,
        default_model=config.effective_model,
        timeout=120.0,  # 2 minute timeout for preference analysis
    )


def get_preference_config() -> Dict[str, Any]:
    """
    Get base configuration for Preference Agent.

    Returns configuration dict with provider settings.
    """
    return {
        "provider": config.effective_provider,
        "model": config.effective_model,
        "temperature": 0.3,  # Lower temperature for consistent analysis
        "max_tokens": 1000,
    }


def get_analysis_config() -> Dict[str, Any]:
    """
    Get configuration for preference analysis.

    Uses lower temperature for consistent, analytical outputs.
    """
    base = get_preference_config()
    base["temperature"] = 0.2
    base["max_tokens"] = 1500
    return base


def get_recommendation_config() -> Dict[str, Any]:
    """
    Get configuration for preference recommendations.

    Uses slightly higher temperature for creative suggestions.
    """
    base = get_preference_config()
    base["temperature"] = 0.5
    base["max_tokens"] = 1000
    return base


__all__ = [
    "get_preference_llm",
    "get_preference_config",
    "get_analysis_config",
    "get_recommendation_config",
]
