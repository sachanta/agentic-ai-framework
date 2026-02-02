"""
Newsletter Platform configuration tests.

Tests for Phase 1 configuration fields only.
Marked as @stable - these tests should pass across all phases.
"""
import pytest
import os
from unittest.mock import patch


@pytest.mark.stable
class TestNewsletterConfigDefaults:
    """Test default configuration values."""

    def test_platform_enabled_by_default(self, newsletter_config):
        """Test that platform is enabled by default."""
        assert newsletter_config.ENABLED is True

    def test_llm_settings_none_by_default(self, newsletter_config):
        """Test that LLM overrides are None by default (use global)."""
        assert newsletter_config.LLM_PROVIDER is None
        assert newsletter_config.LLM_MODEL is None
        assert newsletter_config.LLM_TEMPERATURE is None
        assert newsletter_config.LLM_MAX_TOKENS is None

    def test_search_settings_defaults(self, newsletter_config):
        """Test default search settings."""
        assert newsletter_config.SEARCH_DEPTH == "advanced"
        assert newsletter_config.MAX_RESULTS_PER_TOPIC == 10
        assert newsletter_config.RECENCY_DAYS == 3

    def test_content_settings_defaults(self, newsletter_config):
        """Test default content settings."""
        assert newsletter_config.MAX_ARTICLES == 10
        assert newsletter_config.DEFAULT_TONE == "professional"
        assert newsletter_config.DEFAULT_FREQUENCY == "weekly"
        assert newsletter_config.MAX_WORD_COUNT == 2000
        assert newsletter_config.MIN_WORD_COUNT == 500

    def test_email_settings_defaults(self, newsletter_config):
        """Test default email settings."""
        assert newsletter_config.FROM_EMAIL == "newsletter@example.com"
        assert newsletter_config.FROM_NAME == "AI Newsletter"

    def test_rag_settings_defaults(self, newsletter_config):
        """Test default RAG settings."""
        assert newsletter_config.WEAVIATE_COLLECTION == "NewsletterRAG"
        assert newsletter_config.CHUNK_SIZE == 1000
        assert newsletter_config.CHUNK_OVERLAP == 200

    def test_cache_settings_defaults(self, newsletter_config):
        """Test default cache settings."""
        assert newsletter_config.CACHE_TTL_SECONDS == 3600

    def test_api_keys_none_by_default(self, newsletter_config):
        """Test that API keys are not set by default."""
        assert newsletter_config.TAVILY_API_KEY is None
        assert newsletter_config.RESEND_API_KEY is None


@pytest.mark.stable
class TestNewsletterConfigEnvPrefix:
    """Test environment variable prefix handling."""

    def test_env_prefix_is_newsletter(self):
        """Test that config uses NEWSLETTER_ prefix."""
        from app.platforms.newsletter.config import NewsletterConfig
        # model_config can be a dict or ConfigDict
        config_dict = NewsletterConfig.model_config
        assert config_dict.get("env_prefix") == "NEWSLETTER_"

    def test_env_override_enabled(self):
        """Test overriding ENABLED via environment variable."""
        with patch.dict(os.environ, {"NEWSLETTER_ENABLED": "false"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.ENABLED is False

    def test_env_override_search_depth(self):
        """Test overriding SEARCH_DEPTH via environment variable."""
        with patch.dict(os.environ, {"NEWSLETTER_SEARCH_DEPTH": "basic"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.SEARCH_DEPTH == "basic"

    def test_env_override_max_articles(self):
        """Test overriding MAX_ARTICLES via environment variable."""
        with patch.dict(os.environ, {"NEWSLETTER_MAX_ARTICLES": "5"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.MAX_ARTICLES == 5


@pytest.mark.stable
class TestNewsletterConfigEffectiveProperties:
    """Test effective_* property methods."""

    def test_effective_provider_uses_global_when_not_set(self, mock_global_settings):
        """Test that effective_provider falls back to global settings."""
        from app.platforms.newsletter.config import NewsletterConfig
        config = NewsletterConfig()
        assert config.effective_provider == "openai"

    def test_effective_provider_uses_override_when_set(self, mock_global_settings):
        """Test that effective_provider uses platform override when set."""
        with patch.dict(os.environ, {"NEWSLETTER_LLM_PROVIDER": "ollama"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.effective_provider == "ollama"

    def test_effective_model_uses_global_when_not_set(self, mock_global_settings):
        """Test that effective_model falls back to global settings."""
        from app.platforms.newsletter.config import NewsletterConfig
        config = NewsletterConfig()
        assert config.effective_model == "gpt-4"

    def test_effective_model_uses_override_when_set(self, mock_global_settings):
        """Test that effective_model uses platform override when set."""
        with patch.dict(os.environ, {"NEWSLETTER_LLM_MODEL": "llama3"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.effective_model == "llama3"

    def test_effective_temperature_uses_global_when_not_set(self, mock_global_settings):
        """Test that effective_temperature falls back to global settings."""
        from app.platforms.newsletter.config import NewsletterConfig
        config = NewsletterConfig()
        assert config.effective_temperature == 0.7

    def test_effective_temperature_uses_override_when_set(self, mock_global_settings):
        """Test that effective_temperature uses platform override when set."""
        with patch.dict(os.environ, {"NEWSLETTER_LLM_TEMPERATURE": "0.5"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.effective_temperature == 0.5

    def test_effective_max_tokens_uses_global_when_not_set(self, mock_global_settings):
        """Test that effective_max_tokens falls back to global settings."""
        from app.platforms.newsletter.config import NewsletterConfig
        config = NewsletterConfig()
        assert config.effective_max_tokens == 4096

    def test_effective_max_tokens_uses_override_when_set(self, mock_global_settings):
        """Test that effective_max_tokens uses platform override when set."""
        with patch.dict(os.environ, {"NEWSLETTER_LLM_MAX_TOKENS": "2048"}):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.effective_max_tokens == 2048


@pytest.mark.stable
class TestNewsletterConfigDomainLists:
    """Test domain list parsing properties."""

    def test_include_domains_empty_by_default(self, newsletter_config):
        """Test that include_domains_list is empty by default."""
        assert newsletter_config.include_domains_list == []

    def test_exclude_domains_empty_by_default(self, newsletter_config):
        """Test that exclude_domains_list is empty by default."""
        assert newsletter_config.exclude_domains_list == []

    def test_include_domains_parses_comma_separated(self):
        """Test parsing comma-separated include domains."""
        with patch.dict(os.environ, {
            "NEWSLETTER_INCLUDE_DOMAINS": "techcrunch.com, reuters.com, bbc.com"
        }):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.include_domains_list == [
                "techcrunch.com",
                "reuters.com",
                "bbc.com",
            ]

    def test_exclude_domains_parses_comma_separated(self):
        """Test parsing comma-separated exclude domains."""
        with patch.dict(os.environ, {
            "NEWSLETTER_EXCLUDE_DOMAINS": "spam.com, ads.com"
        }):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.exclude_domains_list == ["spam.com", "ads.com"]

    def test_domain_list_handles_whitespace(self):
        """Test that domain list parsing handles extra whitespace."""
        with patch.dict(os.environ, {
            "NEWSLETTER_INCLUDE_DOMAINS": "  a.com  ,  b.com  ,  "
        }):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.include_domains_list == ["a.com", "b.com"]

    def test_domain_list_handles_empty_entries(self):
        """Test that domain list parsing skips empty entries."""
        with patch.dict(os.environ, {
            "NEWSLETTER_INCLUDE_DOMAINS": "a.com,,b.com,"
        }):
            from app.platforms.newsletter.config import NewsletterConfig
            config = NewsletterConfig()
            assert config.include_domains_list == ["a.com", "b.com"]
