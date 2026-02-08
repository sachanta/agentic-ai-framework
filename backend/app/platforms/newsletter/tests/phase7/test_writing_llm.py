"""
Tests for Writing Agent LLM configuration.

Tests factory functions and configuration loading.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetWritingLlm:
    """Tests for get_writing_llm() factory function."""

    def test_get_writing_llm_initializes(self):
        """Ensure LLM provider can be initialized without errors."""
        with patch("app.platforms.newsletter.agents.writing.llm.get_llm_provider") as mock_provider:
            mock_provider.return_value = MagicMock()

            from app.platforms.newsletter.agents.writing.llm import get_writing_llm

            llm = get_writing_llm()

            mock_provider.assert_called_once()
            call_kwargs = mock_provider.call_args.kwargs
            assert "default_model" in call_kwargs
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] == 300.0  # 5 minute timeout

    def test_get_writing_llm_uses_platform_config(self):
        """Verify LLM uses platform-specific configuration."""
        with patch("app.platforms.newsletter.agents.writing.llm.get_llm_provider") as mock_provider, \
             patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:

            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"
            mock_provider.return_value = MagicMock()

            from app.platforms.newsletter.agents.writing.llm import get_writing_llm

            get_writing_llm()

            call_kwargs = mock_provider.call_args.kwargs
            assert call_kwargs["default_model"] == "llama3"

    def test_get_writing_llm_handles_different_providers(self):
        """Test that different provider types are handled correctly."""
        providers_to_test = ["ollama", "openai", "gemini", "aws_bedrock"]

        for provider_name in providers_to_test:
            with patch("app.platforms.newsletter.agents.writing.llm.get_llm_provider") as mock_provider, \
                 patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:

                mock_config.effective_provider = provider_name
                mock_config.effective_model = "test-model"
                mock_provider.return_value = MagicMock()

                from app.platforms.newsletter.agents.writing.llm import get_writing_llm

                llm = get_writing_llm()

                assert mock_provider.called
                call_kwargs = mock_provider.call_args.kwargs
                assert "provider_type" in call_kwargs


class TestGetWritingConfig:
    """Tests for get_writing_config() function."""

    def test_get_writing_config_returns_dict(self):
        """Ensure config returns a dictionary with expected keys."""
        with patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"
            mock_config.effective_temperature = 0.7
            mock_config.effective_max_tokens = 1000

            from app.platforms.newsletter.agents.writing.llm import get_writing_config

            config = get_writing_config()

            assert isinstance(config, dict)
            assert "provider" in config
            assert "model" in config
            assert "temperature" in config
            assert "max_tokens" in config

    def test_get_writing_config_has_higher_max_tokens(self):
        """Writing config should have higher max_tokens for content generation."""
        with patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"
            mock_config.effective_temperature = 0.7
            mock_config.effective_max_tokens = 1000

            from app.platforms.newsletter.agents.writing.llm import get_writing_config

            config = get_writing_config()

            # Writing should have higher tokens than default
            assert config["max_tokens"] == 2000


class TestGetCreativeConfig:
    """Tests for get_creative_config() function."""

    def test_get_creative_config_has_higher_temperature(self):
        """Creative config should have higher temperature for variety."""
        with patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"
            mock_config.effective_temperature = 0.7
            mock_config.effective_max_tokens = 1000

            from app.platforms.newsletter.agents.writing.llm import get_creative_config

            config = get_creative_config()

            assert config["temperature"] == 0.8  # Higher for creativity

    def test_get_creative_config_inherits_base(self):
        """Creative config should inherit from base config."""
        with patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:
            mock_config.effective_provider = "openai"
            mock_config.effective_model = "gpt-4"
            mock_config.effective_temperature = 0.7
            mock_config.effective_max_tokens = 1000

            from app.platforms.newsletter.agents.writing.llm import get_creative_config

            config = get_creative_config()

            assert config["provider"] == "openai"
            assert config["model"] == "gpt-4"


class TestGetFormattingConfig:
    """Tests for get_formatting_config() function."""

    def test_get_formatting_config_has_lower_temperature(self):
        """Formatting config should have lower temperature for consistency."""
        with patch("app.platforms.newsletter.agents.writing.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"
            mock_config.effective_temperature = 0.7
            mock_config.effective_max_tokens = 1000

            from app.platforms.newsletter.agents.writing.llm import get_formatting_config

            config = get_formatting_config()

            assert config["temperature"] == 0.3  # Lower for consistency
