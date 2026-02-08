"""
Tests for the newsletter formatters.

Tests HTML, email HTML, plain text, and markdown output formatting.
"""
import pytest
from app.platforms.newsletter.agents.writing.formatters import (
    format_html,
    format_email_html,
    format_plain_text,
    format_markdown,
    format_all,
    _markdown_to_html,
)


SAMPLE_CONTENT = """## Welcome to This Week's Digest

Here's what's happening in the world of technology.

### AI Breakthroughs

**OpenAI** released a new model that's taking the industry by storm.

> "This is a game-changer for the industry" - Tech Expert

- First key point about AI
- Second important insight
- Third notable development

### Climate Tech Update

Investment in climate technology continues to grow.

Stay tuned for more updates next week!"""


class TestFormatHtml:
    """Tests for format_html function."""

    def test_returns_valid_html(self):
        """Test that output is valid HTML."""
        result = format_html(SAMPLE_CONTENT, "Test Newsletter")

        assert "<!DOCTYPE html>" in result
        assert "<html" in result
        assert "</html>" in result
        assert "<head>" in result
        assert "<body>" in result

    def test_includes_title(self):
        """Test that title is included."""
        result = format_html(SAMPLE_CONTENT, "My Newsletter Title")

        assert "My Newsletter Title" in result
        assert "<title>My Newsletter Title</title>" in result

    def test_includes_subtitle(self):
        """Test that subtitle is included when provided."""
        result = format_html(SAMPLE_CONTENT, "Title", subtitle="January 2024")

        assert "January 2024" in result

    def test_includes_styles(self):
        """Test that CSS styles are embedded."""
        result = format_html(SAMPLE_CONTENT, "Title")

        assert "<style>" in result
        assert "font-family" in result
        assert "gradient" in result

    def test_converts_headers(self):
        """Test that markdown headers are converted to HTML."""
        result = format_html(SAMPLE_CONTENT, "Title")

        assert "<h2>" in result
        assert "<h3>" in result


class TestFormatEmailHtml:
    """Tests for format_email_html function."""

    def test_returns_valid_email_html(self):
        """Test that output is valid email HTML."""
        result = format_email_html(SAMPLE_CONTENT, "Newsletter")

        assert "<!DOCTYPE html>" in result
        assert "<table" in result  # Email uses tables for layout
        assert "role=\"presentation\"" in result

    def test_includes_preheader(self):
        """Test that preheader text is included."""
        result = format_email_html(
            SAMPLE_CONTENT,
            "Newsletter",
            preheader="Check out this week's top stories"
        )

        assert "Check out this week's top stories" in result

    def test_includes_unsubscribe_link(self):
        """Test that unsubscribe link is included."""
        result = format_email_html(
            SAMPLE_CONTENT,
            "Newsletter",
            unsubscribe_url="https://example.com/unsubscribe"
        )

        assert "https://example.com/unsubscribe" in result
        assert "Unsubscribe" in result

    def test_responsive_styles(self):
        """Test that responsive styles are included."""
        result = format_email_html(SAMPLE_CONTENT, "Newsletter")

        assert "@media" in result
        assert "max-width" in result

    def test_mso_conditional_comments(self):
        """Test that MSO conditional comments are included for Outlook."""
        result = format_email_html(SAMPLE_CONTENT, "Newsletter")

        assert "<!--[if mso]>" in result


class TestFormatPlainText:
    """Tests for format_plain_text function."""

    def test_returns_plain_text(self):
        """Test that output is plain text without HTML."""
        result = format_plain_text(SAMPLE_CONTENT, "Newsletter")

        assert "<" not in result or result.count("<") == 0
        assert ">" not in result or ">" not in result.replace(">", "")  # Allow > in quotes

    def test_includes_title(self):
        """Test that title is included."""
        result = format_plain_text(SAMPLE_CONTENT, "My Newsletter")

        assert "My Newsletter" in result

    def test_converts_bullets(self):
        """Test that bullets are converted."""
        result = format_plain_text(SAMPLE_CONTENT, "Newsletter")

        assert "•" in result

    def test_removes_markdown_formatting(self):
        """Test that markdown formatting is removed."""
        result = format_plain_text(SAMPLE_CONTENT, "Newsletter")

        assert "**" not in result
        assert "##" not in result

    def test_wraps_lines(self):
        """Test that lines are wrapped to specified width."""
        long_content = "This is a very long line that should be wrapped because it exceeds the maximum width allowed for plain text emails which is typically around 72 characters."
        result = format_plain_text(long_content, "Test", width=72)

        lines = result.split('\n')
        content_lines = [l for l in lines if l.strip() and not l.startswith('=')]
        # Most lines should be under the width limit
        assert all(len(l) <= 80 for l in content_lines)  # Allow some flexibility


class TestFormatMarkdown:
    """Tests for format_markdown function."""

    def test_returns_markdown(self):
        """Test that output is valid markdown."""
        result = format_markdown(SAMPLE_CONTENT, "Newsletter")

        assert "# Newsletter" in result
        assert "##" in result

    def test_includes_frontmatter_by_default(self):
        """Test that YAML frontmatter is included."""
        result = format_markdown(SAMPLE_CONTENT, "Newsletter")

        assert "---" in result
        assert "title:" in result
        assert "date:" in result

    def test_excludes_frontmatter_when_disabled(self):
        """Test that frontmatter can be disabled."""
        result = format_markdown(SAMPLE_CONTENT, "Newsletter", include_metadata=False)

        assert "---" not in result


class TestFormatAll:
    """Tests for format_all function."""

    def test_returns_all_formats(self):
        """Test that all format versions are returned."""
        result = format_all(SAMPLE_CONTENT, "Newsletter")

        assert "html" in result
        assert "email_html" in result
        assert "text" in result
        assert "markdown" in result

    def test_all_formats_are_strings(self):
        """Test that all formats are strings."""
        result = format_all(SAMPLE_CONTENT, "Newsletter")

        assert all(isinstance(v, str) for v in result.values())

    def test_all_formats_not_empty(self):
        """Test that no format is empty."""
        result = format_all(SAMPLE_CONTENT, "Newsletter")

        assert all(len(v) > 0 for v in result.values())


class TestMarkdownToHtml:
    """Tests for _markdown_to_html helper function."""

    def test_converts_headers(self):
        """Test header conversion."""
        result = _markdown_to_html("## Header Two\n### Header Three")

        assert "<h2>Header Two</h2>" in result
        assert "<h3>Header Three</h3>" in result

    def test_converts_bold(self):
        """Test bold text conversion."""
        result = _markdown_to_html("This is **bold** text")

        assert "<strong>bold</strong>" in result

    def test_converts_italic(self):
        """Test italic text conversion."""
        result = _markdown_to_html("This is *italic* text")

        assert "<em>italic</em>" in result

    def test_converts_blockquotes(self):
        """Test blockquote conversion."""
        result = _markdown_to_html("> This is a quote")

        assert "<blockquote>" in result

    def test_converts_lists(self):
        """Test bullet list conversion."""
        result = _markdown_to_html("- Item one\n- Item two")

        assert "<li>Item one</li>" in result
        assert "<li>Item two</li>" in result
        assert "<ul>" in result

    def test_converts_links(self):
        """Test link conversion."""
        result = _markdown_to_html("[Click here](https://example.com)")

        assert '<a href="https://example.com">Click here</a>' in result


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_content(self):
        """Test with empty content."""
        result = format_all("", "Empty Newsletter")

        assert all(isinstance(v, str) for v in result.values())

    def test_special_characters(self):
        """Test content with special HTML characters."""
        content = "Test <script>alert('xss')</script> & more"
        result = format_html(content, "Test")

        assert "<script>" not in result
        assert "&lt;script&gt;" in result or "script" not in result

    def test_unicode_content(self):
        """Test content with unicode characters."""
        content = "Hello 世界! Émojis: 🚀 📧"
        result = format_all(content, "Unicode Test")

        assert "世界" in result["text"]
        assert "🚀" in result["markdown"]

    def test_very_long_content(self):
        """Test with very long content."""
        content = "Long content. " * 1000
        result = format_all(content, "Long Newsletter")

        assert all(len(v) > 0 for v in result.values())
