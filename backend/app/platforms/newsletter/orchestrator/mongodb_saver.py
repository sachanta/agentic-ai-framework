"""
MongoDB Checkpointer for LangGraph.

Persists workflow state to MongoDB for durable HITL workflows.
"""
import base64
import logging
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterator, Sequence

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database

from app.config import settings
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

# Collection names
CHECKPOINTS_COLLECTION = "langgraph_checkpoints"
WRITES_COLLECTION = "langgraph_writes"


class MongoDBSaver(BaseCheckpointSaver):
    """
    MongoDB-based checkpoint saver for LangGraph.

    Stores checkpoints and pending writes in MongoDB collections,
    enabling persistent HITL workflows that survive restarts.
    """

    def __init__(
        self,
        db: Database | None = None,
        async_db: AsyncIOMotorDatabase | None = None,
    ):
        """
        Initialize MongoDB saver.

        Args:
            db: Synchronous MongoDB database (optional)
            async_db: Async MongoDB database (optional)
        """
        super().__init__(serde=JsonPlusSerializer())
        self._db = db
        self._async_db = async_db
        self._sync_client: MongoClient | None = None

    def _ensure_indexes(self, collection_db: Database) -> None:
        """Create indexes for efficient queries."""
        checkpoints = collection_db[CHECKPOINTS_COLLECTION]
        checkpoints.create_index(
            [("thread_id", 1), ("checkpoint_ns", 1), ("checkpoint_id", 1)],
            unique=True,
        )
        checkpoints.create_index([("thread_id", 1), ("checkpoint_ns", 1)])

        writes = collection_db[WRITES_COLLECTION]
        writes.create_index(
            [("thread_id", 1), ("checkpoint_ns", 1), ("checkpoint_id", 1), ("task_id", 1)],
        )

    @property
    def db(self) -> Database:
        """Get sync database, creating if needed."""
        if self._db is None:
            # Create sync PyMongo client for sync operations
            self._sync_client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            self._db = self._sync_client[settings.MONGODB_DATABASE]
            self._ensure_indexes(self._db)
        return self._db

    @property
    def async_db(self) -> AsyncIOMotorDatabase:
        """Get async database, creating if needed."""
        if self._async_db is None:
            # Use the global async database from app.db.mongodb
            self._async_db = get_database()
        return self._async_db

    def _get_thread_id(self, config: RunnableConfig) -> str:
        """Extract thread_id from config."""
        return config.get("configurable", {}).get("thread_id", "")

    def _get_checkpoint_ns(self, config: RunnableConfig) -> str:
        """Extract checkpoint namespace from config."""
        return config.get("configurable", {}).get("checkpoint_ns", "")

    def _get_checkpoint_id(self, config: RunnableConfig) -> str | None:
        """Extract checkpoint_id from config."""
        return config.get("configurable", {}).get("checkpoint_id")

    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> dict:
        """Serialize checkpoint for MongoDB storage."""
        type_str, data_bytes = self.serde.dumps_typed(checkpoint["channel_values"])
        return {
            "v": checkpoint["v"],
            "id": checkpoint["id"],
            "ts": checkpoint["ts"],
            "channel_values": base64.b64encode(data_bytes).decode("ascii"),
            "channel_values_type": type_str,
            "channel_versions": dict(checkpoint["channel_versions"]),
            "versions_seen": {
                k: dict(v) for k, v in checkpoint["versions_seen"].items()
            },
            "updated_channels": checkpoint.get("updated_channels"),
        }

    def _deserialize_checkpoint(self, data: dict) -> Checkpoint:
        """Deserialize checkpoint from MongoDB storage."""
        type_str = data.get("channel_values_type", self.serde.dumps_typed({})[0])
        channel_bytes = base64.b64decode(data["channel_values"])
        return Checkpoint(
            v=data["v"],
            id=data["id"],
            ts=data["ts"],
            channel_values=self.serde.loads_typed((type_str, channel_bytes)),
            channel_versions=data["channel_versions"],
            versions_seen={
                k: v for k, v in data["versions_seen"].items()
            },
            updated_channels=data.get("updated_channels"),
        )

    def _serialize_metadata(self, metadata: CheckpointMetadata) -> dict:
        """Serialize metadata for MongoDB storage."""
        return dict(metadata) if metadata else {}

    def _deserialize_metadata(self, data: dict) -> CheckpointMetadata:
        """Deserialize metadata from MongoDB storage."""
        return CheckpointMetadata(**data) if data else CheckpointMetadata()

    # Synchronous methods

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get checkpoint tuple by config."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        checkpoint_id = self._get_checkpoint_id(config)

        query = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
        }
        if checkpoint_id:
            query["checkpoint_id"] = checkpoint_id

        doc = self.db[CHECKPOINTS_COLLECTION].find_one(
            query,
            sort=[("checkpoint_id", -1)],
        )

        if not doc:
            return None

        # Get pending writes
        writes_docs = list(self.db[WRITES_COLLECTION].find({
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": doc["checkpoint_id"],
        }))

        pending_writes = [
            (
                w["task_id"],
                w["channel"],
                self.serde.loads_typed((
                    w.get("value_type", self.serde.dumps_typed({})[0]),
                    base64.b64decode(w["value"]),
                )),
            )
            for w in writes_docs
        ] if writes_docs else None

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": doc["checkpoint_id"],
                }
            },
            checkpoint=self._deserialize_checkpoint(doc["checkpoint"]),
            metadata=self._deserialize_metadata(doc.get("metadata", {})),
            parent_config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": doc["parent_checkpoint_id"],
                }
            } if doc.get("parent_checkpoint_id") else None,
            pending_writes=pending_writes,
        )

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List checkpoints matching criteria."""
        query: dict[str, Any] = {}

        if config:
            thread_id = self._get_thread_id(config)
            checkpoint_ns = self._get_checkpoint_ns(config)
            if thread_id:
                query["thread_id"] = thread_id
            if checkpoint_ns:
                query["checkpoint_ns"] = checkpoint_ns

        if filter:
            for key, value in filter.items():
                query[f"metadata.{key}"] = value

        if before:
            before_id = self._get_checkpoint_id(before)
            if before_id:
                query["checkpoint_id"] = {"$lt": before_id}

        cursor = self.db[CHECKPOINTS_COLLECTION].find(query).sort("checkpoint_id", -1)
        if limit:
            cursor = cursor.limit(limit)

        for doc in cursor:
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": doc["thread_id"],
                        "checkpoint_ns": doc["checkpoint_ns"],
                        "checkpoint_id": doc["checkpoint_id"],
                    }
                },
                checkpoint=self._deserialize_checkpoint(doc["checkpoint"]),
                metadata=self._deserialize_metadata(doc.get("metadata", {})),
                parent_config={
                    "configurable": {
                        "thread_id": doc["thread_id"],
                        "checkpoint_ns": doc["checkpoint_ns"],
                        "checkpoint_id": doc["parent_checkpoint_id"],
                    }
                } if doc.get("parent_checkpoint_id") else None,
                pending_writes=None,
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        parent_checkpoint_id = self._get_checkpoint_id(config)

        doc = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint["id"],
            "parent_checkpoint_id": parent_checkpoint_id,
            "checkpoint": self._serialize_checkpoint(checkpoint),
            "metadata": self._serialize_metadata(metadata),
            "created_at": datetime.now(timezone.utc),
        }

        self.db[CHECKPOINTS_COLLECTION].replace_one(
            {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            },
            doc,
            upsert=True,
        )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Save pending writes."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        checkpoint_id = self._get_checkpoint_id(config)

        if not checkpoint_id:
            return

        docs = []
        for channel, value in writes:
            type_str, data_bytes = self.serde.dumps_typed(value)
            docs.append({
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "task_path": task_path,
                "channel": channel,
                "value": base64.b64encode(data_bytes).decode("ascii"),
                "value_type": type_str,
                "created_at": datetime.now(timezone.utc),
            })

        if docs:
            self.db[WRITES_COLLECTION].insert_many(docs)

    def delete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread."""
        self.db[CHECKPOINTS_COLLECTION].delete_many({"thread_id": thread_id})
        self.db[WRITES_COLLECTION].delete_many({"thread_id": thread_id})

    # Async methods

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Get checkpoint tuple by config (async)."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        checkpoint_id = self._get_checkpoint_id(config)

        query = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
        }
        if checkpoint_id:
            query["checkpoint_id"] = checkpoint_id

        doc = await self.async_db[CHECKPOINTS_COLLECTION].find_one(
            query,
            sort=[("checkpoint_id", -1)],
        )

        if not doc:
            return None

        # Get pending writes
        writes_cursor = self.async_db[WRITES_COLLECTION].find({
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": doc["checkpoint_id"],
        })
        writes_docs = await writes_cursor.to_list(length=100)

        pending_writes = [
            (
                w["task_id"],
                w["channel"],
                self.serde.loads_typed((
                    w.get("value_type", self.serde.dumps_typed({})[0]),
                    base64.b64decode(w["value"]),
                )),
            )
            for w in writes_docs
        ] if writes_docs else None

        return CheckpointTuple(
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": doc["checkpoint_id"],
                }
            },
            checkpoint=self._deserialize_checkpoint(doc["checkpoint"]),
            metadata=self._deserialize_metadata(doc.get("metadata", {})),
            parent_config={
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": checkpoint_ns,
                    "checkpoint_id": doc["parent_checkpoint_id"],
                }
            } if doc.get("parent_checkpoint_id") else None,
            pending_writes=pending_writes,
        )

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints matching criteria (async)."""
        query: dict[str, Any] = {}

        if config:
            thread_id = self._get_thread_id(config)
            checkpoint_ns = self._get_checkpoint_ns(config)
            if thread_id:
                query["thread_id"] = thread_id
            if checkpoint_ns:
                query["checkpoint_ns"] = checkpoint_ns

        if filter:
            for key, value in filter.items():
                query[f"metadata.{key}"] = value

        if before:
            before_id = self._get_checkpoint_id(before)
            if before_id:
                query["checkpoint_id"] = {"$lt": before_id}

        cursor = self.async_db[CHECKPOINTS_COLLECTION].find(query).sort("checkpoint_id", -1)
        if limit:
            cursor = cursor.limit(limit)

        async for doc in cursor:
            yield CheckpointTuple(
                config={
                    "configurable": {
                        "thread_id": doc["thread_id"],
                        "checkpoint_ns": doc["checkpoint_ns"],
                        "checkpoint_id": doc["checkpoint_id"],
                    }
                },
                checkpoint=self._deserialize_checkpoint(doc["checkpoint"]),
                metadata=self._deserialize_metadata(doc.get("metadata", {})),
                parent_config={
                    "configurable": {
                        "thread_id": doc["thread_id"],
                        "checkpoint_ns": doc["checkpoint_ns"],
                        "checkpoint_id": doc["parent_checkpoint_id"],
                    }
                } if doc.get("parent_checkpoint_id") else None,
                pending_writes=None,
            )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """Save a checkpoint (async)."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        parent_checkpoint_id = self._get_checkpoint_id(config)

        doc = {
            "thread_id": thread_id,
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": checkpoint["id"],
            "parent_checkpoint_id": parent_checkpoint_id,
            "checkpoint": self._serialize_checkpoint(checkpoint),
            "metadata": self._serialize_metadata(metadata),
            "created_at": datetime.now(timezone.utc),
        }

        await self.async_db[CHECKPOINTS_COLLECTION].replace_one(
            {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            },
            doc,
            upsert=True,
        )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Save pending writes (async)."""
        thread_id = self._get_thread_id(config)
        checkpoint_ns = self._get_checkpoint_ns(config)
        checkpoint_id = self._get_checkpoint_id(config)

        if not checkpoint_id:
            return

        docs = []
        for channel, value in writes:
            type_str, data_bytes = self.serde.dumps_typed(value)
            docs.append({
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "task_id": task_id,
                "task_path": task_path,
                "channel": channel,
                "value": base64.b64encode(data_bytes).decode("ascii"),
                "value_type": type_str,
                "created_at": datetime.now(timezone.utc),
            })

        if docs:
            await self.async_db[WRITES_COLLECTION].insert_many(docs)

    async def adelete_thread(self, thread_id: str) -> None:
        """Delete all checkpoints for a thread (async)."""
        await self.async_db[CHECKPOINTS_COLLECTION].delete_many({"thread_id": thread_id})
        await self.async_db[WRITES_COLLECTION].delete_many({"thread_id": thread_id})


# Singleton instance
_saver: MongoDBSaver | None = None


def get_mongodb_saver() -> MongoDBSaver:
    """Get or create the MongoDB saver singleton."""
    global _saver
    if _saver is None:
        _saver = MongoDBSaver()
    return _saver


__all__ = ["MongoDBSaver", "get_mongodb_saver"]
