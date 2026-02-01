"""
API v1 router - combines all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    platforms,
    agents,
    tools,
    workflows,
    executions,
    logs,
    settings,
    weaviate,
    mongodb,
)

# Platform routers
from app.platforms.hello_world.router import router as hello_world_router

api_router = APIRouter()

# Core endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(platforms.router, prefix="/platforms", tags=["platforms"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(weaviate.router, prefix="/weaviate", tags=["weaviate"])
api_router.include_router(mongodb.router, prefix="/mongodb", tags=["mongodb"])

# Platform-specific endpoints
api_router.include_router(
    hello_world_router,
    prefix="/platforms/hello-world",
    tags=["platform:hello-world"],
)
