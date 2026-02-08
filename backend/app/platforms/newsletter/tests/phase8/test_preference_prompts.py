"""
Tests for Preference Agent prompts.

Tests prompt templates and helper functions.
"""
import pytest


class TestPreferencePrompts:
    """Tests for prompt templates."""

    def test_preference_system_prompt_exists(self):
        """Verify system prompt is defined."""
        from app.platforms.newsletter.agents.preference.prompts import PREFERENCE_SYSTEM_PROMPT

        assert PREFERENCE_SYSTEM_PROMPT is not None
        assert len(PREFERENCE_SYSTEM_PROMPT) > 50
        assert "preference" in PREFERENCE_SYSTEM_PROMPT.lower()

    def test_analyze_preferences_prompt_has_placeholders(self):
        """Verify analyze prompt has required placeholders."""
        from app.platforms.newsletter.agents.preference.prompts import ANALYZE_PREFERENCES_PROMPT

        assert "{preferences}" in ANALYZE_PREFERENCES_PROMPT
        assert "{engagement_history}" in ANALYZE_PREFERENCES_PROMPT

    def test_recommend_preferences_prompt_has_placeholders(self):
        """Verify recommend prompt has required placeholders."""
        from app.platforms.newsletter.agents.preference.prompts import RECOMMEND_PREFERENCES_PROMPT

        assert "{preferences}" in RECOMMEND_PREFERENCES_PROMPT
        assert "{analysis}" in RECOMMEND_PREFERENCES_PROMPT

    def test_learn_from_engagement_prompt_has_placeholders(self):
        """Verify learn prompt has required placeholders."""
        from app.platforms.newsletter.agents.preference.prompts import LEARN_FROM_ENGAGEMENT_PROMPT

        assert "{topics}" in LEARN_FROM_ENGAGEMENT_PROMPT
        assert "{tone}" in LEARN_FROM_ENGAGEMENT_PROMPT
        assert "{opened}" in LEARN_FROM_ENGAGEMENT_PROMPT
        assert "{clicked_links}" in LEARN_FROM_ENGAGEMENT_PROMPT

    def test_prompts_request_json_output(self):
        """Verify prompts that need JSON request JSON format."""
        from app.platforms.newsletter.agents.preference.prompts import (
            ANALYZE_PREFERENCES_PROMPT,
            RECOMMEND_PREFERENCES_PROMPT,
            LEARN_FROM_ENGAGEMENT_PROMPT,
        )

        assert "json" in ANALYZE_PREFERENCES_PROMPT.lower()
        assert "json" in RECOMMEND_PREFERENCES_PROMPT.lower()
        assert "json" in LEARN_FROM_ENGAGEMENT_PROMPT.lower()


class TestFormatPreferencesForPrompt:
    """Tests for format_preferences_for_prompt helper."""

    def test_formats_basic_preferences(self):
        """Test formatting basic preferences."""
        from app.platforms.newsletter.agents.preference.prompts import format_preferences_for_prompt

        preferences = {
            "topics": ["AI", "technology"],
            "tone": "professional",
            "frequency": "weekly",
            "max_articles": 10,
        }

        result = format_preferences_for_prompt(preferences)

        assert "AI, technology" in result
        assert "professional" in result
        assert "weekly" in result

    def test_formats_empty_topics(self):
        """Test formatting when topics are empty."""
        from app.platforms.newsletter.agents.preference.prompts import format_preferences_for_prompt

        preferences = {"topics": []}

        result = format_preferences_for_prompt(preferences)

        assert "None set" in result

    def test_includes_source_lists(self):
        """Test that source whitelist/blacklist are included."""
        from app.platforms.newsletter.agents.preference.prompts import format_preferences_for_prompt

        preferences = {
            "topics": ["AI"],
            "sources_whitelist": ["TechCrunch", "Wired"],
            "sources_blacklist": ["Spam Site"],
        }

        result = format_preferences_for_prompt(preferences)

        assert "TechCrunch" in result
        assert "Spam Site" in result

    def test_handles_missing_fields(self):
        """Test graceful handling of missing fields."""
        from app.platforms.newsletter.agents.preference.prompts import format_preferences_for_prompt

        preferences = {}

        result = format_preferences_for_prompt(preferences)

        # Should use defaults
        assert "professional" in result
        assert "weekly" in result


class TestFormatEngagementHistory:
    """Tests for format_engagement_history helper."""

    def test_formats_engagement_list(self):
        """Test formatting engagement history."""
        from app.platforms.newsletter.agents.preference.prompts import format_engagement_history

        engagements = [
            {"opened": True, "clicked_links": ["url1", "url2"], "read_time_seconds": 120, "rating": 4},
            {"opened": False, "clicked_links": [], "read_time_seconds": 0, "rating": None},
        ]

        result = format_engagement_history(engagements)

        assert "1." in result
        assert "2." in result
        assert "Yes" in result  # opened: True
        assert "No" in result   # opened: False

    def test_handles_empty_list(self):
        """Test handling of empty engagement list."""
        from app.platforms.newsletter.agents.preference.prompts import format_engagement_history

        result = format_engagement_history([])

        assert "No engagement history" in result

    def test_limits_to_ten_entries(self):
        """Test that history is limited to 10 entries."""
        from app.platforms.newsletter.agents.preference.prompts import format_engagement_history

        engagements = [{"opened": True} for _ in range(20)]

        result = format_engagement_history(engagements)

        # Count numbered entries
        count = sum(1 for line in result.split("\n") if line.strip().startswith(tuple("0123456789")))
        assert count <= 10

    def test_shows_click_count(self):
        """Test that click count is shown."""
        from app.platforms.newsletter.agents.preference.prompts import format_engagement_history

        engagements = [{"opened": True, "clicked_links": ["a", "b", "c"]}]

        result = format_engagement_history(engagements)

        assert "Clicks: 3" in result
