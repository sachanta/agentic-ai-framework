"""
Tavily Search Service tests.

Tests for content discovery via Tavily API.
Unit tests use mocks, integration tests require API key.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta


# ============================================================================
# SearchResult Tests
# ============================================================================

@pytest.mark.stable
class TestSearchResult:
    """Test SearchResult class."""

    def test_search_result_import(self):
        """Test that SearchResult can be imported."""
        from app.platforms.newsletter.services import SearchResult
        assert SearchResult is not None

    def test_search_result_creation(self):
        """Test creating a SearchResult instance."""
        from app.platforms.newsletter.services.tavily import SearchResult

        result = SearchResult(
            title="Test Article",
            url="https://example.com/article",
            content="This is test content for the article.",
            score=0.85,
            published_date="2024-01-15",
            source="example.com",
        )

        assert result.title == "Test Article"
        assert result.url == "https://example.com/article"
        assert result.score == 0.85
        assert result.source == "example.com"

    def test_search_result_extracts_source_from_url(self):
        """Test that source is extracted from URL if not provided."""
        from app.platforms.newsletter.services.tavily import SearchResult

        result = SearchResult(
            title="Test",
            url="https://www.techcrunch.com/article/123",
            content="Content",
        )

        assert result.source == "techcrunch.com"

    def test_search_result_computes_content_hash(self):
        """Test that content hash is computed."""
        from app.platforms.newsletter.services.tavily import SearchResult

        result = SearchResult(
            title="Test",
            url="https://example.com",
            content="Same content here",
        )

        assert result.content_hash is not None
        assert len(result.content_hash) == 32  # MD5 hex length

    def test_search_result_same_content_same_hash(self):
        """Test that same content produces same hash."""
        from app.platforms.newsletter.services.tavily import SearchResult

        result1 = SearchResult(
            title="Test 1",
            url="https://example1.com",
            content="Same content",
        )
        result2 = SearchResult(
            title="Test 2",
            url="https://example2.com",
            content="Same content",
        )

        assert result1.content_hash == result2.content_hash

    def test_search_result_to_dict(self):
        """Test converting SearchResult to dictionary."""
        from app.platforms.newsletter.services.tavily import SearchResult

        result = SearchResult(
            title="Test",
            url="https://example.com",
            content="Content",
            score=0.9,
        )
        result.recency_boost = 0.1
        result.quality_score = 0.15

        d = result.to_dict()

        assert d["title"] == "Test"
        assert d["url"] == "https://example.com"
        assert d["score"] == 0.9
        assert d["recency_boost"] == 0.1
        assert d["quality_score"] == 0.15
        assert d["final_score"] == 0.9 + 0.1 + 0.15


# ============================================================================
# TavilySearchService Tests
# ============================================================================

@pytest.mark.stable
class TestTavilySearchServiceInit:
    """Test TavilySearchService initialization."""

    def test_service_import(self):
        """Test that TavilySearchService can be imported."""
        from app.platforms.newsletter.services import TavilySearchService
        assert TavilySearchService is not None

    def test_service_factory_import(self):
        """Test that get_tavily_service can be imported."""
        from app.platforms.newsletter.services import get_tavily_service
        assert callable(get_tavily_service)

    def test_service_instantiation(self):
        """Test creating a TavilySearchService instance."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        service = TavilySearchService(api_key="test-key")
        assert service.api_key == "test-key"

    def test_service_is_configured_with_key(self):
        """Test is_configured returns True when API key is set."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        service = TavilySearchService(api_key="test-key")
        assert service.is_configured() is True

    def test_service_is_not_configured_without_key(self):
        """Test is_configured returns False without API key."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        with patch("app.platforms.newsletter.services.tavily.config") as mock_config:
            mock_config.TAVILY_API_KEY = None
            service = TavilySearchService()
            assert service.is_configured() is False

    def test_client_raises_without_api_key(self):
        """Test that accessing client without API key raises error."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        with patch("app.platforms.newsletter.services.tavily.config") as mock_config:
            mock_config.TAVILY_API_KEY = None
            service = TavilySearchService()

            with pytest.raises(ValueError, match="Tavily API key not configured"):
                _ = service.client


@pytest.mark.stable
class TestTavilySearchServiceQualityFilter:
    """Test quality filtering functionality."""

    def test_quality_filter_removes_short_content(self):
        """Test that short content is filtered out."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")
        results = [
            SearchResult(title="Short", url="http://a.com", content="Too short"),
            SearchResult(
                title="Long",
                url="http://b.com",
                content="This is a much longer piece of content that should pass the quality filter because it has enough characters to be considered valuable content for a newsletter article.",
            ),
        ]

        filtered = service.apply_quality_filter(results, min_content_length=50)

        assert len(filtered) == 1
        assert filtered[0].title == "Long"

    def test_quality_filter_boosts_high_quality_sources(self):
        """Test that high-quality sources get a boost."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")
        long_content = "x" * 200  # Enough to pass length filter

        results = [
            SearchResult(
                title="TechCrunch",
                url="https://techcrunch.com/article",
                content=long_content,
            ),
            SearchResult(
                title="Random Blog",
                url="https://randomsite.com/post",
                content=long_content,
            ),
        ]

        filtered = service.apply_quality_filter(results)

        tc_result = next(r for r in filtered if "techcrunch" in r.url)
        other_result = next(r for r in filtered if "randomsite" in r.url)

        assert tc_result.quality_score > 0
        assert other_result.quality_score == 0


@pytest.mark.stable
class TestTavilySearchServiceRecencyBoost:
    """Test recency boost functionality."""

    def test_recency_boost_24h_articles(self):
        """Test that articles within 24h get highest boost."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        # Article from 2 hours ago
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        results = [
            SearchResult(
                title="Recent",
                url="http://a.com",
                content="Content",
                published_date=recent_date,
            ),
        ]

        boosted = service.apply_recency_boost(results)

        assert boosted[0].recency_boost == service.RECENCY_24H_BOOST

    def test_recency_boost_within_window(self):
        """Test that articles within recency window get boost."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        # Article from 2 days ago (within default 3-day window)
        older_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        results = [
            SearchResult(
                title="Older",
                url="http://a.com",
                content="Content",
                published_date=older_date,
            ),
        ]

        boosted = service.apply_recency_boost(results, recency_days=3)

        assert boosted[0].recency_boost == service.RECENCY_WINDOW_BOOST

    def test_recency_no_boost_for_old_articles(self):
        """Test that old articles don't get boost."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        # Article from 10 days ago
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        results = [
            SearchResult(
                title="Old",
                url="http://a.com",
                content="Content",
                published_date=old_date,
            ),
        ]

        boosted = service.apply_recency_boost(results, recency_days=3)

        assert boosted[0].recency_boost == 0


@pytest.mark.stable
class TestTavilySearchServiceDeduplication:
    """Test deduplication functionality."""

    def test_deduplicate_exact_duplicates(self):
        """Test that exact duplicate content is removed."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")
        same_content = "This is the exact same content in both results."

        results = [
            SearchResult(title="First", url="http://a.com", content=same_content),
            SearchResult(title="Second", url="http://b.com", content=same_content),
        ]

        deduped = service.deduplicate(results)

        assert len(deduped) == 1
        assert deduped[0].title == "First"  # First one kept

    def test_deduplicate_similar_content(self):
        """Test that similar content is deduplicated."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        results = [
            SearchResult(
                title="First",
                url="http://a.com",
                content="AI breakthrough in healthcare transforms patient diagnosis accuracy.",
            ),
            SearchResult(
                title="Second",
                url="http://b.com",
                content="AI breakthrough in healthcare transforms patient diagnosis accuracy today.",
            ),
        ]

        deduped = service.deduplicate(results, similarity_threshold=0.8)

        assert len(deduped) == 1

    def test_deduplicate_keeps_different_content(self):
        """Test that different content is kept."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        results = [
            SearchResult(
                title="AI Article",
                url="http://a.com",
                content="Artificial intelligence makes major advances in 2024.",
            ),
            SearchResult(
                title="Climate Article",
                url="http://b.com",
                content="New climate technology reduces carbon emissions significantly.",
            ),
        ]

        deduped = service.deduplicate(results)

        assert len(deduped) == 2


@pytest.mark.stable
class TestTavilySearchServiceSorting:
    """Test result sorting functionality."""

    def test_sort_by_score_descending(self):
        """Test sorting by final score in descending order."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        results = [
            SearchResult(title="Low", url="http://a.com", content="x", score=0.5),
            SearchResult(title="High", url="http://b.com", content="x", score=0.9),
            SearchResult(title="Mid", url="http://c.com", content="x", score=0.7),
        ]

        sorted_results = service.sort_by_score(results)

        assert sorted_results[0].title == "High"
        assert sorted_results[1].title == "Mid"
        assert sorted_results[2].title == "Low"

    def test_sort_includes_boosts(self):
        """Test that sorting considers recency and quality boosts."""
        from app.platforms.newsletter.services.tavily import (
            TavilySearchService,
            SearchResult,
        )

        service = TavilySearchService(api_key="test")

        results = [
            SearchResult(title="Base High", url="http://a.com", content="x", score=0.9),
            SearchResult(
                title="Base Low + Boosts", url="http://b.com", content="x", score=0.5
            ),
        ]
        results[1].recency_boost = 0.2
        results[1].quality_score = 0.3

        sorted_results = service.sort_by_score(results)

        # 0.5 + 0.2 + 0.3 = 1.0 > 0.9
        assert sorted_results[0].title == "Base Low + Boosts"


# ============================================================================
# TavilySearchService Search Tests (Mocked)
# ============================================================================

@pytest.mark.stable
class TestTavilySearchServiceSearch:
    """Test search functionality with mocked API."""

    @pytest.fixture
    def mock_tavily_response(self):
        """Mock Tavily API response."""
        return {
            "results": [
                {
                    "title": "AI in Healthcare",
                    "url": "https://techcrunch.com/ai-healthcare",
                    "content": "Artificial intelligence is transforming healthcare with new diagnostic tools that improve patient outcomes significantly.",
                    "score": 0.92,
                    "published_date": "2024-01-15T10:00:00Z",
                },
                {
                    "title": "Climate Tech Funding",
                    "url": "https://reuters.com/climate-funding",
                    "content": "Climate technology startups received record funding in 2024 as investors bet on sustainable solutions to combat global warming.",
                    "score": 0.88,
                    "published_date": "2024-01-14T08:30:00Z",
                },
            ]
        }

    @pytest.mark.asyncio
    async def test_search_topic_returns_results(self, mock_tavily_response):
        """Test that search_topic returns SearchResult objects."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        service = TavilySearchService(api_key="test-key")

        with patch.object(service, "_client") as mock_client:
            mock_client.search = AsyncMock(return_value=mock_tavily_response)
            service._client = mock_client

            results = await service.search_topic("AI")

            assert len(results) == 2
            assert results[0].title == "AI in Healthcare"
            assert results[0].score == 0.92

    @pytest.mark.asyncio
    async def test_search_topics_parallel(self, mock_tavily_response):
        """Test that search_topics searches multiple topics in parallel."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        service = TavilySearchService(api_key="test-key")

        with patch.object(service, "_client") as mock_client:
            mock_client.search = AsyncMock(return_value=mock_tavily_response)
            service._client = mock_client

            results = await service.search_topics(["AI", "Climate"])

            assert "AI" in results
            assert "Climate" in results
            assert len(results["AI"]) == 2
            assert len(results["Climate"]) == 2

    @pytest.mark.asyncio
    async def test_search_and_filter_full_pipeline(self, mock_tavily_response):
        """Test the full search and filter pipeline."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        service = TavilySearchService(api_key="test-key")

        with patch.object(service, "_client") as mock_client:
            mock_client.search = AsyncMock(return_value=mock_tavily_response)
            service._client = mock_client

            results = await service.search_and_filter(
                topics=["AI"],
                max_results=5,
                deduplicate_results=True,
                apply_quality=True,
                apply_recency=True,
            )

            assert isinstance(results, list)
            assert len(results) <= 5
            # Results should be dictionaries
            assert all(isinstance(r, dict) for r in results)
            # Should have final_score calculated
            assert all("final_score" in r for r in results)


# ============================================================================
# Integration Tests (require API key)
# ============================================================================

@pytest.mark.integration
class TestTavilySearchServiceIntegration:
    """Integration tests requiring actual Tavily API key."""

    @pytest.fixture
    def tavily_service(self):
        """Get configured Tavily service."""
        from app.platforms.newsletter.services.tavily import TavilySearchService

        service = TavilySearchService()
        if not service.is_configured():
            pytest.skip("NEWSLETTER_TAVILY_API_KEY not configured")
        return service

    @pytest.mark.asyncio
    async def test_real_search_topic(self, tavily_service):
        """Test real API search for a topic."""
        results = await tavily_service.search_topic(
            "artificial intelligence",
            max_results=3,
            search_depth="basic",
        )

        assert len(results) > 0
        assert all(r.title for r in results)
        assert all(r.url for r in results)

    @pytest.mark.asyncio
    async def test_real_search_and_filter(self, tavily_service):
        """Test real API with full filter pipeline."""
        results = await tavily_service.search_and_filter(
            topics=["technology"],
            max_results=5,
        )

        assert len(results) > 0
        assert len(results) <= 5
        # Should be sorted by score (descending)
        scores = [r["final_score"] for r in results]
        assert scores == sorted(scores, reverse=True)
