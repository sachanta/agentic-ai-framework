"""
Tests for Preference API endpoints.

Tests the preference router endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_preference_agent():
    """Create mock PreferenceAgent."""
    with patch(
        "app.platforms.newsletter.routers.preference.PreferenceAgent"
    ) as MockAgent:
        mock_instance = MagicMock()
        mock_instance.run = AsyncMock()
        MockAgent.return_value = mock_instance
        yield mock_instance


class TestGetPreferences:
    """Test GET /preferences/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_preferences_success(self, mock_preference_agent):
        """Test successful preferences retrieval."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "preferences": {
                "user_id": "test_user",
                "topics": ["AI", "Technology"],
                "tone": "professional",
                "frequency": "weekly",
                "max_articles": 10,
                "preferred_sources": [],
                "excluded_sources": [],
                "include_summaries": True,
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/test_user"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert data["topics"] == ["AI", "Technology"]
        assert data["tone"] == "professional"

    @pytest.mark.asyncio
    async def test_get_preferences_returns_defaults(self, mock_preference_agent):
        """Test defaults returned for new user."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "preferences": {
                "user_id": "new_user",
                "topics": [],
                "tone": "professional",
                "frequency": "weekly",
                "max_articles": 10,
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/new_user"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["tone"] == "professional"
        assert data["frequency"] == "weekly"


class TestUpdatePreferences:
    """Test PATCH /preferences/{user_id} endpoint."""

    @pytest.mark.asyncio
    async def test_update_preferences_success(self, mock_preference_agent):
        """Test successful preferences update."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "preferences": {
                "user_id": "test_user",
                "topics": ["AI", "ML"],
                "tone": "casual",
                "frequency": "weekly",
                "max_articles": 15,
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                "/api/v1/platforms/newsletter/preferences/test_user",
                json={
                    "topics": ["AI", "ML"],
                    "tone": "casual",
                    "max_articles": 15,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["topics"] == ["AI", "ML"]
        assert data["tone"] == "casual"
        assert data["max_articles"] == 15

    @pytest.mark.asyncio
    async def test_update_partial_preferences(self, mock_preference_agent):
        """Test partial update only changes specified fields."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "preferences": {
                "user_id": "test_user",
                "topics": ["Technology"],
                "tone": "professional",  # unchanged
                "frequency": "weekly",
                "max_articles": 10,
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.patch(
                "/api/v1/platforms/newsletter/preferences/test_user",
                json={"topics": ["Technology"]},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["topics"] == ["Technology"]
        assert data["tone"] == "professional"  # Should be preserved


class TestRecordEngagement:
    """Test POST /preferences/{user_id}/engagement endpoint."""

    @pytest.mark.asyncio
    async def test_record_engagement_success(self, mock_preference_agent):
        """Test successful engagement recording."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "message": "Engagement recorded",
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/platforms/newsletter/preferences/test_user/engagement",
                json={
                    "newsletter_id": "newsletter_123",
                    "opened": True,
                    "clicked_links": ["https://example.com/article1"],
                    "read_time_seconds": 120,
                    "rating": 4,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_record_engagement_minimal(self, mock_preference_agent):
        """Test engagement with minimal data."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "message": "Engagement recorded",
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/v1/platforms/newsletter/preferences/test_user/engagement",
                json={
                    "newsletter_id": "newsletter_123",
                    "opened": False,
                },
            )

        assert response.status_code == 200


class TestAnalyzePreferences:
    """Test GET /preferences/{user_id}/analysis endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_preferences_success(self, mock_preference_agent):
        """Test successful analysis."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "analysis": {
                "user_id": "test_user",
                "insights": [
                    {
                        "category": "topics",
                        "message": "User prefers AI content",
                        "confidence": 0.85,
                    }
                ],
                "engagement_summary": {
                    "avg_read_time": 90,
                    "open_rate": 0.75,
                },
            },
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/test_user/analysis"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert len(data["insights"]) >= 1
        assert data["insights"][0]["category"] == "topics"


class TestGetRecommendations:
    """Test GET /preferences/{user_id}/recommendations endpoint."""

    @pytest.mark.asyncio
    async def test_get_recommendations_success(self, mock_preference_agent):
        """Test successful recommendations."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "recommendations": [
                {
                    "field": "topics",
                    "current_value": ["AI"],
                    "recommended_value": ["AI", "ML"],
                    "reason": "Based on clicked articles",
                    "confidence": 0.8,
                }
            ],
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/test_user/recommendations"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert len(data["recommendations"]) >= 1

    @pytest.mark.asyncio
    async def test_get_recommendations_empty(self, mock_preference_agent):
        """Test when no recommendations available."""
        mock_preference_agent.run.return_value = {
            "success": True,
            "recommendations": [],
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/test_user/recommendations"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["recommendations"] == []


class TestErrorHandling:
    """Test error handling in preference endpoints."""

    @pytest.mark.asyncio
    async def test_agent_error_returns_500(self, mock_preference_agent):
        """Test that agent errors return 500."""
        mock_preference_agent.run.return_value = {
            "success": False,
            "error": "Database connection failed",
        }

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/test_user"
            )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_exception_returns_500(self, mock_preference_agent):
        """Test that exceptions return 500."""
        mock_preference_agent.run.side_effect = Exception("Unexpected error")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/api/v1/platforms/newsletter/preferences/test_user"
            )

        assert response.status_code == 500
