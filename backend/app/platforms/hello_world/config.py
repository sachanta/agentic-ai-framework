"""
Hello World Platform configuration.

This platform can use the global LLM settings or override them.
Set environment variables with HELLO_WORLD_ prefix to override.
"""
from typing import Optional
from pydantic_settings import BaseSettings

from app.config import settings


class HelloWorldConfig(BaseSettings):
    """
    Configuration for the Hello World platform.

    LLM settings default to global config but can be overridden
    with HELLO_WORLD_ prefixed environment variables.
    """

    # LLM settings - None means use global settings
    LLM_PROVIDER: Optional[str] = None  # Override: HELLO_WORLD_LLM_PROVIDER
    LLM_MODEL: Optional[str] = None     # Override: HELLO_WORLD_LLM_MODEL
    LLM_TEMPERATURE: Optional[float] = None
    LLM_MAX_TOKENS: Optional[int] = None

    # Platform-specific settings
    GREETING_PREFIX: str = "Hello"
    MAX_GREETING_LENGTH: int = 500

    class Config:
        env_prefix = "HELLO_WORLD_"

    @property
    def effective_provider(self) -> str:
        """Get the effective LLM provider (platform override or global)."""
        return self.LLM_PROVIDER or settings.LLM_PROVIDER

    @property
    def effective_model(self) -> str:
        """Get the effective LLM model (platform override or global)."""
        return self.LLM_MODEL or settings.LLM_DEFAULT_MODEL

    @property
    def effective_temperature(self) -> float:
        """Get the effective temperature (platform override or global)."""
        return self.LLM_TEMPERATURE if self.LLM_TEMPERATURE is not None else settings.LLM_TEMPERATURE

    @property
    def effective_max_tokens(self) -> int:
        """Get the effective max tokens (platform override or global)."""
        return self.LLM_MAX_TOKENS if self.LLM_MAX_TOKENS is not None else settings.LLM_MAX_TOKENS


config = HelloWorldConfig()
