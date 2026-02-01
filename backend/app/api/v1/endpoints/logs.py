"""
Logging endpoints.
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user, require_admin
from app.db.repositories.log import get_log_repository, LogRepository
from app.schemas.log import (
    LogEntry,
    LogListResponse,
    LogStatsResponse,
    CreateLogRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_repo() -> LogRepository:
    """Get the log repository."""
    return get_log_repository()


@router.get("", response_model=LogListResponse)
async def get_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by log source"),
    start_time: Optional[datetime] = Query(None, description="Filter logs after this time"),
    end_time: Optional[datetime] = Query(None, description="Filter logs before this time"),
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    search: Optional[str] = Query(None, description="Search in message text"),
    current_user: dict = Depends(get_current_user),
    repo: LogRepository = Depends(get_repo),
):
    """
    Get system logs with filtering and pagination.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        level: Filter by log level (debug, info, warning, error, critical)
        source: Filter by log source (system, api, agent, orchestrator, platform, etc.)
        start_time: Filter logs after this time
        end_time: Filter logs before this time
        platform_id: Filter by platform ID
        agent_id: Filter by agent ID
        search: Search in message text

    Returns:
        Paginated list of log entries
    """
    result = await repo.find_many(
        page=page,
        page_size=page_size,
        level=level,
        source=source,
        start_time=start_time,
        end_time=end_time,
        platform_id=platform_id,
        agent_id=agent_id,
        search=search,
    )

    return LogListResponse(
        items=[LogEntry(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(
    current_user: dict = Depends(get_current_user),
    repo: LogRepository = Depends(get_repo),
):
    """
    Get log statistics.

    Returns summary statistics including counts by level and source,
    and recent error entries.
    """
    stats = await repo.get_stats()

    return LogStatsResponse(
        total=stats["total"],
        by_level=stats["by_level"],
        by_source=stats["by_source"],
        recent_errors=[LogEntry(**e) for e in stats["recent_errors"]],
    )


@router.post("", response_model=LogEntry, status_code=status.HTTP_201_CREATED)
async def create_log(
    request: CreateLogRequest,
    current_user: dict = Depends(get_current_user),
    repo: LogRepository = Depends(get_repo),
):
    """
    Create a new log entry.

    This endpoint allows programmatic logging from external sources.

    Args:
        request: Log entry data

    Returns:
        Created log entry
    """
    result = await repo.create(
        level=request.level,
        source=request.source,
        message=request.message,
        details=request.details,
        user_id=current_user.get("id"),
        platform_id=request.platform_id,
        agent_id=request.agent_id,
        execution_id=request.execution_id,
    )

    return LogEntry(**result)


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = Query(30, ge=1, le=365, description="Delete logs older than this many days"),
    current_user: dict = Depends(require_admin),
    repo: LogRepository = Depends(get_repo),
):
    """
    Delete old log entries.

    Requires admin privileges.

    Args:
        days: Delete logs older than this many days (default: 30)

    Returns:
        Number of deleted entries
    """
    deleted_count = await repo.delete_old(days=days)

    logger.info(
        f"Log cleanup performed by user '{current_user.get('username')}': "
        f"{deleted_count} entries deleted (older than {days} days)"
    )

    return {
        "message": f"Deleted {deleted_count} log entries older than {days} days",
        "deleted_count": deleted_count,
    }


@router.get("/levels")
async def get_log_levels():
    """
    Get available log levels.

    Returns list of valid log levels.
    """
    return {
        "levels": ["debug", "info", "warning", "error", "critical"],
    }


@router.get("/sources")
async def get_log_sources():
    """
    Get available log sources.

    Returns list of valid log sources.
    """
    return {
        "sources": [
            "system",
            "api",
            "agent",
            "orchestrator",
            "platform",
            "auth",
            "database",
            "llm",
        ],
    }
