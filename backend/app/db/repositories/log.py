"""
Log repository for MongoDB operations.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from bson import ObjectId

from app.db.mongodb import get_database
from app.models.log import LogLevel, LogSource

logger = logging.getLogger(__name__)


class LogRepository:
    """Repository for log operations."""

    collection_name = "logs"

    def __init__(self):
        self.db = get_database()
        if self.db is not None:
            self.collection = self.db[self.collection_name]
        else:
            self.collection = None

    def _format_log(self, doc: dict) -> dict:
        """Format a log document for response."""
        if doc is None:
            return None
        return {
            "id": str(doc.get("_id", "")),
            "timestamp": doc.get("timestamp"),
            "level": doc.get("level"),
            "source": doc.get("source"),
            "message": doc.get("message"),
            "details": doc.get("details", {}),
            "user_id": doc.get("user_id"),
            "platform_id": doc.get("platform_id"),
            "agent_id": doc.get("agent_id"),
            "execution_id": doc.get("execution_id"),
            "trace_id": doc.get("trace_id"),
            "duration_ms": doc.get("duration_ms"),
            "error": doc.get("error"),
        }

    async def create(
        self,
        level: str,
        source: str,
        message: str,
        details: Dict[str, Any] = None,
        user_id: Optional[str] = None,
        platform_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> dict:
        """
        Create a new log entry.

        Args:
            level: Log level
            source: Log source
            message: Log message
            details: Additional details
            user_id: Associated user ID
            platform_id: Associated platform ID
            agent_id: Associated agent ID
            execution_id: Associated execution ID
            trace_id: Trace ID for correlation
            duration_ms: Duration in milliseconds
            error: Error message if applicable
            stack_trace: Stack trace if applicable

        Returns:
            Created log entry
        """
        doc = {
            "timestamp": datetime.utcnow(),
            "level": level,
            "source": source,
            "message": message,
            "details": details or {},
            "user_id": user_id,
            "platform_id": platform_id,
            "agent_id": agent_id,
            "execution_id": execution_id,
            "trace_id": trace_id,
            "duration_ms": duration_ms,
            "error": error,
            "stack_trace": stack_trace,
        }

        if self.collection is not None:
            result = await self.collection.insert_one(doc)
            doc["_id"] = result.inserted_id
        else:
            # In-memory logging when DB is not available
            logger.log(
                getattr(logging, level.upper(), logging.INFO),
                f"[{source}] {message}",
                extra={"details": details},
            )

        return self._format_log(doc)

    async def find_many(
        self,
        page: int = 1,
        page_size: int = 50,
        level: Optional[str] = None,
        source: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        platform_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find logs with filtering and pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            level: Filter by log level
            source: Filter by log source
            start_time: Filter logs after this time
            end_time: Filter logs before this time
            platform_id: Filter by platform ID
            agent_id: Filter by agent ID
            search: Search in message text

        Returns:
            Dictionary with items, total, page info
        """
        if self.collection is None:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }

        # Build filter
        filter_query = {}

        if level:
            filter_query["level"] = level
        if source:
            filter_query["source"] = source
        if platform_id:
            filter_query["platform_id"] = platform_id
        if agent_id:
            filter_query["agent_id"] = agent_id

        if start_time or end_time:
            filter_query["timestamp"] = {}
            if start_time:
                filter_query["timestamp"]["$gte"] = start_time
            if end_time:
                filter_query["timestamp"]["$lte"] = end_time

        if search:
            filter_query["message"] = {"$regex": search, "$options": "i"}

        # Get total count
        total = await self.collection.count_documents(filter_query)
        total_pages = (total + page_size - 1) // page_size

        # Get paginated results
        skip = (page - 1) * page_size
        cursor = self.collection.find(filter_query)
        cursor = cursor.sort("timestamp", -1).skip(skip).limit(page_size)

        items = []
        async for doc in cursor:
            items.append(self._format_log(doc))

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get log statistics.

        Returns:
            Dictionary with log statistics
        """
        if self.collection is None:
            return {
                "total": 0,
                "by_level": {},
                "by_source": {},
                "recent_errors": [],
            }

        # Total count
        total = await self.collection.count_documents({})

        # Count by level
        by_level = {}
        level_pipeline = [
            {"$group": {"_id": "$level", "count": {"$sum": 1}}}
        ]
        async for doc in self.collection.aggregate(level_pipeline):
            by_level[doc["_id"]] = doc["count"]

        # Count by source
        by_source = {}
        source_pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}}
        ]
        async for doc in self.collection.aggregate(source_pipeline):
            by_source[doc["_id"]] = doc["count"]

        # Recent errors
        error_cursor = self.collection.find(
            {"level": {"$in": ["error", "critical"]}}
        ).sort("timestamp", -1).limit(10)

        recent_errors = []
        async for doc in error_cursor:
            recent_errors.append(self._format_log(doc))

        return {
            "total": total,
            "by_level": by_level,
            "by_source": by_source,
            "recent_errors": recent_errors,
        }

    async def delete_old(self, days: int = 30) -> int:
        """
        Delete logs older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted logs
        """
        if self.collection is None:
            return 0

        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.collection.delete_many(
            {"timestamp": {"$lt": cutoff}}
        )

        logger.info(f"Deleted {result.deleted_count} old log entries")
        return result.deleted_count


# Repository instance
_log_repository: Optional[LogRepository] = None


def get_log_repository() -> LogRepository:
    """Get the log repository instance."""
    global _log_repository
    if _log_repository is None:
        _log_repository = LogRepository()
    return _log_repository


# Convenience function for logging
async def log_event(
    level: str,
    source: str,
    message: str,
    **kwargs,
) -> dict:
    """
    Log an event to the database.

    Args:
        level: Log level (debug, info, warning, error, critical)
        source: Log source (system, api, agent, etc.)
        message: Log message
        **kwargs: Additional log fields

    Returns:
        Created log entry
    """
    repo = get_log_repository()
    return await repo.create(level=level, source=source, message=message, **kwargs)
