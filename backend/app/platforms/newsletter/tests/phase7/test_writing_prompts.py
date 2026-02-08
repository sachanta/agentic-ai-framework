"""
Tests for Writing Agent prompts.

Tests prompt templates and helper functions.
"""
import pytest
from typing import Dict, Any, List


class TestWritingPrompts:
    """Tests for prompt templates."""

    def test_writing_system_prompt_exists(self):
        """Verify system prompt is defined."""
        from app.platforms.newsletter.agents.writing.prompts import WRITING_SYSTEM_PROMPT

        assert WRITING_SYSTEM_PROMPT is not None
        assert len(WRITING_SYSTEM_PROMPT) > 100
        assert "newsletter" in WRITING_SYSTEM_PROMPT.lower()

    def test_generate_newsletter_prompt_has_placeholders(self):
        """Verify newsletter prompt has required placeholders."""
        from app.platforms.newsletter.agents.writing.prompts import GENERATE_NEWSLETTER_PROMPT

        assert "{tone}" in GENERATE_NEWSLETTER_PROMPT
        assert "{topics}" in GENERATE_NEWSLETTER_PROMPT
        assert "{articles}" in GENERATE_NEWSLETTER_PROMPT
        assert "{rag_context}" in GENERATE_NEWSLETTER_PROMPT

    def test_generate_subject_lines_prompt_has_placeholders(self):
        """Verify subject lines prompt has required placeholders."""
        from app.platforms.newsletter.agents.writing.prompts import GENERATE_SUBJECT_LINES_PROMPT

        assert "{content}" in GENERATE_SUBJECT_LINES_PROMPT
        assert "{tone}" in GENERATE_SUBJECT_LINES_PROMPT
        # Should ask for 5 subject lines
        assert "5" in GENERATE_SUBJECT_LINES_PROMPT

    def test_generate_summary_prompt_has_placeholders(self):
        """Verify summary prompt has required placeholders."""
        from app.platforms.newsletter.agents.writing.prompts import GENERATE_SUMMARY_PROMPT

        assert "{content}" in GENERATE_SUMMARY_PROMPT

    def test_prompts_request_json_output(self):
        """Verify prompts that need JSON request JSON format."""
        from app.platforms.newsletter.agents.writing.prompts import (
            GENERATE_SUBJECT_LINES_PROMPT,
            GENERATE_SUMMARY_PROMPT,
        )

        assert "json" in GENERATE_SUBJECT_LINES_PROMPT.lower()
        assert "json" in GENERATE_SUMMARY_PROMPT.lower()


class TestFormatArticlesForNewsletter:
    """Tests for format_articles_for_newsletter helper."""

    def test_formats_single_article(self):
        """Test formatting a single article."""
        from app.platforms.newsletter.agents.writing.prompts import format_articles_for_newsletter

        articles = [
            {
                "title": "Test Article",
                "source": "TestSource",
                "content": "This is the content.",
                "summary": "This is the summary.",
            }
        ]

        result = format_articles_for_newsletter(articles)

        assert "Test Article" in result
        assert "TestSource" in result
        assert "Article 1" in result

    def test_formats_multiple_articles(self):
        """Test formatting multiple articles."""
        from app.platforms.newsletter.agents.writing.prompts import format_articles_for_newsletter

        articles = [
            {"title": "Article One", "source": "Source1", "content": "Content 1"},
            {"title": "Article Two", "source": "Source2", "content": "Content 2"},
            {"title": "Article Three", "source": "Source3", "content": "Content 3"},
        ]

        result = format_articles_for_newsletter(articles)

        assert "Article 1" in result
        assert "Article 2" in result
        assert "Article 3" in result
        assert "Article One" in result
        assert "Article Two" in result

    def test_uses_summary_over_content(self):
        """Test that summary is preferred over content if available."""
        from app.platforms.newsletter.agents.writing.prompts import format_articles_for_newsletter

        articles = [
            {
                "title": "Test",
                "source": "Source",
                "content": "Long content that should not appear",
                "summary": "Short summary that should appear",
            }
        ]

        result = format_articles_for_newsletter(articles)

        assert "Short summary" in result

    def test_truncates_long_content(self):
        """Test that long content is truncated."""
        from app.platforms.newsletter.agents.writing.prompts import format_articles_for_newsletter

        long_content = "x" * 1000
        articles = [{"title": "Test", "source": "Source", "content": long_content}]

        result = format_articles_for_newsletter(articles, max_chars=100)

        assert "..." in result
        assert len(result) < len(long_content)

    def test_handles_missing_fields(self):
        """Test graceful handling of missing fields."""
        from app.platforms.newsletter.agents.writing.prompts import format_articles_for_newsletter

        articles = [{"title": "Only Title"}]

        result = format_articles_for_newsletter(articles)

        assert "Only Title" in result
        assert "Unknown" in result  # Default source


class TestFormatRagExamples:
    """Tests for format_rag_examples helper."""

    def test_formats_rag_examples(self):
        """Test formatting RAG examples."""
        from app.platforms.newsletter.agents.writing.prompts import format_rag_examples

        examples = [
            {"content": "Example content 1", "engagement_score": 0.85},
            {"content": "Example content 2", "engagement_score": 0.72},
        ]

        result = format_rag_examples(examples)

        assert "Example 1" in result
        assert "Example 2" in result
        assert "85%" in result or "0.85" in result

    def test_limits_examples(self):
        """Test that examples are limited."""
        from app.platforms.newsletter.agents.writing.prompts import format_rag_examples

        examples = [
            {"content": f"Content {i}", "engagement_score": 0.5}
            for i in range(10)
        ]

        result = format_rag_examples(examples, max_examples=2)

        assert "Example 1" in result
        assert "Example 2" in result
        assert "Example 3" not in result

    def test_returns_empty_for_no_examples(self):
        """Test that empty list returns empty string."""
        from app.platforms.newsletter.agents.writing.prompts import format_rag_examples

        result = format_rag_examples([])

        assert result == ""

    def test_truncates_long_content(self):
        """Test that example content is truncated."""
        from app.platforms.newsletter.agents.writing.prompts import format_rag_examples

        examples = [{"content": "x" * 1000, "engagement_score": 0.5}]

        result = format_rag_examples(examples)

        # Content should be truncated to 500 chars + "..."
        assert len(result) < 1000


class TestExtractTopicsFromArticles:
    """Tests for extract_topics_from_articles helper."""

    def test_extracts_topics_field(self):
        """Test extracting topics from articles."""
        from app.platforms.newsletter.agents.writing.prompts import extract_topics_from_articles

        articles = [
            {"title": "Article 1", "topics": ["AI", "technology"]},
            {"title": "Article 2", "topics": ["climate", "environment"]},
        ]

        result = extract_topics_from_articles(articles)

        assert "AI" in result
        assert "technology" in result
        assert "climate" in result

    def test_extracts_matched_topics(self):
        """Test extracting matched_topics from scoring."""
        from app.platforms.newsletter.agents.writing.prompts import extract_topics_from_articles

        articles = [
            {"title": "Article", "matched_topics": ["AI", "ML"]},
        ]

        result = extract_topics_from_articles(articles)

        assert "AI" in result
        assert "ML" in result

    def test_deduplicates_topics(self):
        """Test that duplicate topics are removed."""
        from app.platforms.newsletter.agents.writing.prompts import extract_topics_from_articles

        articles = [
            {"title": "Article 1", "topics": ["AI", "technology"]},
            {"title": "Article 2", "topics": ["AI", "science"]},
        ]

        result = extract_topics_from_articles(articles)

        # AI should only appear once
        assert result.count("AI") <= 1

    def test_limits_topics(self):
        """Test that topics are limited to 5."""
        from app.platforms.newsletter.agents.writing.prompts import extract_topics_from_articles

        articles = [
            {"title": "Article", "topics": [f"topic{i}" for i in range(10)]},
        ]

        result = extract_topics_from_articles(articles)

        assert len(result) <= 5

    def test_handles_empty_articles(self):
        """Test handling of empty article list."""
        from app.platforms.newsletter.agents.writing.prompts import extract_topics_from_articles

        result = extract_topics_from_articles([])

        assert result == []
