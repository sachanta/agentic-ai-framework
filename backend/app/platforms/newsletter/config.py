"""
Newsletter Platform configuration.

This platform can use the global LLM settings or override them.
Set environment variables with NEWSLETTER_ prefix to override.
"""
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import settings


class NewsletterConfig(BaseSettings):
    """
    Configuration for the Newsletter platform.

    LLM settings default to global config but can be overridden
    with NEWSLETTER_ prefixed environment variables.
    """

    # Platform enable/disable
    ENABLED: bool = True

    # LLM settings - None means use global settings
    LLM_PROVIDER: Optional[str] = None  # Override: NEWSLETTER_LLM_PROVIDER
    LLM_MODEL: Optional[str] = None     # Override: NEWSLETTER_LLM_MODEL
    LLM_TEMPERATURE: Optional[float] = None
    LLM_MAX_TOKENS: Optional[int] = None

    # External service API keys
    TAVILY_API_KEY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None

    # Email settings
    FROM_EMAIL: str = "newsletter@example.com"
    FROM_NAME: str = "AI Newsletter"

    # Search settings
    SEARCH_DEPTH: str = "advanced"  # basic or advanced
    MAX_RESULTS_PER_TOPIC: int = 10
    RECENCY_DAYS: int = 3
    INCLUDE_DOMAINS: Optional[str] = None  # Comma-separated list
    EXCLUDE_DOMAINS: Optional[str] = None  # Comma-separated list

    # Content settings
    MAX_ARTICLES: int = 10
    DEFAULT_TONE: str = "professional"  # professional, casual, formal, enthusiastic
    DEFAULT_FREQUENCY: str = "weekly"   # daily, weekly, monthly
    MAX_WORD_COUNT: int = 2000
    MIN_WORD_COUNT: int = 500

    # RAG settings
    WEAVIATE_COLLECTION: str = "NewsletterRAG"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Cache settings (using MongoDB with TTL indexes)
    CACHE_TTL_SECONDS: int = 3600  # Default TTL for cached items

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="NEWSLETTER_",
        case_sensitive=True,
        extra="ignore",
    )

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

    @property
    def include_domains_list(self) -> List[str]:
        """Parse include domains as a list."""
        if not self.INCLUDE_DOMAINS:
            return []
        return [d.strip() for d in self.INCLUDE_DOMAINS.split(",") if d.strip()]

    @property
    def exclude_domains_list(self) -> List[str]:
        """Parse exclude domains as a list."""
        if not self.EXCLUDE_DOMAINS:
            return []
        return [d.strip() for d in self.EXCLUDE_DOMAINS.split(",") if d.strip()]


config = NewsletterConfig()
