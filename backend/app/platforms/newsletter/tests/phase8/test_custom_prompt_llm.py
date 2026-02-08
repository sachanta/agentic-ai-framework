"""
Tests for Custom Prompt Agent LLM configuration.

Tests LLM provider factory and configuration functions.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.platforms.newsletter.agents.custom_prompt.llm import (
    get_custom_prompt_llm,
    get_custom_prompt_config,
    get_analysis_config,
    get_enhancement_config,
    PROVIDER_MAP,
)
from app.common.providers.llm import LLMProviderType


class TestProviderMap:
    """Test provider type mapping."""

    def test_provider_map_has_expected_providers(self):
        """Test provider map includes expected providers."""
        assert "ollama" in PROVIDER_MAP
        assert "openai" in PROVIDER_MAP
        assert "gemini" in PROVIDER_MAP
        assert "aws_bedrock" in PROVIDER_MAP

    def test_provider_map_uses_correct_enum_values(self):
        """Test provider map uses correct LLMProviderType values."""
        assert PROVIDER_MAP["ollama"] == LLMProviderType.OLLAMA
        assert PROVIDER_MAP["openai"] == LLMProviderType.OPENAI
        assert PROVIDER_MAP["gemini"] == LLMProviderType.GEMINI
        assert PROVIDER_MAP["aws_bedrock"] == LLMProviderType.AWS_BEDROCK


class TestGetCustomPromptLLM:
    """Test LLM provider factory function."""

    def test_get_custom_prompt_llm_returns_provider(self):
        """Test factory returns an LLM provider."""
        with patch(
            "app.platforms.newsletter.agents.custom_prompt.llm.get_llm_provider"
        ) as mock_get_llm:
            mock_provider = MagicMock()
            mock_get_llm.return_value = mock_provider

            result = get_custom_prompt_llm()

            assert result == mock_provider
            mock_get_llm.assert_called_once()

    def test_get_custom_prompt_llm_uses_correct_timeout(self):
        """Test factory uses 1-minute timeout for NLP operations."""
        with patch(
            "app.platforms.newsletter.agents.custom_prompt.llm.get_llm_provider"
        ) as mock_get_llm:
            mock_get_llm.return_value = MagicMock()

            get_custom_prompt_llm()

            call_kwargs = mock_get_llm.call_args.kwargs
            assert call_kwargs["timeout"] == 60.0  # 1 minute

    def test_get_custom_prompt_llm_uses_default_model(self):
        """Test factory uses default_model parameter."""
        with patch(
            "app.platforms.newsletter.agents.custom_prompt.llm.get_llm_provider"
        ) as mock_get_llm:
            mock_get_llm.return_value = MagicMock()

            get_custom_prompt_llm()

            call_kwargs = mock_get_llm.call_args.kwargs
            assert "default_model" in call_kwargs


class TestConfigFunctions:
    """Test configuration functions."""

    def test_get_custom_prompt_config_returns_dict(self):
        """Test base config returns a dictionary."""
        config = get_custom_prompt_config()

        assert isinstance(config, dict)
        assert "provider" in config
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_custom_prompt_config_low_temperature(self):
        """Test base config has low temperature for consistent parsing."""
        config = get_custom_prompt_config()

        assert config["temperature"] <= 0.3

    def test_get_analysis_config_returns_dict(self):
        """Test analysis config returns a dictionary."""
        config = get_analysis_config()

        assert isinstance(config, dict)
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_analysis_config_very_low_temperature(self):
        """Test analysis config has very low temperature."""
        config = get_analysis_config()

        # Analysis needs very low temperature for accurate extraction
        assert config["temperature"] <= 0.2

    def test_get_analysis_config_sufficient_tokens(self):
        """Test analysis config has sufficient tokens."""
        config = get_analysis_config()

        assert config["max_tokens"] >= 800

    def test_get_enhancement_config_returns_dict(self):
        """Test enhancement config returns a dictionary."""
        config = get_enhancement_config()

        assert isinstance(config, dict)
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_enhancement_config_higher_temperature(self):
        """Test enhancement config has higher temperature for creativity."""
        base = get_custom_prompt_config()
        enhancement = get_enhancement_config()

        # Enhancement should allow more creativity
        assert enhancement["temperature"] > base["temperature"]
