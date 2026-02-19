"""
Memory Service for Newsletter Platform.

Provides short-term caching and context persistence using MongoDB with TTL indexes.
Handles user preferences, research results, engagement metrics, and session state.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from app.db.mongodb import get_database
from app.platforms.newsletter.config import config

logger = logging.getLogger(__name__)


# Collection name for newsletter cache
CACHE_COLLECTION = "newsletter_cache"


class CacheType(str, Enum):
    """Types of cached data."""
    PREFERENCES = "preferences"
    RESEARCH = "research"
    ENGAGEMENT = "engagement"
    SESSION = "session"
    WORKFLOW = "workflow"
    ANALYTICS = "analytics"


class MemoryService:
    """
    Memory service for short-term context and caching.

    Features:
    - Store/retrieve user preferences with TTL
    - Cache research results to avoid duplicate searches
    - Track engagement metrics in real-time
    - Persist workflow state across API calls
    - Automatic expiration via MongoDB TTL indexes
    """

    def __init__(self, default_ttl: Optional[int] = None):
        """
        Initialize the memory service.

        Args:
            default_ttl: Default TTL in seconds (uses config if not specified)
        """
        self.default_ttl = default_ttl or config.CACHE_TTL_SECONDS
        self._indexes_ensured = False

    def _get_collection(self):
        """Get the cache collection."""
        db = get_database()
        return db[CACHE_COLLECTION]

    async def ensure_indexes(self) -> bool:
        """
        Ensure TTL index exists on the cache collection.

        Returns:
            True if indexes are ready
        """
        if self._indexes_ensured:
            return True

        try:
            collection = self._get_collection()

            # Create TTL index on expires_at field
            # MongoDB will automatically delete documents when expires_at is reached
            await collection.create_index(
                "expires_at",
                expireAfterSeconds=0,  # Use the expires_at field value directly
                name="ttl_index"
            )

            # Create compound index for efficient lookups
            await collection.create_index(
                [("user_id", 1), ("type", 1), ("key", 1)],
                name="user_type_key_index"
            )

            # Create index for key lookups
            await collection.create_index("key", name="key_index")

            logger.info(f"Ensured indexes on {CACHE_COLLECTION} collection")
            self._indexes_ensured = True
            return True

        except Exception as e:
            logger.error(f"Failed to ensure indexes: {e}")
            return False

    def _make_key(self, user_id: str, cache_type: CacheType, key: str) -> str:
        """Create a composite cache key."""
        return f"{user_id}:{cache_type.value}:{key}"

    async def set(
        self,
        user_id: str,
        cache_type: CacheType,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store a value in the cache.

        Args:
            user_id: User who owns this cache entry
            cache_type: Type of cached data
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: TTL in seconds (uses default if not specified)

        Returns:
            True if stored successfully
        """
        try:
            await self.ensure_indexes()
            collection = self._get_collection()

            ttl_seconds = ttl if ttl is not None else self.default_ttl
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=ttl_seconds)

            composite_key = self._make_key(user_id, cache_type, key)

            doc = {
                "key": composite_key,
                "user_id": user_id,
                "type": cache_type.value,
                "subkey": key,
                "value": self._serialize_value(value),
                "created_at": now,
                "expires_at": expires_at,
                "ttl_seconds": ttl_seconds,
            }

            # Upsert to handle updates
            await collection.update_one(
                {"key": composite_key},
                {"$set": doc},
                upsert=True,
            )

            logger.debug(f"Cached {cache_type.value}:{key} for user {user_id} (TTL: {ttl_seconds}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to cache value: {e}")
            return False

    async def get(
        self,
        user_id: str,
        cache_type: CacheType,
        key: str,
    ) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            user_id: User who owns this cache entry
            cache_type: Type of cached data
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            collection = self._get_collection()
            composite_key = self._make_key(user_id, cache_type, key)

            doc = await collection.find_one({"key": composite_key})

            if not doc:
                return None

            # Check if expired (TTL index should handle this, but double-check)
            expires_at = doc.get("expires_at")
            if expires_at:
                # Ensure timezone-aware comparison (MongoDB may return naive datetimes)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at < datetime.now(timezone.utc):
                    logger.debug(f"Cache entry expired: {composite_key}")
                    return None

            return self._deserialize_value(doc.get("value"))

        except Exception as e:
            logger.error(f"Failed to get cached value: {e}")
            return None

    async def delete(
        self,
        user_id: str,
        cache_type: CacheType,
        key: str,
    ) -> bool:
        """
        Delete a cached value.

        Args:
            user_id: User who owns this cache entry
            cache_type: Type of cached data
            key: Cache key

        Returns:
            True if deleted (or didn't exist)
        """
        try:
            collection = self._get_collection()
            composite_key = self._make_key(user_id, cache_type, key)

            await collection.delete_one({"key": composite_key})
            return True

        except Exception as e:
            logger.error(f"Failed to delete cached value: {e}")
            return False

    async def delete_by_type(
        self,
        user_id: str,
        cache_type: CacheType,
    ) -> int:
        """
        Delete all cached values of a specific type for a user.

        Args:
            user_id: User who owns these cache entries
            cache_type: Type of cached data to delete

        Returns:
            Number of entries deleted
        """
        try:
            collection = self._get_collection()

            result = await collection.delete_many({
                "user_id": user_id,
                "type": cache_type.value,
            })

            return result.deleted_count

        except Exception as e:
            logger.error(f"Failed to delete cached values by type: {e}")
            return 0

    async def delete_all_user_data(self, user_id: str) -> int:
        """
        Delete all cached data for a user.

        Args:
            user_id: User whose cache to clear

        Returns:
            Number of entries deleted
        """
        try:
            collection = self._get_collection()

            result = await collection.delete_many({"user_id": user_id})
            logger.info(f"Deleted {result.deleted_count} cache entries for user {user_id}")
            return result.deleted_count

        except Exception as e:
            logger.error(f"Failed to delete user cache: {e}")
            return 0

    async def get_all_by_type(
        self,
        user_id: str,
        cache_type: CacheType,
    ) -> List[Dict[str, Any]]:
        """
        Get all cached values of a specific type for a user.

        Args:
            user_id: User who owns these cache entries
            cache_type: Type of cached data

        Returns:
            List of cached entries with key and value
        """
        try:
            collection = self._get_collection()
            now = datetime.now(timezone.utc)

            cursor = collection.find({
                "user_id": user_id,
                "type": cache_type.value,
                "expires_at": {"$gt": now},  # Only non-expired
            })

            results = []
            async for doc in cursor:
                results.append({
                    "key": doc.get("subkey"),
                    "value": self._deserialize_value(doc.get("value")),
                    "created_at": doc.get("created_at"),
                    "expires_at": doc.get("expires_at"),
                })

            return results

        except Exception as e:
            logger.error(f"Failed to get cached values by type: {e}")
            return []

    # Convenience methods for specific cache types

    async def set_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Store user preferences."""
        return await self.set(
            user_id=user_id,
            cache_type=CacheType.PREFERENCES,
            key="current",
            value=preferences,
            ttl=ttl or 86400,  # 24 hours default for preferences
        )

    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user preferences."""
        return await self.get(
            user_id=user_id,
            cache_type=CacheType.PREFERENCES,
            key="current",
        )

    async def set_research_results(
        self,
        user_id: str,
        topics_hash: str,
        results: List[Dict[str, Any]],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache research results for topics."""
        return await self.set(
            user_id=user_id,
            cache_type=CacheType.RESEARCH,
            key=topics_hash,
            value=results,
            ttl=ttl or 1800,  # 30 minutes default for research
        )

    async def get_research_results(
        self,
        user_id: str,
        topics_hash: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached research results."""
        return await self.get(
            user_id=user_id,
            cache_type=CacheType.RESEARCH,
            key=topics_hash,
        )

    async def update_engagement(
        self,
        user_id: str,
        newsletter_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update engagement metrics for a newsletter.

        Args:
            user_id: User who owns the newsletter
            newsletter_id: Newsletter being engaged with
            event_type: Type of event (open, click, etc.)
            event_data: Additional event data
        """
        # Get existing engagement or create new
        engagement = await self.get(
            user_id=user_id,
            cache_type=CacheType.ENGAGEMENT,
            key=newsletter_id,
        ) or {"events": [], "summary": {}}

        # Add event
        engagement["events"].append({
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": event_data or {},
        })

        # Update summary
        summary = engagement.get("summary", {})
        summary[event_type] = summary.get(event_type, 0) + 1
        engagement["summary"] = summary

        return await self.set(
            user_id=user_id,
            cache_type=CacheType.ENGAGEMENT,
            key=newsletter_id,
            value=engagement,
            ttl=86400,  # 24 hours for engagement
        )

    async def get_engagement(
        self,
        user_id: str,
        newsletter_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get engagement metrics for a newsletter."""
        return await self.get(
            user_id=user_id,
            cache_type=CacheType.ENGAGEMENT,
            key=newsletter_id,
        )

    async def set_workflow_state(
        self,
        user_id: str,
        workflow_id: str,
        state: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Store workflow state for resumability."""
        return await self.set(
            user_id=user_id,
            cache_type=CacheType.WORKFLOW,
            key=workflow_id,
            value=state,
            ttl=ttl or 7200,  # 2 hours default for workflow state
        )

    async def get_workflow_state(
        self,
        user_id: str,
        workflow_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get workflow state."""
        return await self.get(
            user_id=user_id,
            cache_type=CacheType.WORKFLOW,
            key=workflow_id,
        )

    async def set_session_context(
        self,
        user_id: str,
        session_id: str,
        context: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Store session context."""
        return await self.set(
            user_id=user_id,
            cache_type=CacheType.SESSION,
            key=session_id,
            value=context,
            ttl=ttl or 3600,  # 1 hour default for session
        )

    async def get_session_context(
        self,
        user_id: str,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get session context."""
        return await self.get(
            user_id=user_id,
            cache_type=CacheType.SESSION,
            key=session_id,
        )

    async def set_analytics_snapshot(
        self,
        user_id: str,
        snapshot_type: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache analytics snapshot."""
        return await self.set(
            user_id=user_id,
            cache_type=CacheType.ANALYTICS,
            key=snapshot_type,
            value=data,
            ttl=ttl or 300,  # 5 minutes for analytics
        )

    async def get_analytics_snapshot(
        self,
        user_id: str,
        snapshot_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Get cached analytics snapshot."""
        return await self.get(
            user_id=user_id,
            cache_type=CacheType.ANALYTICS,
            key=snapshot_type,
        )

    async def touch(
        self,
        user_id: str,
        cache_type: CacheType,
        key: str,
        extend_ttl: Optional[int] = None,
    ) -> bool:
        """
        Extend the TTL of a cached entry.

        Args:
            user_id: User who owns this cache entry
            cache_type: Type of cached data
            key: Cache key
            extend_ttl: New TTL in seconds (uses original if not specified)

        Returns:
            True if entry was touched
        """
        try:
            collection = self._get_collection()
            composite_key = self._make_key(user_id, cache_type, key)

            doc = await collection.find_one({"key": composite_key})
            if not doc:
                return False

            ttl_seconds = extend_ttl or doc.get("ttl_seconds", self.default_ttl)
            new_expires = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            await collection.update_one(
                {"key": composite_key},
                {"$set": {"expires_at": new_expires}},
            )

            return True

        except Exception as e:
            logger.error(f"Failed to touch cache entry: {e}")
            return False

    async def get_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cache statistics.

        Args:
            user_id: Filter by user (all users if None)

        Returns:
            Statistics about cached entries
        """
        try:
            collection = self._get_collection()
            now = datetime.now(timezone.utc)

            # Build query
            query = {"expires_at": {"$gt": now}}
            if user_id:
                query["user_id"] = user_id

            # Count by type
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$type",
                    "count": {"$sum": 1},
                }},
            ]

            type_counts = {}
            async for doc in collection.aggregate(pipeline):
                type_counts[doc["_id"]] = doc["count"]

            total = sum(type_counts.values())

            return {
                "total_entries": total,
                "by_type": type_counts,
                "user_id": user_id,
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    async def cleanup_expired(self) -> int:
        """
        Manually cleanup expired entries.

        Note: MongoDB TTL index handles this automatically, but this can be
        called for immediate cleanup.

        Returns:
            Number of entries cleaned up
        """
        try:
            collection = self._get_collection()
            now = datetime.now(timezone.utc)

            result = await collection.delete_many({
                "expires_at": {"$lt": now}
            })

            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} expired cache entries")

            return result.deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
            return 0

    def _serialize_value(self, value: Any) -> str:
        """Serialize a value for storage."""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, default=str)
        except (TypeError, ValueError):
            return str(value)

    def _deserialize_value(self, value: Optional[str]) -> Any:
        """Deserialize a stored value."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def health_check(self) -> Dict[str, Any]:
        """
        Check memory service health.

        Returns:
            Health status dictionary
        """
        try:
            collection = self._get_collection()

            # Try a simple operation
            await collection.find_one({})

            stats = await self.get_stats()

            return {
                "healthy": True,
                "collection": CACHE_COLLECTION,
                "indexes_ensured": self._indexes_ensured,
                "default_ttl": self.default_ttl,
                "stats": stats,
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
            }


# Singleton instance
_memory_service: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
    """Get the memory service singleton instance."""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
