"""
Tests for Custom Prompt prompts module.

Tests prompt templates and helper functions.
"""
import pytest

from app.platforms.newsletter.agents.custom_prompt.prompts import (
    CUSTOM_PROMPT_SYSTEM_PROMPT,
    ANALYZE_PROMPT_PROMPT,
    GENERATE_PARAMETERS_PROMPT,
    ENHANCE_PROMPT_PROMPT,
    VALIDATE_PARAMETERS_PROMPT,
    INTENT_KEYWORDS,
    TONE_KEYWORDS,
    TIME_PATTERNS,
    detect_intent_keywords,
    detect_tone_keywords,
    detect_time_range,
    extract_quoted_topics,
)


class TestPromptTemplates:
    """Test prompt template definitions."""

    def test_system_prompt_exists(self):
        """Test system prompt is defined."""
        assert CUSTOM_PROMPT_SYSTEM_PROMPT
        assert len(CUSTOM_PROMPT_SYSTEM_PROMPT) > 50

    def test_analyze_prompt_template(self):
        """Test analyze prompt has placeholders."""
        assert "{prompt}" in ANALYZE_PROMPT_PROMPT
        assert "intent" in ANALYZE_PROMPT_PROMPT.lower()
        assert "topics" in ANALYZE_PROMPT_PROMPT.lower()

    def test_generate_parameters_template(self):
        """Test generate parameters prompt has placeholders."""
        assert "{analysis}" in GENERATE_PARAMETERS_PROMPT
        assert "{preferences}" in GENERATE_PARAMETERS_PROMPT

    def test_enhance_prompt_template(self):
        """Test enhance prompt has placeholders."""
        assert "{prompt}" in ENHANCE_PROMPT_PROMPT
        assert "{preferences}" in ENHANCE_PROMPT_PROMPT
        assert "{successful_topics}" in ENHANCE_PROMPT_PROMPT

    def test_validate_parameters_template(self):
        """Test validate parameters prompt has placeholders."""
        assert "{parameters}" in VALIDATE_PARAMETERS_PROMPT


class TestIntentKeywords:
    """Test intent keyword detection."""

    def test_intent_keywords_defined(self):
        """Test all intent categories have keywords."""
        expected_intents = ["research", "summarize", "analyze", "compare", "generate"]
        for intent in expected_intents:
            assert intent in INTENT_KEYWORDS
            assert len(INTENT_KEYWORDS[intent]) > 0

    def test_detect_research_intent(self):
        """Test detecting research intent."""
        prompts = [
            "Find articles about AI",
            "Search for news on technology",
            "Discover new trends",
            "Look for healthcare innovations",
            "Get information about ML",
        ]
        for prompt in prompts:
            assert detect_intent_keywords(prompt) == "research"

    def test_detect_summarize_intent(self):
        """Test detecting summarize intent."""
        prompts = [
            "Summarize the latest news",
            "Give me a summary of AI developments",
            "Create a brief overview",
            "Recap the week's events",
        ]
        for prompt in prompts:
            assert detect_intent_keywords(prompt) == "summarize"

    def test_detect_analyze_intent(self):
        """Test detecting analyze intent."""
        prompts = [
            "Analyze market trends",
            "Deep dive into AI",
            "In-depth analysis of trends",
            "Study the industry patterns",
        ]
        for prompt in prompts:
            assert detect_intent_keywords(prompt) == "analyze"

    def test_detect_compare_intent(self):
        """Test detecting compare intent."""
        prompts = [
            "Compare Python vs JavaScript",
            "What's the difference between AWS and GCP",
            "React versus Vue comparison",
        ]
        for prompt in prompts:
            assert detect_intent_keywords(prompt) == "compare"

    def test_detect_generate_intent(self):
        """Test detecting generate intent."""
        prompts = [
            "Write a newsletter about AI",
            "Create content for technology",
            "Generate an article",
            "Compose an essay",
            "Draft a report",
        ]
        for prompt in prompts:
            assert detect_intent_keywords(prompt) == "generate"

    def test_default_intent_is_research(self):
        """Test default intent when no keywords match."""
        assert detect_intent_keywords("AI and machine learning") == "research"
        assert detect_intent_keywords("Just some random text") == "research"

    def test_case_insensitive_detection(self):
        """Test intent detection is case insensitive."""
        assert detect_intent_keywords("FIND articles") == "research"
        assert detect_intent_keywords("SUMMARIZE news") == "summarize"


class TestToneKeywords:
    """Test tone keyword detection."""

    def test_tone_keywords_defined(self):
        """Test all tone categories have keywords."""
        expected_tones = ["professional", "casual", "formal", "enthusiastic"]
        for tone in expected_tones:
            assert tone in TONE_KEYWORDS
            assert len(TONE_KEYWORDS[tone]) > 0

    def test_detect_professional_tone(self):
        """Test detecting professional tone."""
        prompts = [
            "Write in a professional manner",
            "Keep it business-like",
            "Corporate style newsletter",
        ]
        for prompt in prompts:
            assert detect_tone_keywords(prompt) == "professional"

    def test_detect_casual_tone(self):
        """Test detecting casual tone."""
        prompts = [
            "Keep it casual and friendly",
            "Conversational style",
            "Relaxed tone please",
        ]
        for prompt in prompts:
            assert detect_tone_keywords(prompt) == "casual"

    def test_detect_formal_tone(self):
        """Test detecting formal tone."""
        prompts = [
            "Use an academic style",
            "Write it scholarly",
            "Technical documentation style",
        ]
        for prompt in prompts:
            assert detect_tone_keywords(prompt) == "formal"

    def test_detect_enthusiastic_tone(self):
        """Test detecting enthusiastic tone."""
        prompts = [
            "Make it exciting and enthusiastic",
            "Engaging and energetic",
        ]
        for prompt in prompts:
            assert detect_tone_keywords(prompt) == "enthusiastic"

    def test_no_tone_detected(self):
        """Test None returned when no tone keywords found."""
        assert detect_tone_keywords("Find AI articles") is None
        assert detect_tone_keywords("Just some text") is None


class TestTimePatterns:
    """Test time range pattern detection."""

    def test_time_patterns_defined(self):
        """Test time patterns are defined with day values."""
        assert "today" in TIME_PATTERNS
        assert "this week" in TIME_PATTERNS
        assert "this month" in TIME_PATTERNS
        assert all(isinstance(v, int) for v in TIME_PATTERNS.values())

    def test_detect_today(self):
        """Test detecting today."""
        assert detect_time_range("Find articles from today") == 1

    def test_detect_this_week(self):
        """Test detecting this week."""
        assert detect_time_range("News from this week") == 7

    def test_detect_last_week(self):
        """Test detecting last week."""
        assert detect_time_range("Articles from last week") == 7

    def test_detect_this_month(self):
        """Test detecting this month."""
        assert detect_time_range("Updates from this month") == 30

    def test_detect_recent(self):
        """Test detecting recent."""
        assert detect_time_range("Find recent articles") == 7

    def test_detect_latest(self):
        """Test detecting latest."""
        assert detect_time_range("Get the latest news") == 3

    def test_no_time_range_detected(self):
        """Test None returned when no time pattern found."""
        assert detect_time_range("Find AI articles") is None
        assert detect_time_range("Just some text") is None


class TestExtractQuotedTopics:
    """Test quoted topic extraction."""

    def test_extract_double_quoted_topics(self):
        """Test extracting topics in double quotes."""
        result = extract_quoted_topics('Find articles about "machine learning"')
        assert "machine learning" in result

    def test_extract_single_quoted_topics(self):
        """Test extracting topics in single quotes."""
        result = extract_quoted_topics("Find articles about 'artificial intelligence'")
        assert "artificial intelligence" in result

    def test_extract_multiple_topics(self):
        """Test extracting multiple quoted topics."""
        result = extract_quoted_topics(
            'Find "AI" and "machine learning" articles'
        )
        assert "AI" in result
        assert "machine learning" in result

    def test_extract_mixed_quotes(self):
        """Test extracting with mixed quote types."""
        result = extract_quoted_topics(
            "Find \"AI\" and 'ML' articles"
        )
        assert "AI" in result
        assert "ML" in result

    def test_no_quotes(self):
        """Test empty list when no quotes present."""
        result = extract_quoted_topics("Find AI articles")
        assert result == []

    def test_empty_quotes(self):
        """Test handling of empty quotes."""
        result = extract_quoted_topics('Find "" articles')
        # Empty string might be included, but that's OK
        assert isinstance(result, list)
