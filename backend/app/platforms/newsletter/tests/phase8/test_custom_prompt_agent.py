"""
Tests for Custom Prompt Agent.

Tests NLP analysis and parameter extraction functionality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.platforms.newsletter.agents.custom_prompt.agent import CustomPromptAgent
from app.platforms.newsletter.agents.custom_prompt.schemas import (
    PromptAnalysis,
    ExtractedParameters,
    ValidationResult,
    EnhancedPrompt,
)


@pytest.fixture
def mock_llm():
    """Create a mock LLM provider."""
    llm = MagicMock()
    llm.generate = AsyncMock()
    return llm


@pytest.fixture
def agent(mock_llm):
    """Create CustomPromptAgent with mocked LLM."""
    with patch(
        "app.platforms.newsletter.agents.custom_prompt.agent.get_custom_prompt_llm"
    ) as mock_get_llm:
        mock_get_llm.return_value = mock_llm
        return CustomPromptAgent()


class TestCustomPromptAgentInit:
    """Test CustomPromptAgent initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes with correct attributes."""
        assert agent.name == "custom_prompt"
        assert "natural language" in agent.description.lower() or "parameters" in agent.description.lower()

    def test_agent_has_llm(self, agent):
        """Test agent has LLM provider."""
        assert agent.llm is not None


class TestAnalyzePrompt:
    """Test prompt analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_prompt_basic(self, agent, mock_llm):
        """Test basic prompt analysis."""
        mock_llm.generate.return_value = """{
            "intent": "research",
            "topics": ["AI", "healthcare"],
            "tone": "professional",
            "constraints": {},
            "focus_areas": ["medical applications"],
            "exclusions": [],
            "time_range": null,
            "confidence": 0.9
        }"""

        result = await agent.analyze_prompt("Find articles about AI in healthcare")

        assert isinstance(result, PromptAnalysis)
        assert result.intent == "research"
        assert "AI" in result.topics
        assert result.confidence >= 0.5

    @pytest.mark.asyncio
    async def test_analyze_prompt_with_quotes(self, agent, mock_llm):
        """Test analysis extracts quoted topics."""
        mock_llm.generate.return_value = """{
            "intent": "research",
            "topics": ["machine learning"],
            "tone": null,
            "constraints": {},
            "focus_areas": [],
            "exclusions": [],
            "time_range": null,
            "confidence": 0.85
        }"""

        result = await agent.analyze_prompt('Find articles about "machine learning"')

        assert isinstance(result, PromptAnalysis)
        assert "machine learning" in result.topics

    @pytest.mark.asyncio
    async def test_analyze_prompt_detects_intent(self, agent, mock_llm):
        """Test intent detection from keywords."""
        mock_llm.generate.return_value = """{
            "intent": "summarize",
            "topics": ["report"],
            "tone": null,
            "constraints": {},
            "focus_areas": [],
            "exclusions": [],
            "time_range": null,
            "confidence": 0.8
        }"""

        result = await agent.analyze_prompt("Summarize the latest tech report")

        assert result.intent == "summarize"

    @pytest.mark.asyncio
    async def test_analyze_prompt_llm_failure_fallback(self, agent, mock_llm):
        """Test fallback when LLM fails."""
        mock_llm.generate.side_effect = Exception("LLM error")

        result = await agent.analyze_prompt("Find articles about AI")

        # Should still return a result with lower confidence
        assert isinstance(result, PromptAnalysis)
        assert result.confidence <= 0.5  # Low confidence for fallback

    @pytest.mark.asyncio
    async def test_analyze_prompt_detects_tone(self, agent, mock_llm):
        """Test tone detection."""
        mock_llm.generate.return_value = """{
            "intent": "generate",
            "topics": ["news"],
            "tone": "casual",
            "constraints": {},
            "focus_areas": [],
            "exclusions": [],
            "time_range": null,
            "confidence": 0.85
        }"""

        result = await agent.analyze_prompt("Write casual news summary")

        assert result.tone == "casual"


class TestEnhancePrompt:
    """Test prompt enhancement functionality."""

    @pytest.mark.asyncio
    async def test_enhance_prompt_basic(self, agent, mock_llm):
        """Test basic prompt enhancement."""
        mock_llm.generate.return_value = """{
            "enhanced_prompt": "Find professional articles about AI focusing on enterprise applications",
            "added_context": ["professional tone from preferences", "enterprise focus"],
            "suggestions": []
        }"""

        preferences = {"tone": "professional", "topics": ["enterprise"]}
        result = await agent.enhance_prompt("Find AI articles", preferences)

        assert isinstance(result, EnhancedPrompt)
        assert result.enhanced_prompt != result.original_prompt
        assert result.user_preferences_applied is True

    @pytest.mark.asyncio
    async def test_enhance_prompt_with_successful_topics(self, agent, mock_llm):
        """Test enhancement with successful topics."""
        mock_llm.generate.return_value = """{
            "enhanced_prompt": "Find AI and blockchain articles",
            "added_context": ["blockchain from past success"],
            "suggestions": []
        }"""

        result = await agent.enhance_prompt(
            "Find AI articles",
            {},
            successful_topics=["blockchain", "fintech"]
        )

        assert isinstance(result, EnhancedPrompt)
        assert len(result.added_context) >= 0

    @pytest.mark.asyncio
    async def test_enhance_prompt_llm_failure(self, agent, mock_llm):
        """Test enhancement fallback on LLM failure."""
        mock_llm.generate.side_effect = Exception("LLM error")

        result = await agent.enhance_prompt("Find AI articles", {})

        # Should return original prompt
        assert result.enhanced_prompt == result.original_prompt
        assert result.user_preferences_applied is False


class TestGenerateParameters:
    """Test parameter generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_parameters_from_analysis(self, agent, mock_llm):
        """Test parameter generation from analysis."""
        mock_llm.generate.return_value = """{
            "topics": ["artificial intelligence", "machine learning"],
            "tone": "professional",
            "max_articles": 10,
            "max_word_count": null,
            "focus_areas": ["practical applications"],
            "time_range_days": 7,
            "include_summaries": true,
            "source_preferences": [],
            "exclusions": []
        }"""

        analysis = {
            "intent": "research",
            "topics": ["AI", "ML"],
            "tone": "professional",
        }

        result = await agent.generate_parameters(analysis, {})

        assert isinstance(result, ExtractedParameters)
        assert len(result.topics) > 0
        assert result.time_range_days == 7

    @pytest.mark.asyncio
    async def test_generate_parameters_with_preferences(self, agent, mock_llm):
        """Test parameter generation with user preferences."""
        mock_llm.generate.return_value = """{
            "topics": ["AI"],
            "tone": "casual",
            "max_articles": 15,
            "max_word_count": null,
            "focus_areas": [],
            "time_range_days": 14,
            "include_summaries": true,
            "source_preferences": [],
            "exclusions": []
        }"""

        analysis = PromptAnalysis(
            original_prompt="Find AI news",
            intent="research",
            topics=["AI"],
        )

        preferences = {"tone": "casual", "max_articles": 15}

        result = await agent.generate_parameters(analysis, preferences)

        assert isinstance(result, ExtractedParameters)

    @pytest.mark.asyncio
    async def test_generate_parameters_to_research_params(self, agent, mock_llm):
        """Test conversion to research parameters."""
        mock_llm.generate.return_value = """{
            "topics": ["AI", "ML"],
            "tone": "professional",
            "max_articles": 10,
            "time_range_days": 7,
            "include_summaries": true
        }"""

        result = await agent.generate_parameters({"topics": ["AI"]}, {})

        research_params = result.to_research_params()
        assert "topics" in research_params
        assert "max_results" in research_params

    @pytest.mark.asyncio
    async def test_generate_parameters_to_writing_params(self, agent, mock_llm):
        """Test conversion to writing parameters."""
        mock_llm.generate.return_value = """{
            "topics": ["AI"],
            "tone": "casual",
            "max_articles": 10,
            "focus_areas": ["tutorials"]
        }"""

        result = await agent.generate_parameters({"topics": ["AI"]}, {})

        writing_params = result.to_writing_params()
        assert "tone" in writing_params
        assert "focus_areas" in writing_params


class TestValidateParameters:
    """Test parameter validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_parameters_valid(self, agent, mock_llm):
        """Test validation of valid parameters."""
        mock_llm.generate.return_value = """{
            "valid": true,
            "errors": [],
            "warnings": [],
            "suggestions": ["Consider adding focus areas"]
        }"""

        params = {
            "topics": ["AI", "ML"],
            "tone": "professional",
            "max_articles": 10,
            "time_range_days": 7,
        }

        result = await agent.validate_parameters(params)

        assert isinstance(result, ValidationResult)
        assert result.valid is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_validate_parameters_no_topics(self, agent, mock_llm):
        """Test validation catches missing topics."""
        params = {
            "topics": [],
            "tone": "professional",
        }

        result = await agent.validate_parameters(params)

        assert result.valid is False
        assert any("topics" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_parameters_invalid_range(self, agent, mock_llm):
        """Test validation catches invalid ranges."""
        params = {
            "topics": ["AI"],
            "max_articles": 0,  # Invalid: must be >= 1
        }

        result = await agent.validate_parameters(params)

        assert result.valid is False
        assert any("max_articles" in e.lower() for e in result.errors)

    @pytest.mark.asyncio
    async def test_validate_parameters_high_values_warning(self, agent, mock_llm):
        """Test validation warns on high values."""
        mock_llm.generate.return_value = """{
            "valid": true,
            "errors": [],
            "warnings": ["Consider reducing max_articles"],
            "suggestions": []
        }"""

        params = {
            "topics": ["AI"],
            "max_articles": 50,  # Very high
            "time_range_days": 7,
        }

        result = await agent.validate_parameters(params)

        # Should have warning about high value
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_parameters_with_schema(self, agent, mock_llm):
        """Test validation with ExtractedParameters schema."""
        mock_llm.generate.return_value = """{
            "valid": true,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }"""

        params = ExtractedParameters(
            topics=["AI"],
            tone="professional",
            max_articles=10,
        )

        result = await agent.validate_parameters(params)

        assert isinstance(result, ValidationResult)
        assert result.valid is True


class TestRunMethod:
    """Test main run() method routing."""

    @pytest.mark.asyncio
    async def test_run_analyze_action(self, agent, mock_llm):
        """Test run with analyze action."""
        mock_llm.generate.return_value = """{
            "intent": "research",
            "topics": ["AI"],
            "tone": null,
            "constraints": {},
            "focus_areas": [],
            "exclusions": [],
            "time_range": null,
            "confidence": 0.9
        }"""

        result = await agent.run({
            "action": "analyze",
            "prompt": "Find AI articles",
        })

        assert result["success"] is True
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_run_enhance_action(self, agent, mock_llm):
        """Test run with enhance action."""
        mock_llm.generate.return_value = """{
            "enhanced_prompt": "Enhanced prompt",
            "added_context": [],
            "suggestions": []
        }"""

        result = await agent.run({
            "action": "enhance",
            "prompt": "Find AI articles",
            "preferences": {"tone": "casual"},
        })

        assert result["success"] is True
        assert "enhanced" in result

    @pytest.mark.asyncio
    async def test_run_generate_action(self, agent, mock_llm):
        """Test run with generate action."""
        mock_llm.generate.return_value = """{
            "topics": ["AI"],
            "tone": "professional",
            "max_articles": 10,
            "time_range_days": 7
        }"""

        result = await agent.run({
            "action": "generate",
            "prompt": "Find AI articles",
            "analysis": {"topics": ["AI"], "intent": "research"},
        })

        assert result["success"] is True
        assert "parameters" in result

    @pytest.mark.asyncio
    async def test_run_validate_action(self, agent, mock_llm):
        """Test run with validate action."""
        mock_llm.generate.return_value = """{
            "valid": true,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }"""

        result = await agent.run({
            "action": "validate",
            "parameters": {"topics": ["AI"], "max_articles": 10},
        })

        assert result["success"] is True
        assert "validation" in result

    @pytest.mark.asyncio
    async def test_run_missing_prompt(self, agent):
        """Test run fails without prompt for analyze/enhance."""
        result = await agent.run({"action": "analyze"})

        assert result["success"] is False
        assert "prompt" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_unknown_action(self, agent):
        """Test run fails for unknown action."""
        result = await agent.run({
            "action": "unknown",
            "prompt": "Test",
        })

        assert result["success"] is False
        assert "unknown" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_default_action_is_analyze(self, agent, mock_llm):
        """Test default action is analyze."""
        mock_llm.generate.return_value = """{
            "intent": "research",
            "topics": [],
            "tone": null,
            "constraints": {},
            "focus_areas": [],
            "exclusions": [],
            "time_range": null,
            "confidence": 0.5
        }"""

        result = await agent.run({"prompt": "Test"})

        assert result["success"] is True
        assert "analysis" in result


class TestJsonParsing:
    """Test JSON response parsing."""

    @pytest.mark.asyncio
    async def test_parse_json_with_markdown(self, agent, mock_llm):
        """Test parsing JSON in markdown code blocks."""
        mock_llm.generate.return_value = """```json
{
    "intent": "research",
    "topics": ["AI"],
    "tone": null,
    "constraints": {},
    "focus_areas": [],
    "exclusions": [],
    "time_range": null,
    "confidence": 0.9
}
```"""

        result = await agent.analyze_prompt("Find AI articles")

        assert result.intent == "research"

    @pytest.mark.asyncio
    async def test_parse_json_without_markdown(self, agent, mock_llm):
        """Test parsing plain JSON."""
        mock_llm.generate.return_value = '{"intent": "research", "topics": ["AI"], "tone": null, "constraints": {}, "focus_areas": [], "exclusions": [], "time_range": null, "confidence": 0.8}'

        result = await agent.analyze_prompt("Find AI articles")

        assert result.intent == "research"

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, agent, mock_llm):
        """Test handling of invalid JSON."""
        mock_llm.generate.return_value = "This is not valid JSON"

        # Should fall back to keyword detection
        result = await agent.analyze_prompt("Find AI articles")

        assert isinstance(result, PromptAnalysis)
        # Should have lower confidence due to parsing failure
        assert result.confidence < 1.0
