"""
Tests for Research API endpoints (Phase 6A).

Tests the research router endpoints for topic search,
custom prompt search, and trending content.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.platforms.newsletter.routers.research import router


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1/platforms/newsletter")

client = TestClient(app)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_research_result():
    """Standard mock research result."""
    return {
        "success": True,
        "articles": [
            {
                "title": "AI Breakthrough in Healthcare",
                "url": "https://example.com/article1",
                "source": "TechCrunch",
                "content": "Article content about AI...",
                "summary": "AI is transforming healthcare diagnostics.",
                "key_takeaway": "AI can detect diseases earlier.",
                "published_date": None,
                "score": 0.85,
                "relevance_score": 0.9,
                "quality_score": 0.8,
                "recency_boost": 0.1,
            },
            {
                "title": "New Machine Learning Framework",
                "url": "https://example.com/article2",
                "source": "Reuters",
                "content": "Content about ML frameworks...",
                "summary": "A new framework simplifies ML development.",
                "key_takeaway": "10x faster model training.",
                "published_date": None,
                "score": 0.75,
                "relevance_score": 0.82,
                "quality_score": 0.7,
                "recency_boost": 0.05,
            },
        ],
        "metadata": {
            "topics": ["AI", "technology"],
            "total_found": 15,
            "after_filter": 2,
            "source": "tavily",
        },
    }


@pytest.fixture
def mock_empty_result():
    """Mock empty research result."""
    return {
        "success": True,
        "articles": [],
        "metadata": {
            "topics": ["obscure_topic"],
            "total_found": 0,
            "after_filter": 0,
            "source": "tavily",
            "message": "No results found",
        },
    }


@pytest.fixture
def mock_error_result():
    """Mock error research result."""
    return {
        "success": False,
        "articles": [],
        "error": "Tavily API rate limit exceeded",
    }


# ============================================================================
# POST /research Tests
# ============================================================================

class TestResearchTopics:
    """Tests for POST /research endpoint."""

    def test_research_topics_success(self, mock_research_result):
        """Test successful topic research."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={
                    "topics": ["AI", "technology"],
                    "max_results": 10,
                    "include_summaries": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["articles"]) == 2
            assert data["articles"][0]["title"] == "AI Breakthrough in Healthcare"
            assert data["metadata"]["topics"] == ["AI", "technology"]
            assert data["metadata"]["total_found"] == 15
            assert data["metadata"]["after_filter"] == 2

    def test_research_topics_empty_results(self, mock_empty_result):
        """Test research with no results."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_empty_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["obscure_topic"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["articles"]) == 0
            assert data["metadata"]["total_found"] == 0

    def test_research_topics_error(self, mock_error_result):
        """Test research with error."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_error_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["error"] == "Tavily API rate limit exceeded"

    def test_research_topics_validation_empty_topics(self):
        """Test validation rejects empty topics list."""
        response = client.post(
            "/api/v1/platforms/newsletter/research",
            json={"topics": []},
        )
        assert response.status_code == 422

    def test_research_topics_validation_max_results(self, mock_research_result):
        """Test max_results validation."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            # Valid range
            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"], "max_results": 50},
            )
            assert response.status_code == 200

            # Invalid: too high
            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"], "max_results": 100},
            )
            assert response.status_code == 422

            # Invalid: too low
            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"], "max_results": 0},
            )
            assert response.status_code == 422

    def test_research_topics_with_summaries_disabled(self, mock_research_result):
        """Test research without summaries."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={
                    "topics": ["AI"],
                    "include_summaries": False,
                },
            )

            assert response.status_code == 200
            # Verify include_summaries was passed correctly
            call_args = mock_agent.run.call_args[0][0]
            assert call_args["include_summaries"] is False


# ============================================================================
# POST /research/custom Tests
# ============================================================================

class TestResearchCustomPrompt:
    """Tests for POST /research/custom endpoint."""

    def test_custom_prompt_success(self, mock_research_result):
        """Test successful custom prompt research."""
        mock_research_result["metadata"]["topics"] = ["AI", "healthcare"]

        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research/custom",
                json={
                    "prompt": "Find the latest AI breakthroughs in healthcare",
                    "max_results": 10,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["articles"]) == 2
            # Check that custom_prompt was passed
            call_args = mock_agent.run.call_args[0][0]
            assert call_args["custom_prompt"] == "Find the latest AI breakthroughs in healthcare"

    def test_custom_prompt_observability_newsletter(self, mock_research_result):
        """Test custom prompt for observability newsletter."""
        mock_research_result["metadata"]["topics"] = ["observability", "OpenTelemetry"]

        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research/custom",
                json={
                    "prompt": "Generate content for an Observability newsletter focusing on OpenTelemetry",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Processed prompt" in data["metadata"]["message"]

    def test_custom_prompt_validation_empty(self):
        """Test validation rejects empty prompt."""
        response = client.post(
            "/api/v1/platforms/newsletter/research/custom",
            json={"prompt": ""},
        )
        assert response.status_code == 422

    def test_custom_prompt_validation_too_short(self):
        """Test validation rejects too short prompt."""
        response = client.post(
            "/api/v1/platforms/newsletter/research/custom",
            json={"prompt": "AI"},
        )
        assert response.status_code == 422


# ============================================================================
# GET /research/trending Tests
# ============================================================================

class TestResearchTrending:
    """Tests for GET /research/trending endpoint."""

    def test_trending_success(self):
        """Test successful trending content retrieval."""
        mock_trending = [
            {
                "title": "Breaking: New AI Model Released",
                "url": "https://example.com/trending1",
                "source": "TechNews",
                "content": "Content...",
                "score": 0.95,
                "relevance_score": 0.9,
                "quality_score": 0.85,
                "recency_boost": 0.2,
            },
        ]

        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.get_trending = AsyncMock(return_value=mock_trending)
            MockAgent.return_value = mock_agent

            response = client.get(
                "/api/v1/platforms/newsletter/research/trending",
                params={"topics": "AI,technology", "max_results": 5},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["articles"]) == 1
            assert data["metadata"]["topics"] == ["AI", "technology"]
            assert data["metadata"]["source"] == "tavily_trending"

    def test_trending_single_topic(self):
        """Test trending with single topic."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.get_trending = AsyncMock(return_value=[])
            MockAgent.return_value = mock_agent

            response = client.get(
                "/api/v1/platforms/newsletter/research/trending",
                params={"topics": "AI"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["topics"] == ["AI"]

    def test_trending_empty_topics(self):
        """Test trending with empty topics string."""
        response = client.get(
            "/api/v1/platforms/newsletter/research/trending",
            params={"topics": ""},
        )
        assert response.status_code == 400
        assert "At least one topic required" in response.json()["detail"]

    def test_trending_default_max_results(self):
        """Test trending uses default max_results."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.get_trending = AsyncMock(return_value=[])
            MockAgent.return_value = mock_agent

            response = client.get(
                "/api/v1/platforms/newsletter/research/trending",
                params={"topics": "AI"},
            )

            assert response.status_code == 200
            # Default is 10
            mock_agent.get_trending.assert_called_once_with(["AI"], 10)


# ============================================================================
# Response Schema Tests
# ============================================================================

class TestResponseSchemas:
    """Tests for response schema structure."""

    def test_article_response_structure(self, mock_research_result):
        """Test article response has all expected fields."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"]},
            )

            assert response.status_code == 200
            article = response.json()["articles"][0]

            # Check all expected fields
            assert "title" in article
            assert "url" in article
            assert "source" in article
            assert "content" in article
            assert "summary" in article
            assert "key_takeaway" in article
            assert "published_date" in article
            assert "score" in article
            assert "relevance_score" in article
            assert "quality_score" in article
            assert "recency_boost" in article

    def test_metadata_response_structure(self, mock_research_result):
        """Test metadata response has all expected fields."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=mock_research_result)
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"]},
            )

            assert response.status_code == 200
            metadata = response.json()["metadata"]

            assert "topics" in metadata
            assert "total_found" in metadata
            assert "after_filter" in metadata
            assert "source" in metadata
            assert "cached" in metadata


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling."""

    def test_agent_exception_returns_500(self):
        """Test that agent exceptions return 500."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(side_effect=Exception("Unexpected error"))
            MockAgent.return_value = mock_agent

            response = client.post(
                "/api/v1/platforms/newsletter/research",
                json={"topics": ["AI"]},
            )

            assert response.status_code == 500
            assert "Unexpected error" in response.json()["detail"]

    def test_trending_exception_returns_500(self):
        """Test that trending exceptions return 500."""
        with patch("app.platforms.newsletter.routers.research.ResearchAgent") as MockAgent:
            mock_agent = MagicMock()
            mock_agent.get_trending = AsyncMock(side_effect=Exception("API Error"))
            MockAgent.return_value = mock_agent

            response = client.get(
                "/api/v1/platforms/newsletter/research/trending",
                params={"topics": "AI"},
            )

            assert response.status_code == 500
            assert "API Error" in response.json()["detail"]
