"""
Tests for the Writing Agent.

Tests newsletter generation, subject lines, summaries, and RAG integration.
Following CLAUDE.md guidelines:
- Mock at dependency level to catch init bugs
- Test factory functions separately
- Include integration tests (marked for skip if no external API)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List


# Sample test data
SAMPLE_ARTICLES = [
    {
        "title": "AI Advances in Healthcare",
        "source": "TechNews",
        "content": "New AI models are revolutionizing medical diagnosis with unprecedented accuracy...",
        "summary": "AI is transforming healthcare with better diagnostic tools.",
        "topics": ["AI", "healthcare"],
    },
    {
        "title": "Climate Tech Investments Surge",
        "source": "GreenBiz",
        "content": "Venture capital flowing into climate technology startups at record rates...",
        "summary": "Climate tech sees record investment in Q4.",
        "topics": ["climate", "investment"],
    },
    {
        "title": "Remote Work Trends 2024",
        "source": "WorkLife",
        "content": "Companies are adapting to hybrid work models as the new normal...",
        "summary": "Hybrid work becomes the new normal for enterprises.",
        "topics": ["remote work", "business"],
    },
]

SAMPLE_NEWSLETTER_CONTENT = """## AI Advances in Healthcare

New AI models are revolutionizing how doctors diagnose diseases. This breakthrough promises faster and more accurate diagnoses.

## Climate Tech on the Rise

Investment in climate technology has reached record levels, with VCs betting big on sustainability.

## The Future of Work

Hybrid work models are here to stay, with companies finding the right balance between office and remote."""

SAMPLE_SUBJECT_LINES_RESPONSE = """{
    "subject_lines": [
        {"text": "AI, Climate & Work: Your Weekly Digest", "angle": "news"},
        {"text": "3 Trends Shaping Tomorrow's World", "angle": "curiosity"},
        {"text": "What You Missed This Week in Tech", "angle": "benefit"},
        {"text": "Is Your Industry Ready for These Changes?", "angle": "question"},
        {"text": "Breaking: Major Shifts in AI and Climate", "angle": "urgency"}
    ]
}"""

SAMPLE_SUMMARY_RESPONSE = """{
    "summary": [
        "AI is transforming healthcare diagnostics",
        "Climate tech investments hit record highs",
        "Hybrid work becomes mainstream",
        "Companies adapting to new workforce expectations",
        "Tech and sustainability converge"
    ],
    "one_liner": "This week's top stories cover AI in healthcare, climate investment surge, and the hybrid work revolution."
}"""


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response object."""
    def _create_response(content: str):
        mock = MagicMock()
        mock.content = content
        return mock
    return _create_response


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service."""
    mock = MagicMock()
    mock.is_available = MagicMock(return_value=True)
    mock.search_similar = AsyncMock(return_value=[
        {
            "content": "Previous newsletter content example about AI trends...",
            "engagement_score": 0.85,
            "topics": ["AI", "technology"],
        }
    ])
    return mock


class TestWritingAgentInitialization:
    """Tests for WritingAgent initialization - mock at dependency level."""

    def test_agent_initializes_with_default_dependencies(self):
        """Test agent initialization with default dependencies."""
        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service") as mock_rag:

            mock_llm.return_value = MagicMock()
            mock_rag.return_value = MagicMock()

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            assert agent.name == "writing"
            mock_llm.assert_called_once()
            mock_rag.assert_called_once()

    def test_agent_accepts_custom_rag_service(self):
        """Test agent accepts injected RAG service."""
        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm") as mock_llm:
            mock_llm.return_value = MagicMock()
            custom_rag = MagicMock()

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent(rag_service=custom_rag)

            assert agent.rag_service is custom_rag

    def test_agent_respects_use_rag_flag(self):
        """Test agent respects use_rag initialization flag."""
        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service") as mock_rag:

            mock_llm.return_value = MagicMock()
            mock_rag.return_value = MagicMock()

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent(use_rag=False)

            assert agent.use_rag is False

    def test_agent_has_valid_tones(self):
        """Test agent has expected valid tones."""
        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm") as mock_llm, \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service") as mock_rag:

            mock_llm.return_value = MagicMock()
            mock_rag.return_value = MagicMock()

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            assert "professional" in agent.VALID_TONES
            assert "casual" in agent.VALID_TONES
            assert "formal" in agent.VALID_TONES
            assert "enthusiastic" in agent.VALID_TONES


class TestWritingAgentRun:
    """Tests for WritingAgent.run() method - mock at dependency level."""

    @pytest.mark.asyncio
    async def test_run_generates_newsletter(self, mock_llm_response, mock_rag_service):
        """Test that run() generates a complete newsletter."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "user_id": "test_user",
                "tone": "professional",
                "title": "Weekly Digest",
            })

            assert result["success"] is True
            assert result["newsletter"] is not None
            assert "content" in result["newsletter"]
            assert "html" in result["newsletter"]
            assert "text" in result["newsletter"]
            assert "markdown" in result["newsletter"]
            assert "email_html" in result["newsletter"]

    @pytest.mark.asyncio
    async def test_run_returns_subject_lines(self, mock_llm_response, mock_rag_service):
        """Test that run() returns subject lines."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "include_subject_lines": True,
            })

            assert "subject_lines" in result
            assert len(result["subject_lines"]) == 5

    @pytest.mark.asyncio
    async def test_run_returns_summary(self, mock_llm_response, mock_rag_service):
        """Test that run() returns summary bullets."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "include_summary": True,
            })

            assert "summary" in result
            assert "summary" in result["summary"]
            assert len(result["summary"]["summary"]) >= 5

    @pytest.mark.asyncio
    async def test_run_without_articles_returns_error(self, mock_rag_service):
        """Test that run() returns error when no articles provided."""
        mock_llm = MagicMock()

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": [],
                "user_id": "test_user",
            })

            assert result["success"] is False
            assert "error" in result
            assert "No articles" in result["error"]

    @pytest.mark.asyncio
    async def test_run_handles_llm_error(self, mock_rag_service):
        """Test that run() handles LLM errors gracefully."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM Connection Error"))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
            })

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_tone_defaults_to_professional(self, mock_llm_response, mock_rag_service):
        """Test that invalid tone defaults to professional."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "tone": "invalid_tone",
            })

            assert result["success"] is True
            assert result["newsletter"]["tone"] == "professional"


class TestWritingAgentSubjectLines:
    """Tests for WritingAgent.create_subject_lines() method."""

    @pytest.mark.asyncio
    async def test_create_subject_lines_returns_five_options(self, mock_llm_response):
        """Test that create_subject_lines returns 5 options."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value=mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service"):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.create_subject_lines(SAMPLE_NEWSLETTER_CONTENT, "professional")

            assert len(result) == 5
            assert all("text" in sl for sl in result)
            assert all("angle" in sl for sl in result)

    @pytest.mark.asyncio
    async def test_create_subject_lines_uses_creative_config(self, mock_llm_response):
        """Test that subject lines use creative (higher temp) config."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value=mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service"), \
             patch("app.platforms.newsletter.agents.writing.agent.get_creative_config") as mock_config:

            mock_config.return_value = {"temperature": 0.8, "max_tokens": 500}

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()
            await agent.create_subject_lines(SAMPLE_NEWSLETTER_CONTENT, "professional")

            mock_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subject_lines_fallback_on_parse_error(self, mock_llm_response):
        """Test fallback when JSON parsing fails."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value=mock_llm_response("Invalid JSON response"))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service"):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.create_subject_lines(SAMPLE_NEWSLETTER_CONTENT, "professional")

            assert len(result) == 5  # Fallback returns 5
            assert all("text" in sl for sl in result)

    @pytest.mark.asyncio
    async def test_create_subject_lines_fallback_on_exception(self):
        """Test fallback subject lines when LLM fails completely."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM Error"))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service"):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.create_subject_lines(SAMPLE_NEWSLETTER_CONTENT, "professional")

            assert len(result) == 5
            assert all("text" in sl for sl in result)


class TestWritingAgentSummary:
    """Tests for WritingAgent.generate_summary() method."""

    @pytest.mark.asyncio
    async def test_generate_summary_returns_bullets(self, mock_llm_response):
        """Test that generate_summary returns bullet points."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value=mock_llm_response(SAMPLE_SUMMARY_RESPONSE))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service"):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.generate_summary(SAMPLE_NEWSLETTER_CONTENT)

            assert "summary" in result
            assert len(result["summary"]) >= 5
            assert "one_liner" in result

    @pytest.mark.asyncio
    async def test_generate_summary_fallback_on_error(self):
        """Test fallback summary when LLM fails."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("LLM Error"))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service"):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.generate_summary(SAMPLE_NEWSLETTER_CONTENT)

            assert "summary" in result
            assert len(result["summary"]) > 0


class TestWritingAgentRagIntegration:
    """Tests for RAG integration."""

    @pytest.mark.asyncio
    async def test_rag_examples_are_fetched(self, mock_llm_response, mock_rag_service):
        """Test that RAG examples are fetched when enabled."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value=mock_llm_response(SAMPLE_NEWSLETTER_CONTENT))

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent(use_rag=True)

            await agent.generate_newsletter(SAMPLE_ARTICLES, "professional", "test_user")

            mock_rag_service.search_similar.assert_called_once()

    @pytest.mark.asyncio
    async def test_works_without_rag(self, mock_llm_response):
        """Test that agent works when RAG is unavailable."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        mock_rag = MagicMock()
        mock_rag.is_available = MagicMock(return_value=False)

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent(use_rag=True)

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "user_id": "test_user",
            })

            assert result["success"] is True
            assert result["metadata"]["rag_examples_used"] == 0

    @pytest.mark.asyncio
    async def test_rag_disabled_skips_query(self, mock_llm_response, mock_rag_service):
        """Test that RAG is not queried when disabled."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent(use_rag=False)

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "include_rag": False,
            })

            mock_rag_service.search_similar.assert_not_called()


class TestWritingAgentTones:
    """Tests for different tone options."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tone", ["professional", "casual", "formal", "enthusiastic"])
    async def test_all_tones_work(self, tone, mock_llm_response, mock_rag_service):
        """Test that all tone options work correctly."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
                "tone": tone,
            })

            assert result["success"] is True
            assert result["newsletter"]["tone"] == tone


class TestWritingAgentMetadata:
    """Tests for metadata returned by the agent."""

    @pytest.mark.asyncio
    async def test_metadata_includes_article_count(self, mock_llm_response, mock_rag_service):
        """Test metadata includes article count."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
            })

            assert result["metadata"]["article_count"] == len(SAMPLE_ARTICLES)

    @pytest.mark.asyncio
    async def test_metadata_includes_topics(self, mock_llm_response, mock_rag_service):
        """Test metadata includes extracted topics."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(side_effect=[
            mock_llm_response(SAMPLE_NEWSLETTER_CONTENT),
            mock_llm_response(SAMPLE_SUBJECT_LINES_RESPONSE),
            mock_llm_response(SAMPLE_SUMMARY_RESPONSE),
        ])

        with patch("app.platforms.newsletter.agents.writing.agent.get_writing_llm", return_value=mock_llm), \
             patch("app.platforms.newsletter.agents.writing.agent.get_rag_service", return_value=mock_rag_service):

            from app.platforms.newsletter.agents.writing import WritingAgent

            agent = WritingAgent()

            result = await agent.run({
                "articles": SAMPLE_ARTICLES,
            })

            assert "topics" in result["metadata"]
            assert len(result["metadata"]["topics"]) > 0


@pytest.mark.integration
class TestWritingAgentIntegration:
    """Integration tests - require real services.

    These tests are skipped by default. Run with:
    pytest -m integration
    """

    @pytest.mark.asyncio
    async def test_real_newsletter_generation(self):
        """Test newsletter generation with real LLM.

        Requires Ollama or another LLM provider to be running.
        """
        pytest.skip("Requires running LLM service")

        from app.platforms.newsletter.agents.writing import WritingAgent

        agent = WritingAgent(use_rag=False)

        result = await agent.run({
            "articles": SAMPLE_ARTICLES,
            "tone": "professional",
            "include_subject_lines": True,
            "include_summary": True,
        })

        assert result["success"] is True
        assert len(result["newsletter"]["content"]) > 500
        assert len(result["subject_lines"]) == 5
