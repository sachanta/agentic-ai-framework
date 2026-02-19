"""
Tests for Newsletter Workflow Nodes.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.platforms.newsletter.orchestrator.nodes import (
    get_preferences_node,
    process_prompt_node,
    research_node,
    generate_content_node,
    create_subjects_node,
    format_email_node,
    store_newsletter_node,
    send_email_node,
)
from app.platforms.newsletter.orchestrator.state import NewsletterState


class TestNodeImports:
    """Tests for node module imports."""

    def test_get_preferences_node_import(self):
        """Can import get_preferences_node."""
        assert get_preferences_node is not None

    def test_process_prompt_node_import(self):
        """Can import process_prompt_node."""
        assert process_prompt_node is not None

    def test_research_node_import(self):
        """Can import research_node."""
        assert research_node is not None

    def test_generate_content_node_import(self):
        """Can import generate_content_node."""
        assert generate_content_node is not None

    def test_create_subjects_node_import(self):
        """Can import create_subjects_node."""
        assert create_subjects_node is not None

    def test_format_email_node_import(self):
        """Can import format_email_node."""
        assert format_email_node is not None

    def test_store_newsletter_node_import(self):
        """Can import store_newsletter_node."""
        assert store_newsletter_node is not None

    def test_send_email_node_import(self):
        """Can import send_email_node."""
        assert send_email_node is not None


class TestGetPreferencesNode:
    """Tests for get_preferences_node."""

    @pytest.mark.asyncio
    async def test_get_preferences_node_success(self):
        """get_preferences_node returns preferences on success."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": True,
            "preferences": {"topics": ["tech"], "tone": "casual"},
        })

        with patch(
            "app.platforms.newsletter.agents.PreferenceAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {"user_id": "user123"}
            result = await get_preferences_node(state)

            assert result["preferences_applied"] is True
            assert result["preferences"]["topics"] == ["tech"]

    @pytest.mark.asyncio
    async def test_get_preferences_node_failure(self):
        """get_preferences_node handles agent failure."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": False,
            "error": "User not found",
        })

        with patch(
            "app.platforms.newsletter.agents.PreferenceAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {"user_id": "user123"}
            result = await get_preferences_node(state)

            assert result["preferences_applied"] is False
            assert result["preferences"] == {}

    @pytest.mark.asyncio
    async def test_get_preferences_node_exception(self):
        """get_preferences_node handles exceptions."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(side_effect=Exception("Connection error"))

        with patch(
            "app.platforms.newsletter.agents.PreferenceAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {"user_id": "user123"}
            result = await get_preferences_node(state)

            assert result["preferences_applied"] is False
            assert "error" in result


class TestProcessPromptNode:
    """Tests for process_prompt_node."""

    @pytest.mark.asyncio
    async def test_process_prompt_node_no_prompt(self):
        """process_prompt_node skips when no custom_prompt."""
        state: NewsletterState = {"user_id": "user123", "custom_prompt": None}
        result = await process_prompt_node(state)

        assert result["prompt_analysis"] is None
        assert result["extracted_topics"] is None

    @pytest.mark.asyncio
    async def test_process_prompt_node_with_prompt(self):
        """process_prompt_node processes custom prompt."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": True,
            "analysis": {"topics": ["AI", "ML"], "intent": "educational"},
        })

        with patch(
            "app.platforms.newsletter.agents.CustomPromptAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "custom_prompt": "Focus on AI advancements",
                "topics": ["tech"],
            }
            result = await process_prompt_node(state)

            assert result["extracted_topics"] == ["AI", "ML"]
            # Topics should be merged
            assert "AI" in result["topics"]
            assert "tech" in result["topics"]


class TestResearchNode:
    """Tests for research_node."""

    @pytest.mark.asyncio
    async def test_research_node_success(self):
        """research_node returns articles on success."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": True,
            "articles": [
                {"title": "AI News", "url": "https://example.com/ai"},
            ],
            "metadata": {"total_searched": 100},
        })

        with patch(
            "app.platforms.newsletter.agents.ResearchAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "topics": ["AI"],
                "max_articles": 10,
            }
            result = await research_node(state)

            assert result["research_completed"] is True
            assert len(result["articles"]) == 1
            assert result["articles"][0]["title"] == "AI News"

    @pytest.mark.asyncio
    async def test_research_node_failure(self):
        """research_node handles failure."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": False,
            "error": "API rate limit exceeded",
        })

        with patch(
            "app.platforms.newsletter.agents.ResearchAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "topics": ["AI"],
            }
            result = await research_node(state)

            assert result["research_completed"] is False
            assert result["articles"] == []


class TestGenerateContentNode:
    """Tests for generate_content_node."""

    @pytest.mark.asyncio
    async def test_generate_content_node_success(self):
        """generate_content_node generates content."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": True,
            "newsletter": {
                "markdown": "# Newsletter\n\nContent here",
                "html": "<h1>Newsletter</h1>",
                "text": "Newsletter\n\nContent here",
                "word_count": 50,
            },
        })

        with patch(
            "app.platforms.newsletter.agents.WritingAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "articles": [{"title": "Test"}],
                "tone": "professional",
            }
            result = await generate_content_node(state)

            assert result["content_generated"] is True
            assert "# Newsletter" in result["newsletter_content"]
            assert result["word_count"] == 50

    @pytest.mark.asyncio
    async def test_generate_content_node_failure(self):
        """generate_content_node handles failure."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": False,
            "error": "LLM error",
        })

        with patch(
            "app.platforms.newsletter.agents.WritingAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "articles": [],
            }
            result = await generate_content_node(state)

            assert result["content_generated"] is False


class TestCreateSubjectsNode:
    """Tests for create_subjects_node."""

    @pytest.mark.asyncio
    async def test_create_subjects_node_success(self):
        """create_subjects_node generates subject lines."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": True,
            "subject_lines": [
                "Weekly Tech Digest",
                "AI Updates You Need to Know",
                "This Week in Tech",
            ],
        })

        with patch(
            "app.platforms.newsletter.agents.WritingAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "newsletter_content": "# Newsletter content",
                "tone": "professional",
            }
            result = await create_subjects_node(state)

            assert result["subjects_generated"] is True
            assert len(result["subject_lines"]) == 3

    @pytest.mark.asyncio
    async def test_create_subjects_node_fallback(self):
        """create_subjects_node uses fallback on failure."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": False,
        })

        with patch(
            "app.platforms.newsletter.agents.WritingAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "newsletter_content": "# Newsletter content",
            }
            result = await create_subjects_node(state)

            assert result["subjects_generated"] is True
            assert any(s["text"] == "Your Newsletter Update" for s in result["subject_lines"])


class TestFormatEmailNode:
    """Tests for format_email_node."""

    @pytest.mark.asyncio
    async def test_format_email_node_success(self):
        """format_email_node formats content for email."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": True,
            "formats": {
                "html": "<html><body>Newsletter</body></html>",
                "plain_text": "Newsletter content",
            },
        })

        with patch(
            "app.platforms.newsletter.agents.WritingAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "newsletter_content": "# Newsletter",
            }
            result = await format_email_node(state)

            assert result["current_step"] == "format_email"
            assert "newsletter_html" in result

    @pytest.mark.asyncio
    async def test_format_email_node_preserves_existing(self):
        """format_email_node preserves existing formats on failure."""
        mock_agent = MagicMock()
        mock_agent.run = AsyncMock(return_value={
            "success": False,
        })

        with patch(
            "app.platforms.newsletter.agents.WritingAgent",
            return_value=mock_agent,
        ):
            state: NewsletterState = {
                "newsletter_content": "# Newsletter",
                "newsletter_html": "<p>Existing</p>",
            }
            result = await format_email_node(state)

            assert result["current_step"] == "format_email"


class TestSendEmailNode:
    """Tests for send_email_node."""

    @pytest.mark.asyncio
    async def test_send_email_node_marks_complete(self):
        """send_email_node marks workflow as completed."""
        state: NewsletterState = {
            "newsletter_html": "<p>Content</p>",
            "selected_subject": "Newsletter",
        }
        result = await send_email_node(state)

        assert result["email_sent"] is True
        assert result["status"] == "completed"
        assert result["current_step"] == "send_email"


class TestStoreNewsletterNode:
    """Tests for store_newsletter_node."""

    @pytest.mark.asyncio
    async def test_store_newsletter_node_success(self):
        """store_newsletter_node stores newsletter in database."""
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(return_value="newsletter-123")

        with patch(
            "app.platforms.newsletter.repositories.NewsletterRepository",
            return_value=mock_repo,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "workflow_id": "workflow-123",
                "newsletter_content": "# Content",
                "newsletter_html": "<p>Content</p>",
                "newsletter_plain": "Content",
                "subject_lines": ["Subject 1"],
                "selected_subject": "Subject 1",
                "topics": ["tech"],
                "tone": "professional",
                "word_count": 100,
                "articles": [],
            }
            result = await store_newsletter_node(state)

            assert result["stored_in_db"] is True
            assert result["newsletter_id"] == "newsletter-123"

    @pytest.mark.asyncio
    async def test_store_newsletter_node_failure(self):
        """store_newsletter_node handles failure."""
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock(side_effect=Exception("DB error"))

        with patch(
            "app.platforms.newsletter.repositories.NewsletterRepository",
            return_value=mock_repo,
        ):
            state: NewsletterState = {
                "user_id": "user123",
                "workflow_id": "workflow-123",
                "newsletter_content": "# Content",
                "newsletter_html": "<p>Content</p>",
                "newsletter_plain": "Content",
                "subject_lines": ["Subject 1"],
                "topics": ["tech"],
                "tone": "professional",
                "word_count": 100,
                "articles": [],
            }
            result = await store_newsletter_node(state)

            assert result["stored_in_db"] is False
            assert "error" in result
