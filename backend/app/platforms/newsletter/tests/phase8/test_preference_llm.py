"""
Tests for Preference Agent LLM configuration.

Tests factory functions and configuration loading.
"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetPreferenceLlm:
    """Tests for get_preference_llm() factory function."""

    def test_get_preference_llm_initializes(self):
        """Ensure LLM provider can be initialized without errors."""
        with patch("app.platforms.newsletter.agents.preference.llm.get_llm_provider") as mock_provider:
            mock_provider.return_value = MagicMock()

            from app.platforms.newsletter.agents.preference.llm import get_preference_llm

            llm = get_preference_llm()

            mock_provider.assert_called_once()
            call_kwargs = mock_provider.call_args.kwargs
            assert "default_model" in call_kwargs
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] == 120.0  # 2 minute timeout

    def test_get_preference_llm_uses_platform_config(self):
        """Verify LLM uses platform-specific configuration."""
        with patch("app.platforms.newsletter.agents.preference.llm.get_llm_provider") as mock_provider, \
             patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:

            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"
            mock_provider.return_value = MagicMock()

            from app.platforms.newsletter.agents.preference.llm import get_preference_llm

            get_preference_llm()

            call_kwargs = mock_provider.call_args.kwargs
            assert call_kwargs["default_model"] == "llama3"

    def test_get_preference_llm_handles_different_providers(self):
        """Test that different provider types are handled correctly."""
        providers_to_test = ["ollama", "openai", "gemini", "aws_bedrock"]

        for provider_name in providers_to_test:
            with patch("app.platforms.newsletter.agents.preference.llm.get_llm_provider") as mock_provider, \
                 patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:

                mock_config.effective_provider = provider_name
                mock_config.effective_model = "test-model"
                mock_provider.return_value = MagicMock()

                from app.platforms.newsletter.agents.preference.llm import get_preference_llm

                llm = get_preference_llm()

                assert mock_provider.called
                call_kwargs = mock_provider.call_args.kwargs
                assert "provider_type" in call_kwargs


class TestGetPreferenceConfig:
    """Tests for get_preference_config() function."""

    def test_get_preference_config_returns_dict(self):
        """Ensure config returns a dictionary with expected keys."""
        with patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"

            from app.platforms.newsletter.agents.preference.llm import get_preference_config

            config = get_preference_config()

            assert isinstance(config, dict)
            assert "provider" in config
            assert "model" in config
            assert "temperature" in config
            assert "max_tokens" in config

    def test_get_preference_config_has_low_temperature(self):
        """Preference config should have lower temperature for consistency."""
        with patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"

            from app.platforms.newsletter.agents.preference.llm import get_preference_config

            config = get_preference_config()

            assert config["temperature"] == 0.3


class TestGetAnalysisConfig:
    """Tests for get_analysis_config() function."""

    def test_get_analysis_config_has_lower_temperature(self):
        """Analysis config should have very low temperature."""
        with patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"

            from app.platforms.newsletter.agents.preference.llm import get_analysis_config

            config = get_analysis_config()

            assert config["temperature"] == 0.2

    def test_get_analysis_config_has_higher_max_tokens(self):
        """Analysis config should have higher max_tokens for detailed analysis."""
        with patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"

            from app.platforms.newsletter.agents.preference.llm import get_analysis_config

            config = get_analysis_config()

            assert config["max_tokens"] == 1500


class TestGetRecommendationConfig:
    """Tests for get_recommendation_config() function."""

    def test_get_recommendation_config_has_higher_temperature(self):
        """Recommendation config should have higher temperature for creativity."""
        with patch("app.platforms.newsletter.agents.preference.llm.config") as mock_config:
            mock_config.effective_provider = "ollama"
            mock_config.effective_model = "llama3"

            from app.platforms.newsletter.agents.preference.llm import get_recommendation_config

            config = get_recommendation_config()

            assert config["temperature"] == 0.5
