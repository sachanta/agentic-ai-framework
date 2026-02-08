"""
LLM configuration for Custom Prompt Agent.

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


def get_custom_prompt_llm():
    """
    Get LLM provider for Custom Prompt Agent.

    Uses platform config with 1-minute timeout for NLP operations.
    """
    provider_name = config.effective_provider.lower()
    provider_type = PROVIDER_MAP.get(provider_name, LLMProviderType.GEMINI)

    return get_llm_provider(
        provider_type=provider_type,
        default_model=config.effective_model,
        timeout=60.0,  # 1 minute timeout for NLP parsing
    )


def get_custom_prompt_config() -> Dict[str, Any]:
    """
    Get base configuration for Custom Prompt Agent.

    Returns configuration dict with provider settings.
    """
    return {
        "provider": config.effective_provider,
        "model": config.effective_model,
        "temperature": 0.2,  # Low temperature for consistent parsing
        "max_tokens": 800,
    }


def get_analysis_config() -> Dict[str, Any]:
    """
    Get configuration for prompt analysis.

    Uses very low temperature for accurate extraction.
    """
    base = get_custom_prompt_config()
    base["temperature"] = 0.1
    base["max_tokens"] = 1000
    return base


def get_enhancement_config() -> Dict[str, Any]:
    """
    Get configuration for prompt enhancement.

    Uses slightly higher temperature for creative enhancement.
    """
    base = get_custom_prompt_config()
    base["temperature"] = 0.4
    base["max_tokens"] = 500
    return base


__all__ = [
    "get_custom_prompt_llm",
    "get_custom_prompt_config",
    "get_analysis_config",
    "get_enhancement_config",
]
