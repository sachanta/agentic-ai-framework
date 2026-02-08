"""
LLM configuration for the Writing Agent.

Uses platform-specific config with fallback to global settings.
Optimized for content generation with higher token limits.
"""
import logging
from typing import Any, Dict

from app.common.providers.llm import get_llm_provider, LLMProviderType
from app.platforms.newsletter.config import config

logger = logging.getLogger(__name__)


def get_writing_llm():
    """
    Get the LLM provider for the Writing Agent.

    Uses newsletter platform config with fallback to global settings.
    Uses longer timeout for content generation.

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
        "bedrock": LLMProviderType.AWS_BEDROCK,
    }.get(provider_name, LLMProviderType.GEMINI)

    return get_llm_provider(
        provider_type=provider_type,
        default_model=config.effective_model,
        timeout=300.0,  # 5 minutes for content generation
    )


def get_writing_config() -> Dict[str, Any]:
    """
    Get the LLM configuration for the Writing Agent.

    Returns:
        Dict with model, temperature, max_tokens
    """
    return {
        "provider": config.effective_provider,
        "model": config.effective_model,
        "temperature": config.effective_temperature,
        "max_tokens": 2000,  # Higher for newsletter content
    }


def get_creative_config() -> Dict[str, Any]:
    """
    Get config for creative tasks like subject lines.

    Higher temperature for more creative/varied outputs.

    Returns:
        Dict with model config optimized for creativity
    """
    base_config = get_writing_config()
    return {
        **base_config,
        "temperature": 0.8,  # More creative
        "max_tokens": 500,
    }


def get_formatting_config() -> Dict[str, Any]:
    """
    Get config for formatting tasks.

    Lower temperature for consistent formatting.

    Returns:
        Dict with model config optimized for formatting
    """
    base_config = get_writing_config()
    return {
        **base_config,
        "temperature": 0.3,  # More deterministic
        "max_tokens": 1500,
    }
