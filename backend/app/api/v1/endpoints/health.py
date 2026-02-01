"""
Health check endpoints.
"""
import time
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.mongodb import get_mongodb_status
from app.db.weaviate import get_weaviate_status, is_weaviate_available

router = APIRouter()


class ServiceHealth(BaseModel):
    """Health status for a single service."""
    status: str
    healthy: bool
    latency_ms: Optional[float] = None
    version: Optional[str] = None
    error: Optional[str] = None


class OverallHealth(BaseModel):
    """Overall system health status."""
    status: str
    healthy: bool
    timestamp: float
    services: dict[str, ServiceHealth]


@router.get("", response_model=OverallHealth)
async def health_check():
    """
    Overall health check.

    Returns the health status of all services.
    """
    # Check MongoDB
    mongodb_status = await get_mongodb_status()
    mongodb_health = ServiceHealth(
        status=mongodb_status.get("status", "unknown"),
        healthy=mongodb_status.get("healthy", False),
        latency_ms=mongodb_status.get("latency_ms"),
        version=mongodb_status.get("version"),
        error=mongodb_status.get("error"),
    )

    # Check Weaviate
    weaviate_status = await get_weaviate_status()
    weaviate_health = ServiceHealth(
        status=weaviate_status.get("status", "unknown"),
        healthy=weaviate_status.get("healthy", False),
        latency_ms=weaviate_status.get("latency_ms"),
        version=weaviate_status.get("version"),
        error=weaviate_status.get("error"),
    )

    # API is healthy if it's responding
    api_health = ServiceHealth(
        status="connected",
        healthy=True,
        latency_ms=0,
    )

    # Overall health - healthy if MongoDB is up (Weaviate is optional)
    overall_healthy = mongodb_health.healthy
    overall_status = "healthy" if overall_healthy else "degraded"

    return OverallHealth(
        status=overall_status,
        healthy=overall_healthy,
        timestamp=time.time(),
        services={
            "api": api_health,
            "mongodb": mongodb_health,
            "weaviate": weaviate_health,
        },
    )


@router.get("/mongodb", response_model=ServiceHealth)
async def mongodb_health():
    """MongoDB health check."""
    status = await get_mongodb_status()
    return ServiceHealth(
        status=status.get("status", "unknown"),
        healthy=status.get("healthy", False),
        latency_ms=status.get("latency_ms"),
        version=status.get("version"),
        error=status.get("error"),
    )


@router.get("/weaviate", response_model=ServiceHealth)
async def weaviate_health():
    """Weaviate health check."""
    status = await get_weaviate_status()
    return ServiceHealth(
        status=status.get("status", "unknown"),
        healthy=status.get("healthy", False),
        latency_ms=status.get("latency_ms"),
        version=status.get("version"),
        error=status.get("error"),
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"ping": "pong", "timestamp": time.time()}
