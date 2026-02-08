"""
Tests for MongoDB Checkpointer.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.platforms.newsletter.orchestrator.mongodb_saver import (
    MongoDBSaver,
    get_mongodb_saver,
    CHECKPOINTS_COLLECTION,
    WRITES_COLLECTION,
)


class TestMongoDBSaverImports:
    """Tests for mongodb_saver module imports."""

    def test_mongodb_saver_import(self):
        """Can import MongoDBSaver."""
        assert MongoDBSaver is not None

    def test_get_mongodb_saver_import(self):
        """Can import get_mongodb_saver."""
        assert get_mongodb_saver is not None

    def test_collection_names_defined(self):
        """Collection names are defined."""
        assert CHECKPOINTS_COLLECTION == "langgraph_checkpoints"
        assert WRITES_COLLECTION == "langgraph_writes"


class TestMongoDBSaverInstantiation:
    """Tests for MongoDBSaver instantiation."""

    def test_instantiate_without_args(self):
        """Can instantiate MongoDBSaver without arguments."""
        saver = MongoDBSaver()
        assert saver is not None

    def test_instantiate_with_sync_db(self):
        """Can instantiate with sync database."""
        mock_db = MagicMock()
        saver = MongoDBSaver(db=mock_db)
        assert saver._db == mock_db

    def test_instantiate_with_async_db(self):
        """Can instantiate with async database."""
        mock_db = MagicMock()
        saver = MongoDBSaver(async_db=mock_db)
        assert saver._async_db == mock_db

    def test_has_serde(self):
        """MongoDBSaver has serializer."""
        saver = MongoDBSaver()
        assert saver.serde is not None


class TestMongoDBSaverHelpers:
    """Tests for MongoDBSaver helper methods."""

    def test_get_thread_id(self):
        """_get_thread_id extracts thread_id from config."""
        saver = MongoDBSaver()
        config = {"configurable": {"thread_id": "test-thread-123"}}
        result = saver._get_thread_id(config)
        assert result == "test-thread-123"

    def test_get_thread_id_missing(self):
        """_get_thread_id returns empty string when missing."""
        saver = MongoDBSaver()
        config = {}
        result = saver._get_thread_id(config)
        assert result == ""

    def test_get_checkpoint_ns(self):
        """_get_checkpoint_ns extracts checkpoint_ns from config."""
        saver = MongoDBSaver()
        config = {"configurable": {"checkpoint_ns": "test-ns"}}
        result = saver._get_checkpoint_ns(config)
        assert result == "test-ns"

    def test_get_checkpoint_id(self):
        """_get_checkpoint_id extracts checkpoint_id from config."""
        saver = MongoDBSaver()
        config = {"configurable": {"checkpoint_id": "ckpt-123"}}
        result = saver._get_checkpoint_id(config)
        assert result == "ckpt-123"

    def test_get_checkpoint_id_missing(self):
        """_get_checkpoint_id returns None when missing."""
        saver = MongoDBSaver()
        config = {}
        result = saver._get_checkpoint_id(config)
        assert result is None


class TestMongoDBSaverDbProperty:
    """Tests for MongoDBSaver db property."""

    def test_db_property_creates_sync_client(self):
        """db property creates sync PyMongo client when needed."""
        with patch(
            "app.platforms.newsletter.orchestrator.mongodb_saver.MongoClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_client_class.return_value = mock_client

            saver = MongoDBSaver()
            db = saver.db

            assert db is not None
            mock_client_class.assert_called_once()

    def test_db_property_caches_connection(self):
        """db property caches the database connection."""
        mock_db = MagicMock()
        saver = MongoDBSaver(db=mock_db)

        db1 = saver.db
        db2 = saver.db

        assert db1 is db2


class TestMongoDBSaverAsyncDbProperty:
    """Tests for MongoDBSaver async_db property."""

    def test_async_db_property_uses_get_database(self):
        """async_db property uses get_database function."""
        mock_async_db = MagicMock()
        with patch(
            "app.platforms.newsletter.orchestrator.mongodb_saver.get_database",
            return_value=mock_async_db,
        ):
            saver = MongoDBSaver()
            db = saver.async_db

            assert db == mock_async_db

    def test_async_db_property_caches_connection(self):
        """async_db property caches the database connection."""
        mock_async_db = MagicMock()
        saver = MongoDBSaver(async_db=mock_async_db)

        db1 = saver.async_db
        db2 = saver.async_db

        assert db1 is db2


class TestGetMongoDBSaver:
    """Tests for get_mongodb_saver singleton."""

    def test_get_mongodb_saver_returns_instance(self):
        """get_mongodb_saver returns MongoDBSaver instance."""
        # Reset singleton
        import app.platforms.newsletter.orchestrator.mongodb_saver as module
        module._saver = None

        saver = get_mongodb_saver()
        assert isinstance(saver, MongoDBSaver)

    def test_get_mongodb_saver_returns_same_instance(self):
        """get_mongodb_saver returns same instance on repeated calls."""
        # Reset singleton
        import app.platforms.newsletter.orchestrator.mongodb_saver as module
        module._saver = None

        saver1 = get_mongodb_saver()
        saver2 = get_mongodb_saver()

        assert saver1 is saver2


class TestMongoDBSaverGetTuple:
    """Tests for MongoDBSaver.get_tuple method."""

    def test_get_tuple_returns_none_when_not_found(self):
        """get_tuple returns None when checkpoint not found."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)

        saver = MongoDBSaver(db=mock_db)
        config = {"configurable": {"thread_id": "test-thread"}}

        result = saver.get_tuple(config)
        assert result is None


class TestMongoDBSaverDeleteThread:
    """Tests for MongoDBSaver delete_thread method."""

    def test_delete_thread_deletes_from_collections(self):
        """delete_thread removes checkpoints and writes."""
        mock_db = MagicMock()
        mock_checkpoints = MagicMock()
        mock_writes = MagicMock()

        mock_db.__getitem__ = lambda self, key: (
            mock_checkpoints if key == CHECKPOINTS_COLLECTION else mock_writes
        )

        saver = MongoDBSaver(db=mock_db)
        saver.delete_thread("thread-123")

        mock_checkpoints.delete_many.assert_called_once_with({"thread_id": "thread-123"})
        mock_writes.delete_many.assert_called_once_with({"thread_id": "thread-123"})


class TestMongoDBSaverAsyncDeleteThread:
    """Tests for MongoDBSaver async delete_thread method."""

    @pytest.mark.asyncio
    async def test_adelete_thread_deletes_from_collections(self):
        """adelete_thread removes checkpoints and writes asynchronously."""
        mock_async_db = MagicMock()
        mock_checkpoints = MagicMock()
        mock_writes = MagicMock()

        mock_checkpoints.delete_many = AsyncMock()
        mock_writes.delete_many = AsyncMock()

        mock_async_db.__getitem__ = lambda self, key: (
            mock_checkpoints if key == CHECKPOINTS_COLLECTION else mock_writes
        )

        saver = MongoDBSaver(async_db=mock_async_db)
        await saver.adelete_thread("thread-123")

        mock_checkpoints.delete_many.assert_called_once_with({"thread_id": "thread-123"})
        mock_writes.delete_many.assert_called_once_with({"thread_id": "thread-123"})


class TestMongoDBSaverEnsureIndexes:
    """Tests for MongoDBSaver index creation."""

    def test_ensure_indexes_creates_indexes(self):
        """_ensure_indexes creates necessary indexes."""
        mock_db = MagicMock()
        mock_checkpoints = MagicMock()
        mock_writes = MagicMock()

        mock_db.__getitem__ = lambda self, key: (
            mock_checkpoints if key == CHECKPOINTS_COLLECTION else mock_writes
        )

        saver = MongoDBSaver()
        saver._ensure_indexes(mock_db)

        # Verify indexes were created
        assert mock_checkpoints.create_index.called
        assert mock_writes.create_index.called
