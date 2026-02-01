"""
Greeter LLM configuration.

Uses the platform config which falls back to global settings.
This allows switching LLM providers via environment variables.
"""
from typing import Optional

from app.common.providers.llm import LLMProvider, LLMConfig, get_llm_provider
from app.platforms.hello_world.config import config


def get_greeter_llm() -> LLMProvider:
    """
    Get the LLM provider configured for the greeter agent.

    Configuration hierarchy:
    1. Platform-specific env vars (HELLO_WORLD_LLM_PROVIDER, etc.)
    2. Global env vars (LLM_PROVIDER, LLM_DEFAULT_MODEL, etc.)
    3. Default values (ollama, llama3)

    Returns:
        Configured LLM provider instance
    """
    # Create config from platform settings (which fall back to global)
    llm_config = LLMConfig(
        provider=config.effective_provider,
        model=config.effective_model,
        temperature=config.effective_temperature,
        max_tokens=config.effective_max_tokens,
    )

    return get_llm_provider(config=llm_config)


def get_greeter_config() -> dict:
    """
    Get the current LLM configuration for debugging/status.

    Returns:
        Dictionary with current LLM settings
    """
    return {
        "provider": config.effective_provider,
        "model": config.effective_model,
        "temperature": config.effective_temperature,
        "max_tokens": config.effective_max_tokens,
    }
