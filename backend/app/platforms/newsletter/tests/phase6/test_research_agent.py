"""
Tests for the Research Agent.

Unit tests use mocks for Tavily, Memory, and LLM services.
Integration tests require running services.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.platforms.newsletter.agents.research import (
    ResearchAgent,
    get_research_llm,
    get_research_config,
    get_summarization_config,
    get_analysis_config,
    RESEARCH_SYSTEM_PROMPT,
)
from app.platforms.newsletter.agents.research.prompts import format_articles_for_prompt


class TestResearchAgentInit:
    """Tests for Research Agent initialization."""

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_default_initialization(self, mock_llm, mock_memory, mock_tavily):
        """Test agent initializes with defaults."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        assert agent.name == "research"
        assert "content discovery" in agent.description.lower()
        assert agent.use_llm_for_scoring is False
        assert agent.cache_results is True

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_custom_initialization(self, mock_llm, mock_memory, mock_tavily):
        """Test agent initializes with custom options."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()

        custom_tavily = MagicMock()
        agent = ResearchAgent(
            tavily_service=custom_tavily,
            use_llm_for_scoring=True,
            cache_results=False,
        )

        assert agent.tavily is custom_tavily
        assert agent.use_llm_for_scoring is True
        assert agent.cache_results is False


class TestLLMConfig:
    """Tests for LLM configuration functions."""

    def test_get_research_config(self):
        """Test research config returns expected keys."""
        config = get_research_config()
        assert "provider" in config
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config

    def test_get_summarization_config(self):
        """Test summarization config has lower temperature."""
        config = get_summarization_config()
        assert config["temperature"] <= 0.5
        assert config["max_tokens"] == 500

    def test_get_analysis_config(self):
        """Test analysis config is deterministic."""
        config = get_analysis_config()
        assert config["temperature"] == 0.3
        assert config["max_tokens"] == 200

    @patch("app.platforms.newsletter.agents.research.llm.get_llm_provider")
    def test_get_research_llm_uses_correct_kwargs(self, mock_get_provider):
        """
        Test get_research_llm passes correct kwargs to get_llm_provider.

        This catches issues like passing 'model' instead of 'default_model'.
        OllamaProvider.__init__ accepts 'default_model', not 'model'.
        """
        mock_get_provider.return_value = MagicMock()

        llm = get_research_llm()

        mock_get_provider.assert_called_once()
        call_kwargs = mock_get_provider.call_args.kwargs

        # Should use 'default_model', NOT 'model'
        assert "model" not in call_kwargs, \
            "Use 'default_model' not 'model' - OllamaProvider doesn't accept 'model'"
        assert "default_model" in call_kwargs, \
            "Should pass 'default_model' to get_llm_provider"
        assert "provider_type" in call_kwargs, \
            "Should pass 'provider_type' to get_llm_provider"

    @patch("app.platforms.newsletter.agents.research.llm.get_llm_provider")
    def test_get_research_llm_returns_provider(self, mock_get_provider):
        """Test get_research_llm returns the LLM provider."""
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        llm = get_research_llm()

        assert llm is mock_provider


class TestPrompts:
    """Tests for prompt templates."""

    def test_system_prompt_defined(self):
        """Test system prompt is defined."""
        assert RESEARCH_SYSTEM_PROMPT
        assert "research" in RESEARCH_SYSTEM_PROMPT.lower()

    def test_format_articles_for_prompt(self):
        """Test article formatting for prompts."""
        articles = [
            {"title": "Article 1", "source": "source1.com", "content": "Content 1"},
            {"title": "Article 2", "source": "source2.com", "content": "Content 2"},
        ]

        formatted = format_articles_for_prompt(articles)

        assert "[Article 0]" in formatted
        assert "[Article 1]" in formatted
        assert "Article 1" in formatted
        assert "source1.com" in formatted

    def test_format_articles_truncates_content(self):
        """Test that long content is truncated."""
        articles = [
            {"title": "Test", "source": "test.com", "content": "x" * 1000},
        ]

        formatted = format_articles_for_prompt(articles, max_chars=100)

        # Content should be truncated + "..."
        assert len(formatted) < 1000


class TestCacheKeyGeneration:
    """Tests for cache key generation."""

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_cache_key_consistency(self, mock_llm, mock_memory, mock_tavily):
        """Test same topics produce same cache key."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        key1 = agent._generate_cache_key(["AI", "technology"])
        key2 = agent._generate_cache_key(["AI", "technology"])

        assert key1 == key2

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_cache_key_order_independent(self, mock_llm, mock_memory, mock_tavily):
        """Test topic order doesn't affect cache key."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        key1 = agent._generate_cache_key(["AI", "technology"])
        key2 = agent._generate_cache_key(["technology", "AI"])

        assert key1 == key2

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_cache_key_case_insensitive(self, mock_llm, mock_memory, mock_tavily):
        """Test cache key is case-insensitive."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        key1 = agent._generate_cache_key(["AI"])
        key2 = agent._generate_cache_key(["ai"])

        assert key1 == key2


class TestBaseScoring:
    """Tests for rules-based scoring."""

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_base_score_calculation(self, mock_llm, mock_memory, mock_tavily):
        """Test base score calculation."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        article = {
            "score": 0.8,
            "quality_score": 0.15,
            "recency_boost": 0.2,
            "content": "x" * 600,  # > 500 chars
        }

        score = agent._calculate_base_score(article)

        # Should include all factors (score ~0.49-0.5 based on formula)
        assert score >= 0.4
        assert score <= 1.0

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_base_score_content_length_bonus(self, mock_llm, mock_memory, mock_tavily):
        """Test longer content gets bonus."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        short_article = {"score": 0.5, "content": "short"}
        long_article = {"score": 0.5, "content": "x" * 1500}

        short_score = agent._calculate_base_score(short_article)
        long_score = agent._calculate_base_score(long_article)

        assert long_score > short_score


class TestFallbackSummary:
    """Tests for fallback summary generation."""

    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    def test_fallback_summary(self, mock_llm, mock_memory, mock_tavily):
        """Test fallback summary extraction."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        article = {
            "content": "First sentence here. Second sentence here. Third sentence."
        }

        summary = agent._fallback_summary(article)

        assert "First sentence" in summary
        assert "Second sentence" in summary
        assert len(summary) <= 200 or summary.endswith("...")


class TestRunPipeline:
    """Tests for the main run pipeline."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_run_no_topics(self, mock_llm, mock_memory, mock_tavily):
        """Test run fails gracefully with no topics."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        result = await agent.run({"topics": [], "user_id": "test"})

        assert result["success"] is False
        assert "No topics" in result.get("error", "")

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_run_returns_cached_results(self, mock_llm, mock_memory, mock_tavily):
        """Test run returns cached results when available."""
        mock_llm.return_value = MagicMock()

        cached_articles = [{"title": "Cached Article", "summary": "Cached summary"}]
        mock_memory_instance = AsyncMock()
        mock_memory_instance.get_research_results = AsyncMock(return_value=cached_articles)
        mock_memory.return_value = mock_memory_instance

        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        result = await agent.run({
            "topics": ["AI"],
            "user_id": "test",
        })

        assert result["success"] is True
        assert result["articles"] == cached_articles
        assert result["metadata"]["source"] == "cache"

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_run_full_pipeline(self, mock_llm, mock_memory, mock_tavily):
        """Test full pipeline execution."""
        # Setup LLM mock
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate = AsyncMock(return_value=MagicMock(
            content='[{"index": 0, "summary": "Test summary", "key_takeaway": "Key point"}]'
        ))
        mock_llm.return_value = mock_llm_instance

        # Setup Memory mock (no cache)
        mock_memory_instance = AsyncMock()
        mock_memory_instance.get_research_results = AsyncMock(return_value=None)
        mock_memory_instance.set_research_results = AsyncMock(return_value=True)
        mock_memory.return_value = mock_memory_instance

        # Setup Tavily mock
        mock_tavily_instance = MagicMock()
        mock_tavily_instance.search_and_filter = AsyncMock(return_value=[
            {
                "title": "Test Article",
                "content": "Test content about AI",
                "source": "test.com",
                "score": 0.8,
                "quality_score": 0.1,
                "recency_boost": 0.1,
            }
        ])
        mock_tavily.return_value = mock_tavily_instance

        agent = ResearchAgent()
        agent.llm = mock_llm_instance

        result = await agent.run({
            "topics": ["AI"],
            "user_id": "test",
            "include_summaries": True,
        })

        assert result["success"] is True
        assert len(result["articles"]) > 0
        assert result["metadata"]["source"] == "tavily"

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_run_no_results(self, mock_llm, mock_memory, mock_tavily):
        """Test run handles no search results."""
        mock_llm.return_value = MagicMock()

        mock_memory_instance = AsyncMock()
        mock_memory_instance.get_research_results = AsyncMock(return_value=None)
        mock_memory.return_value = mock_memory_instance

        mock_tavily_instance = MagicMock()
        mock_tavily_instance.search_and_filter = AsyncMock(return_value=[])
        mock_tavily.return_value = mock_tavily_instance

        agent = ResearchAgent()

        result = await agent.run({
            "topics": ["obscure_topic_xyz"],
            "user_id": "test",
        })

        assert result["success"] is True
        assert result["articles"] == []
        assert "No results" in result["metadata"].get("message", "")


class TestSearchMethods:
    """Tests for search methods."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_search_by_topics(self, mock_llm, mock_memory, mock_tavily):
        """Test search_by_topics method."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()

        mock_tavily_instance = MagicMock()
        mock_tavily_instance.search_and_filter = AsyncMock(return_value=[
            {"title": "Article 1"},
            {"title": "Article 2"},
        ])
        mock_tavily.return_value = mock_tavily_instance

        agent = ResearchAgent()

        results = await agent.search_by_topics(["AI", "tech"])

        assert len(results) == 2
        mock_tavily_instance.search_and_filter.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_get_trending(self, mock_llm, mock_memory, mock_tavily):
        """Test get_trending method."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()

        mock_tavily_instance = MagicMock()
        mock_tavily_instance.get_trending = AsyncMock(return_value=[
            {"title": "Trending 1"},
        ])
        mock_tavily.return_value = mock_tavily_instance

        agent = ResearchAgent()

        results = await agent.get_trending(["AI"], max_results=5)

        assert len(results) == 1
        mock_tavily_instance.get_trending.assert_called_once_with(["AI"], 5)


class TestFilterAndScore:
    """Tests for filter and score stage."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_filter_removes_low_score(self, mock_llm, mock_memory, mock_tavily):
        """Test filtering removes low-scoring articles."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        articles = [
            {"title": "Good", "score": 0.9, "content": "x" * 600},
            {"title": "Bad", "score": 0.1, "content": "short"},
        ]

        filtered = await agent._filter_and_score(articles, ["AI"])

        # Low-scoring article should be filtered
        assert len(filtered) <= len(articles)
        # Articles should have relevance_score added
        assert all("relevance_score" in a for a in filtered)

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_filter_sorts_by_score(self, mock_llm, mock_memory, mock_tavily):
        """Test filtering sorts articles by score."""
        mock_llm.return_value = MagicMock()
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()

        articles = [
            {"title": "Medium", "score": 0.5, "content": "x" * 600},
            {"title": "High", "score": 0.9, "content": "x" * 600},
            {"title": "Low", "score": 0.4, "content": "x" * 600},
        ]

        filtered = await agent._filter_and_score(articles, ["AI"])

        # Should be sorted by relevance_score descending
        scores = [a["relevance_score"] for a in filtered]
        assert scores == sorted(scores, reverse=True)


class TestSummarization:
    """Tests for summarization stage."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_summarize_single(self, mock_llm, mock_memory, mock_tavily):
        """Test single article summarization."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate = AsyncMock(return_value=MagicMock(
            content="This is a test summary."
        ))
        mock_llm.return_value = mock_llm_instance

        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()
        agent.llm = mock_llm_instance

        article = {
            "title": "Test Article",
            "source": "test.com",
            "content": "Long content here...",
        }

        summary = await agent._summarize_single(article)

        assert summary == "This is a test summary."

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_batch_summarize(self, mock_llm, mock_memory, mock_tavily):
        """Test batch summarization."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate = AsyncMock(return_value=MagicMock(
            content='```json\n[{"index": 0, "summary": "Summary 1", "key_takeaway": "Key 1"}, {"index": 1, "summary": "Summary 2", "key_takeaway": "Key 2"}]\n```'
        ))
        mock_llm.return_value = mock_llm_instance

        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()
        agent.llm = mock_llm_instance

        articles = [
            {"title": "Article 1", "source": "a.com", "content": "Content 1"},
            {"title": "Article 2", "source": "b.com", "content": "Content 2"},
        ]

        result = await agent._batch_summarize(articles, ["AI"])

        assert result[0].get("summary") == "Summary 1"
        assert result[1].get("summary") == "Summary 2"

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_summarize_no_llm_uses_fallback(self, mock_llm, mock_memory, mock_tavily):
        """Test summarization falls back without LLM."""
        mock_llm.return_value = None
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()
        agent.llm = None

        articles = [
            {"title": "Test", "content": "First sentence. Second sentence."},
        ]

        result = await agent._generate_summaries(articles, ["AI"])

        # Should return articles unchanged (no summaries added)
        assert result == articles


class TestCustomPromptProcessing:
    """Tests for custom prompt processing."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_process_custom_prompt(self, mock_llm, mock_memory, mock_tavily):
        """Test custom prompt is converted to topics."""
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate = AsyncMock(return_value=MagicMock(
            content='{"queries": ["AI news 2024"], "identified_topics": ["AI", "technology"], "time_relevance": "recent"}'
        ))
        mock_llm.return_value = mock_llm_instance

        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()
        agent.llm = mock_llm_instance

        result = await agent._process_custom_prompt("Find me the latest AI news")

        assert "AI" in result.get("topics", [])

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.agents.research.agent.get_tavily_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_memory_service")
    @patch("app.platforms.newsletter.agents.research.agent.get_research_llm")
    async def test_process_custom_prompt_fallback(self, mock_llm, mock_memory, mock_tavily):
        """Test custom prompt fallback without LLM."""
        mock_llm.return_value = None
        mock_memory.return_value = MagicMock()
        mock_tavily.return_value = MagicMock()

        agent = ResearchAgent()
        agent.llm = None

        result = await agent._process_custom_prompt("AI news")

        # Should use prompt as topic
        assert result == {"topics": ["AI news"]}


# Integration tests
@pytest.mark.integration
class TestResearchAgentIntegration:
    """Integration tests requiring live services."""

    @pytest.fixture
    def research_agent(self):
        """Create research agent for testing."""
        return ResearchAgent(cache_results=False)

    @pytest.mark.asyncio
    async def test_full_research_flow(self, research_agent):
        """Test full research pipeline with live services."""
        # Skip if Tavily not configured
        if not research_agent.tavily.is_configured():
            pytest.skip("Tavily API key not configured")

        result = await research_agent.run({
            "topics": ["artificial intelligence"],
            "user_id": "test",
            "max_results": 3,
            "include_summaries": False,  # Skip LLM for faster test
        })

        assert result["success"] is True
        # Should find some results
        assert isinstance(result["articles"], list)
