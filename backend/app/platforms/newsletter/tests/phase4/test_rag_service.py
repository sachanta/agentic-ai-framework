"""
Tests for the Newsletter RAG Service.

Unit tests use mocks for Weaviate and embeddings.
Integration tests require running Weaviate and Ollama instances.
"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from uuid import uuid4

from app.platforms.newsletter.services.rag import (
    NewsletterRAGService,
    get_rag_service,
    COLLECTION_NAME,
)


class TestNewsletterRAGServiceInit:
    """Tests for RAG service initialization."""

    def test_default_initialization(self):
        """Test service initializes with default values."""
        from app.common.providers.embeddings import EmbeddingsProviderType

        service = NewsletterRAGService()
        assert service._embeddings_provider == EmbeddingsProviderType.OLLAMA
        assert service._embeddings_model == "nomic-embed-text"
        assert service._embeddings is None
        assert service._collection_initialized is False

    def test_custom_initialization(self):
        """Test service initializes with custom values."""
        from app.common.providers.embeddings import EmbeddingsProviderType

        service = NewsletterRAGService(
            embeddings_provider=EmbeddingsProviderType.OPENAI,
            embeddings_model="text-embedding-3-small",
        )
        assert service._embeddings_provider == EmbeddingsProviderType.OPENAI
        assert service._embeddings_model == "text-embedding-3-small"

    def test_singleton_pattern(self):
        """Test that get_rag_service returns singleton."""
        # Clear the singleton first
        import app.platforms.newsletter.services.rag as rag_module
        rag_module._rag_service = None

        service1 = get_rag_service()
        service2 = get_rag_service()
        assert service1 is service2


class TestRAGServiceAvailability:
    """Tests for availability checking."""

    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    def test_is_available_true(self, mock_available):
        """Test availability check when Weaviate is available."""
        mock_available.return_value = True
        service = NewsletterRAGService()
        assert service.is_available() is True

    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    def test_is_available_false(self, mock_available):
        """Test availability check when Weaviate is not available."""
        mock_available.return_value = False
        service = NewsletterRAGService()
        assert service.is_available() is False


class TestEnsureCollection:
    """Tests for collection creation/verification."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_ensure_collection_unavailable(self, mock_available):
        """Test ensure_collection when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()
        result = await service.ensure_collection()
        assert result is False

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_ensure_collection_already_exists(self, mock_available, mock_get_client):
        """Test ensure_collection when collection already exists."""
        mock_available.return_value = True

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()
        result = await service.ensure_collection()

        assert result is True
        assert service._collection_initialized is True
        mock_client.collections.exists.assert_called_once_with(COLLECTION_NAME)

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_ensure_collection_already_initialized(self, mock_available):
        """Test ensure_collection when already initialized."""
        mock_available.return_value = True
        service = NewsletterRAGService()
        service._collection_initialized = True

        result = await service.ensure_collection()
        assert result is True

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_ensure_collection_creates_new(self, mock_available, mock_get_client):
        """Test ensure_collection creates collection when missing."""
        mock_available.return_value = True

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = False
        mock_client.collections.create = MagicMock()
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        with patch.dict("sys.modules", {"weaviate.classes.config": MagicMock()}):
            result = await service.ensure_collection()

        assert result is True
        assert service._collection_initialized is True
        mock_client.collections.create.assert_called_once()


class TestStoreNewsletter:
    """Tests for storing newsletters."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_store_unavailable(self, mock_available):
        """Test store when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()

        result = await service.store_newsletter(
            user_id="user123",
            newsletter_id="nl123",
            content="Test content",
        )
        assert result is None

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_store_newsletter_success(self, mock_available, mock_get_client):
        """Test successful newsletter storage."""
        mock_available.return_value = True

        # Mock client
        mock_collection = MagicMock()
        mock_collection.data.insert = MagicMock()

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        # Mock embeddings
        mock_embeddings = AsyncMock()
        mock_embeddings.embed_text = AsyncMock(return_value=[0.1] * 768)
        service._embeddings = mock_embeddings

        result = await service.store_newsletter(
            user_id="user123",
            newsletter_id="nl123",
            content="Test newsletter content about AI",
            title="AI Newsletter",
            topics=["AI", "technology"],
            tone="professional",
            engagement_score=0.85,
            metadata={"source": "test"},
        )

        assert result is not None
        mock_collection.data.insert.assert_called_once()

        # Verify the call arguments
        call_kwargs = mock_collection.data.insert.call_args.kwargs
        assert "uuid" in call_kwargs
        assert "properties" in call_kwargs
        assert "vector" in call_kwargs
        assert call_kwargs["properties"]["user_id"] == "user123"
        assert call_kwargs["properties"]["newsletter_id"] == "nl123"
        assert call_kwargs["properties"]["topics"] == ["AI", "technology"]

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_store_newsletter_with_defaults(self, mock_available, mock_get_client):
        """Test storing with default values."""
        mock_available.return_value = True

        mock_collection = MagicMock()
        mock_collection.data.insert = MagicMock()

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        mock_embeddings = AsyncMock()
        mock_embeddings.embed_text = AsyncMock(return_value=[0.1] * 768)
        service._embeddings = mock_embeddings

        result = await service.store_newsletter(
            user_id="user123",
            newsletter_id="nl123",
            content="Minimal content",
        )

        assert result is not None
        call_kwargs = mock_collection.data.insert.call_args.kwargs
        assert call_kwargs["properties"]["title"] == ""
        assert call_kwargs["properties"]["topics"] == []
        assert call_kwargs["properties"]["tone"] == "professional"
        assert call_kwargs["properties"]["engagement_score"] == 0.0


class TestSearchSimilar:
    """Tests for similarity search."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_search_unavailable(self, mock_available):
        """Test search when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()

        results = await service.search_similar("test query")
        assert results == []

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_search_similar_success(self, mock_available, mock_get_client):
        """Test successful similarity search."""
        mock_available.return_value = True

        # Create mock result objects
        mock_obj = MagicMock()
        mock_obj.uuid = uuid4()
        mock_obj.properties = {
            "newsletter_id": "nl123",
            "user_id": "user123",
            "title": "Test Newsletter",
            "content": "Test content",
            "topics": ["AI"],
            "tone": "professional",
            "engagement_score": 0.8,
            "metadata_json": "{}",
        }
        mock_obj.metadata = MagicMock()
        mock_obj.metadata.distance = 0.2
        mock_obj.metadata.certainty = None

        mock_results = MagicMock()
        mock_results.objects = [mock_obj]

        mock_collection = MagicMock()
        mock_collection.query.near_vector = MagicMock(return_value=mock_results)

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()
        service._collection_initialized = True

        mock_embeddings = AsyncMock()
        mock_embeddings.embed_text = AsyncMock(return_value=[0.1] * 768)
        service._embeddings = mock_embeddings

        results = await service.search_similar(
            query="AI technology",
            user_id="user123",
            limit=5,
        )

        assert len(results) == 1
        assert results[0]["newsletter_id"] == "nl123"
        assert results[0]["score"] == 0.8  # 1.0 - 0.2 distance

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_search_with_min_score_filter(self, mock_available, mock_get_client):
        """Test search filters by minimum score."""
        mock_available.return_value = True

        # Create mock result with low score
        mock_obj = MagicMock()
        mock_obj.uuid = uuid4()
        mock_obj.properties = {
            "newsletter_id": "nl123",
            "user_id": "user123",
            "title": "Test",
            "content": "Test",
            "topics": [],
            "tone": "professional",
            "engagement_score": 0.5,
            "metadata_json": "{}",
        }
        mock_obj.metadata = MagicMock()
        mock_obj.metadata.distance = 0.9  # Low relevance (0.1 score)
        mock_obj.metadata.certainty = None

        mock_results = MagicMock()
        mock_results.objects = [mock_obj]

        mock_collection = MagicMock()
        mock_collection.query.near_vector = MagicMock(return_value=mock_results)

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()
        service._collection_initialized = True

        mock_embeddings = AsyncMock()
        mock_embeddings.embed_text = AsyncMock(return_value=[0.1] * 768)
        service._embeddings = mock_embeddings

        # Should filter out low score results
        results = await service.search_similar(
            query="test",
            min_score=0.5,
        )

        assert len(results) == 0  # Filtered out


class TestRecommendations:
    """Tests for content recommendations."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_recommendations_unavailable(self, mock_available):
        """Test recommendations when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()

        results = await service.get_recommendations("user123")
        assert results == []

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_recommendations_by_newsletter(self, mock_available, mock_get_client):
        """Test recommendations based on specific newsletter."""
        mock_available.return_value = True

        # Source newsletter
        source_obj = MagicMock()
        source_obj.vector = {"default": [0.1] * 768}
        source_obj.properties = {"newsletter_id": "nl123"}

        source_results = MagicMock()
        source_results.objects = [source_obj]

        # Similar newsletters
        similar_obj = MagicMock()
        similar_obj.uuid = uuid4()
        similar_obj.properties = {
            "newsletter_id": "nl456",
            "title": "Similar Newsletter",
            "topics": ["AI"],
            "tone": "casual",
            "engagement_score": 0.9,
        }
        similar_obj.metadata = MagicMock()
        similar_obj.metadata.distance = 0.1
        similar_obj.metadata.certainty = None

        similar_results = MagicMock()
        similar_results.objects = [similar_obj]

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects = MagicMock(return_value=source_results)
        mock_collection.query.near_vector = MagicMock(return_value=similar_results)

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()
        service._collection_initialized = True

        results = await service.get_recommendations(
            user_id="user123",
            based_on_newsletter_id="nl123",
            limit=5,
        )

        assert len(results) == 1
        assert results[0]["newsletter_id"] == "nl456"


class TestUserPatterns:
    """Tests for user pattern analysis."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_patterns_unavailable(self, mock_available):
        """Test patterns when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()

        result = await service.get_user_patterns("user123")
        assert "error" in result

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_patterns_no_data(self, mock_available, mock_get_client):
        """Test patterns when user has no newsletters."""
        mock_available.return_value = True

        mock_results = MagicMock()
        mock_results.objects = []

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects = MagicMock(return_value=mock_results)

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()
        service._collection_initialized = True

        result = await service.get_user_patterns("user123")

        assert result["total_newsletters"] == 0
        assert result["avg_engagement"] == 0.0

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_patterns_with_data(self, mock_available, mock_get_client):
        """Test pattern analysis with user data."""
        mock_available.return_value = True

        # Create mock newsletters
        mock_objs = []
        for i, (topics, tone, score) in enumerate([
            (["AI", "tech"], "professional", 0.8),
            (["AI"], "casual", 0.6),
            (["finance", "tech"], "professional", 0.9),
        ]):
            obj = MagicMock()
            obj.properties = {
                "newsletter_id": f"nl{i}",
                "topics": topics,
                "tone": tone,
                "engagement_score": score,
            }
            mock_objs.append(obj)

        mock_results = MagicMock()
        mock_results.objects = mock_objs

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects = MagicMock(return_value=mock_results)

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()
        service._collection_initialized = True

        result = await service.get_user_patterns("user123")

        assert result["total_newsletters"] == 3
        assert "AI" in result["top_topics"]
        assert result["primary_tone"] == "professional"
        assert result["avg_engagement"] == pytest.approx(0.767, rel=0.01)


class TestUpdateEngagement:
    """Tests for engagement score updates."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_update_unavailable(self, mock_available):
        """Test update when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()

        result = await service.update_engagement("nl123", 0.9)
        assert result is False

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_update_success(self, mock_available, mock_get_client):
        """Test successful engagement update."""
        mock_available.return_value = True

        mock_obj = MagicMock()
        mock_obj.uuid = uuid4()

        mock_results = MagicMock()
        mock_results.objects = [mock_obj]

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects = MagicMock(return_value=mock_results)
        mock_collection.data.update = MagicMock()

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        result = await service.update_engagement("nl123", 0.95)

        assert result is True
        mock_collection.data.update.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_update_not_found(self, mock_available, mock_get_client):
        """Test update when newsletter not found."""
        mock_available.return_value = True

        mock_results = MagicMock()
        mock_results.objects = []

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects = MagicMock(return_value=mock_results)

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        result = await service.update_engagement("nonexistent", 0.9)

        assert result is False


class TestDeleteOperations:
    """Tests for delete operations."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_delete_newsletter_success(self, mock_available, mock_get_client):
        """Test successful newsletter deletion."""
        mock_available.return_value = True

        mock_obj = MagicMock()
        mock_obj.uuid = uuid4()

        mock_results = MagicMock()
        mock_results.objects = [mock_obj]

        mock_collection = MagicMock()
        mock_collection.query.fetch_objects = MagicMock(return_value=mock_results)
        mock_collection.data.delete_by_id = MagicMock()

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        result = await service.delete_newsletter("nl123")

        assert result is True
        mock_collection.data.delete_by_id.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_delete_user_data(self, mock_available, mock_get_client):
        """Test deleting all user data."""
        mock_available.return_value = True

        mock_result = MagicMock()
        mock_result.successful = 5

        mock_collection = MagicMock()
        mock_collection.data.delete_many = MagicMock(return_value=mock_result)

        mock_client = MagicMock()
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        count = await service.delete_user_data("user123")

        assert count == 5


class TestBuildFilters:
    """Tests for filter building."""

    def test_build_filters_none(self):
        """Test building with no filters."""
        service = NewsletterRAGService()
        filters = service._build_filters()
        assert filters is None

    @patch.dict("sys.modules", {"weaviate.classes.query": MagicMock()})
    def test_build_filters_user_only(self):
        """Test building with user filter only."""
        service = NewsletterRAGService()

        # This will use real Weaviate Filter class if available
        # In unit tests, we just verify the method doesn't crash
        try:
            filters = service._build_filters(user_id="user123")
            assert filters is not None
        except ImportError:
            # Weaviate not installed in test env
            pass


class TestParseMetadata:
    """Tests for metadata parsing."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON metadata."""
        service = NewsletterRAGService()
        result = service._parse_metadata('{"key": "value", "num": 42}')
        assert result == {"key": "value", "num": 42}

    def test_parse_empty_string(self):
        """Test parsing empty string."""
        service = NewsletterRAGService()
        result = service._parse_metadata("")
        assert result == {}

    def test_parse_none(self):
        """Test parsing None."""
        service = NewsletterRAGService()
        result = service._parse_metadata(None)
        assert result == {}

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON."""
        service = NewsletterRAGService()
        result = service._parse_metadata("not valid json")
        assert result == {}


class TestHealthCheck:
    """Tests for health check."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_health_check_unavailable(self, mock_available):
        """Test health check when Weaviate unavailable."""
        mock_available.return_value = False
        service = NewsletterRAGService()

        status = await service.health_check()

        assert status["available"] is False
        assert "error" in status

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.rag.get_weaviate_client")
    @patch("app.platforms.newsletter.services.rag.is_weaviate_available")
    async def test_health_check_success(self, mock_available, mock_get_client):
        """Test successful health check."""
        mock_available.return_value = True

        mock_aggregate = MagicMock()
        mock_aggregate.total_count = 42

        mock_collection = MagicMock()
        mock_collection.aggregate.over_all = MagicMock(return_value=mock_aggregate)

        mock_client = MagicMock()
        mock_client.collections.exists.return_value = True
        mock_client.collections.get.return_value = mock_collection
        mock_get_client.return_value = mock_client

        service = NewsletterRAGService()

        # Mock embeddings health check
        mock_embeddings = AsyncMock()
        mock_embeddings.health_check = AsyncMock(return_value=True)
        service._embeddings = mock_embeddings

        status = await service.health_check()

        assert status["available"] is True
        assert status["embeddings_healthy"] is True
        assert status["document_count"] == 42
        assert status["healthy"] is True


class TestCollectionName:
    """Tests for collection name constant."""

    def test_collection_name(self):
        """Test collection name is defined correctly."""
        assert COLLECTION_NAME == "NewsletterRAG"


# Integration tests - require running Weaviate and Ollama
@pytest.mark.integration
class TestRAGServiceIntegration:
    """Integration tests requiring live Weaviate and Ollama."""

    @pytest.fixture
    def rag_service(self):
        """Create fresh RAG service for each test."""
        return NewsletterRAGService()

    @pytest.mark.asyncio
    async def test_full_workflow(self, rag_service):
        """Test complete store -> search -> delete workflow."""
        # Skip if Weaviate not available
        if not rag_service.is_available():
            pytest.skip("Weaviate not available")

        try:
            # Ensure collection exists
            created = await rag_service.ensure_collection()
            assert created is True

            # Store a newsletter
            user_id = f"test_user_{uuid4().hex[:8]}"
            newsletter_id = f"test_nl_{uuid4().hex[:8]}"

            doc_uuid = await rag_service.store_newsletter(
                user_id=user_id,
                newsletter_id=newsletter_id,
                content="This is a test newsletter about artificial intelligence and machine learning technologies.",
                title="AI & ML Newsletter",
                topics=["AI", "machine learning"],
                tone="professional",
                engagement_score=0.75,
            )

            assert doc_uuid is not None

            # Wait for indexing
            import asyncio
            await asyncio.sleep(1)

            # Search for similar
            results = await rag_service.search_similar(
                query="artificial intelligence",
                user_id=user_id,
                limit=5,
            )

            assert len(results) >= 1
            assert any(r["newsletter_id"] == newsletter_id for r in results)

            # Get patterns
            patterns = await rag_service.get_user_patterns(user_id)
            assert patterns["total_newsletters"] >= 1
            assert "AI" in patterns.get("top_topics", [])

            # Cleanup
            deleted = await rag_service.delete_newsletter(newsletter_id)
            assert deleted is True

        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")

    @pytest.mark.asyncio
    async def test_embeddings_health(self, rag_service):
        """Test embeddings provider is healthy."""
        if not rag_service.is_available():
            pytest.skip("Weaviate not available")

        try:
            healthy = await rag_service.embeddings.health_check()
            assert healthy is True
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")
