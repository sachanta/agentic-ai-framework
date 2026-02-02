"""
Tests for the Newsletter Memory Service.

Unit tests use mocks for MongoDB.
Integration tests require a running MongoDB instance.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.platforms.newsletter.services.memory import (
    MemoryService,
    get_memory_service,
    CacheType,
    CACHE_COLLECTION,
)


class TestMemoryServiceInit:
    """Tests for Memory service initialization."""

    def test_default_initialization(self):
        """Test service initializes with default values."""
        service = MemoryService()
        assert service.default_ttl == 3600  # From config
        assert service._indexes_ensured is False

    def test_custom_ttl_initialization(self):
        """Test service initializes with custom TTL."""
        service = MemoryService(default_ttl=7200)
        assert service.default_ttl == 7200

    def test_singleton_pattern(self):
        """Test that get_memory_service returns singleton."""
        import app.platforms.newsletter.services.memory as memory_module
        memory_module._memory_service = None

        service1 = get_memory_service()
        service2 = get_memory_service()
        assert service1 is service2


class TestCacheType:
    """Tests for CacheType enum."""

    def test_cache_types_defined(self):
        """Test all cache types are defined."""
        assert CacheType.PREFERENCES.value == "preferences"
        assert CacheType.RESEARCH.value == "research"
        assert CacheType.ENGAGEMENT.value == "engagement"
        assert CacheType.SESSION.value == "session"
        assert CacheType.WORKFLOW.value == "workflow"
        assert CacheType.ANALYTICS.value == "analytics"


class TestMakeKey:
    """Tests for key generation."""

    def test_make_key(self):
        """Test composite key generation."""
        service = MemoryService()
        key = service._make_key("user123", CacheType.PREFERENCES, "current")
        assert key == "user123:preferences:current"

    def test_make_key_different_types(self):
        """Test keys are different for different types."""
        service = MemoryService()
        key1 = service._make_key("user123", CacheType.PREFERENCES, "key")
        key2 = service._make_key("user123", CacheType.RESEARCH, "key")
        assert key1 != key2


class TestSerializeDeserialize:
    """Tests for value serialization."""

    def test_serialize_dict(self):
        """Test serializing dictionary."""
        service = MemoryService()
        result = service._serialize_value({"key": "value", "num": 42})
        assert result == '{"key": "value", "num": 42}'

    def test_serialize_list(self):
        """Test serializing list."""
        service = MemoryService()
        result = service._serialize_value([1, 2, 3])
        assert result == '[1, 2, 3]'

    def test_serialize_string(self):
        """Test serializing string returns as-is."""
        service = MemoryService()
        result = service._serialize_value("test string")
        assert result == "test string"

    def test_deserialize_json(self):
        """Test deserializing JSON."""
        service = MemoryService()
        result = service._deserialize_value('{"key": "value"}')
        assert result == {"key": "value"}

    def test_deserialize_none(self):
        """Test deserializing None."""
        service = MemoryService()
        result = service._deserialize_value(None)
        assert result is None

    def test_deserialize_invalid_json(self):
        """Test deserializing invalid JSON returns string."""
        service = MemoryService()
        result = service._deserialize_value("not json")
        assert result == "not json"


class TestEnsureIndexes:
    """Tests for index creation."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_ensure_indexes_success(self, mock_get_db):
        """Test successful index creation."""
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.ensure_indexes()

        assert result is True
        assert service._indexes_ensured is True
        assert mock_collection.create_index.call_count == 3

    @pytest.mark.asyncio
    async def test_ensure_indexes_already_ensured(self):
        """Test skips if indexes already ensured."""
        service = MemoryService()
        service._indexes_ensured = True

        result = await service.ensure_indexes()
        assert result is True


class TestSetGet:
    """Tests for basic set/get operations."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_set_value(self, mock_get_db):
        """Test setting a value."""
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()
        mock_collection.update_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.set(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="current",
            value={"topics": ["AI"]},
            ttl=3600,
        )

        assert result is True
        mock_collection.update_one.assert_called_once()

        # Verify the document structure
        call_args = mock_collection.update_one.call_args
        filter_arg = call_args[0][0]
        update_arg = call_args[0][1]

        assert filter_arg == {"key": "user123:preferences:current"}
        assert "$set" in update_arg
        doc = update_arg["$set"]
        assert doc["user_id"] == "user123"
        assert doc["type"] == "preferences"
        assert doc["ttl_seconds"] == 3600

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_get_value_found(self, mock_get_db):
        """Test getting an existing value."""
        now = datetime.now(timezone.utc)
        mock_doc = {
            "key": "user123:preferences:current",
            "value": '{"topics": ["AI"]}',
            "expires_at": now + timedelta(hours=1),
        }

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_doc)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.get(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="current",
        )

        assert result == {"topics": ["AI"]}

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_get_value_not_found(self, mock_get_db):
        """Test getting a non-existent value."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.get(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="nonexistent",
        )

        assert result is None

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_get_value_expired(self, mock_get_db):
        """Test getting an expired value returns None."""
        now = datetime.now(timezone.utc)
        mock_doc = {
            "key": "user123:preferences:current",
            "value": '{"topics": ["AI"]}',
            "expires_at": now - timedelta(hours=1),  # Expired
        }

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_doc)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.get(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="current",
        )

        assert result is None


class TestDelete:
    """Tests for delete operations."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_delete_single(self, mock_get_db):
        """Test deleting a single entry."""
        mock_collection = AsyncMock()
        mock_collection.delete_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.delete(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="current",
        )

        assert result is True
        mock_collection.delete_one.assert_called_once_with(
            {"key": "user123:preferences:current"}
        )

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_delete_by_type(self, mock_get_db):
        """Test deleting all entries of a type."""
        mock_result = MagicMock()
        mock_result.deleted_count = 5

        mock_collection = AsyncMock()
        mock_collection.delete_many = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        count = await service.delete_by_type(
            user_id="user123",
            cache_type=CacheType.RESEARCH,
        )

        assert count == 5
        mock_collection.delete_many.assert_called_once_with({
            "user_id": "user123",
            "type": "research",
        })

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_delete_all_user_data(self, mock_get_db):
        """Test deleting all user data."""
        mock_result = MagicMock()
        mock_result.deleted_count = 15

        mock_collection = AsyncMock()
        mock_collection.delete_many = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        count = await service.delete_all_user_data("user123")

        assert count == 15


class TestConvenienceMethods:
    """Tests for convenience methods."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_set_preferences(self, mock_get_db):
        """Test setting preferences."""
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()
        mock_collection.update_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.set_preferences(
            user_id="user123",
            preferences={"topics": ["AI"], "tone": "casual"},
        )

        assert result is True

        # Check TTL is 24 hours for preferences
        call_args = mock_collection.update_one.call_args
        doc = call_args[0][1]["$set"]
        assert doc["ttl_seconds"] == 86400

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_get_preferences(self, mock_get_db):
        """Test getting preferences."""
        now = datetime.now(timezone.utc)
        mock_doc = {
            "key": "user123:preferences:current",
            "value": '{"topics": ["AI"]}',
            "expires_at": now + timedelta(hours=1),
        }

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_doc)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.get_preferences("user123")

        assert result == {"topics": ["AI"]}

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_set_research_results(self, mock_get_db):
        """Test caching research results."""
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()
        mock_collection.update_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.set_research_results(
            user_id="user123",
            topics_hash="abc123",
            results=[{"title": "Article 1"}],
        )

        assert result is True

        # Check TTL is 30 minutes for research
        call_args = mock_collection.update_one.call_args
        doc = call_args[0][1]["$set"]
        assert doc["ttl_seconds"] == 1800

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_update_engagement(self, mock_get_db):
        """Test updating engagement metrics."""
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)  # No existing engagement
        mock_collection.update_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.update_engagement(
            user_id="user123",
            newsletter_id="nl123",
            event_type="open",
            event_data={"source": "email"},
        )

        assert result is True

        # Check the engagement structure
        call_args = mock_collection.update_one.call_args
        doc = call_args[0][1]["$set"]
        value = service._deserialize_value(doc["value"])
        assert "events" in value
        assert len(value["events"]) == 1
        assert value["events"][0]["type"] == "open"
        assert value["summary"]["open"] == 1

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_set_workflow_state(self, mock_get_db):
        """Test storing workflow state."""
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock()
        mock_collection.update_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.set_workflow_state(
            user_id="user123",
            workflow_id="wf123",
            state={"step": 2, "checkpoint": "content_review"},
        )

        assert result is True

        # Check TTL is 2 hours for workflow
        call_args = mock_collection.update_one.call_args
        doc = call_args[0][1]["$set"]
        assert doc["ttl_seconds"] == 7200


class TestTouch:
    """Tests for touch (TTL extension) operation."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_touch_extends_ttl(self, mock_get_db):
        """Test that touch extends TTL."""
        mock_doc = {
            "key": "user123:preferences:current",
            "ttl_seconds": 3600,
        }

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=mock_doc)
        mock_collection.update_one = AsyncMock()

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.touch(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="current",
        )

        assert result is True
        mock_collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_touch_not_found(self, mock_get_db):
        """Test touch returns False when entry not found."""
        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        result = await service.touch(
            user_id="user123",
            cache_type=CacheType.PREFERENCES,
            key="nonexistent",
        )

        assert result is False


class TestGetStats:
    """Tests for cache statistics."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_get_stats(self, mock_get_db):
        """Test getting cache statistics."""
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = lambda self: self
        mock_cursor.__anext__ = AsyncMock(
            side_effect=[
                {"_id": "preferences", "count": 10},
                {"_id": "research", "count": 5},
                StopAsyncIteration,
            ]
        )

        mock_collection = AsyncMock()
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        stats = await service.get_stats(user_id="user123")

        assert stats["total_entries"] == 15
        assert stats["by_type"]["preferences"] == 10
        assert stats["by_type"]["research"] == 5
        assert stats["user_id"] == "user123"


class TestCleanupExpired:
    """Tests for manual cleanup."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_cleanup_expired(self, mock_get_db):
        """Test cleaning up expired entries."""
        mock_result = MagicMock()
        mock_result.deleted_count = 10

        mock_collection = AsyncMock()
        mock_collection.delete_many = AsyncMock(return_value=mock_result)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        count = await service.cleanup_expired()

        assert count == 10


class TestHealthCheck:
    """Tests for health check."""

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_health_check_success(self, mock_get_db):
        """Test successful health check."""
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__ = lambda self: self
        mock_cursor.__anext__ = AsyncMock(side_effect=[StopAsyncIteration])

        mock_collection = AsyncMock()
        mock_collection.find_one = AsyncMock(return_value=None)
        mock_collection.aggregate = MagicMock(return_value=mock_cursor)

        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_get_db.return_value = mock_db

        service = MemoryService()
        status = await service.health_check()

        assert status["healthy"] is True
        assert status["collection"] == CACHE_COLLECTION

    @pytest.mark.asyncio
    @patch("app.platforms.newsletter.services.memory.get_database")
    async def test_health_check_failure(self, mock_get_db):
        """Test health check when MongoDB fails."""
        mock_get_db.side_effect = RuntimeError("DB not connected")

        service = MemoryService()
        status = await service.health_check()

        assert status["healthy"] is False
        assert "error" in status


class TestCollectionName:
    """Tests for collection name constant."""

    def test_collection_name(self):
        """Test collection name is defined correctly."""
        assert CACHE_COLLECTION == "newsletter_cache"


# Integration tests - require running MongoDB
@pytest.mark.integration
class TestMemoryServiceIntegration:
    """Integration tests requiring live MongoDB."""

    @pytest.fixture
    def memory_service(self):
        """Create fresh memory service for each test."""
        return MemoryService()

    @pytest.mark.asyncio
    async def test_full_workflow(self, memory_service):
        """Test complete set -> get -> delete workflow."""
        from app.db.mongodb import get_database

        try:
            # Try to access database
            db = get_database()
        except RuntimeError:
            pytest.skip("MongoDB not available")

        user_id = f"test_user_{uuid4().hex[:8]}"
        test_key = f"test_key_{uuid4().hex[:8]}"

        try:
            # Ensure indexes
            await memory_service.ensure_indexes()

            # Set a value
            set_result = await memory_service.set(
                user_id=user_id,
                cache_type=CacheType.PREFERENCES,
                key=test_key,
                value={"test": "data", "number": 42},
                ttl=60,
            )
            assert set_result is True

            # Get the value
            value = await memory_service.get(
                user_id=user_id,
                cache_type=CacheType.PREFERENCES,
                key=test_key,
            )
            assert value == {"test": "data", "number": 42}

            # Delete the value
            delete_result = await memory_service.delete(
                user_id=user_id,
                cache_type=CacheType.PREFERENCES,
                key=test_key,
            )
            assert delete_result is True

            # Verify deleted
            value = await memory_service.get(
                user_id=user_id,
                cache_type=CacheType.PREFERENCES,
                key=test_key,
            )
            assert value is None

        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")

    @pytest.mark.asyncio
    async def test_health_check(self, memory_service):
        """Test health check with live MongoDB."""
        from app.db.mongodb import get_database

        try:
            db = get_database()
        except RuntimeError:
            pytest.skip("MongoDB not available")

        status = await memory_service.health_check()
        assert status["healthy"] is True
