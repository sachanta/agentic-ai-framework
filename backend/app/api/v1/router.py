"""
API v1 router - combines all endpoint routers.
"""
from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    agents,
    auth,
    executions,
    health,
    logs,
    mongodb,
    platforms,
    settings,
    studio,
    tools,
    tools_studio,
    weaviate,
    workflows,
)
from app.core.security import get_current_user
from app.platforms.hello_world.router import router as hello_world_router
from app.platforms.newsletter.router import router as newsletter_router

api_router = APIRouter()

# Auth-required dependency for protecting entire routers
_auth_required = [Depends(get_current_user)]

# Public endpoints (no auth required)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Protected endpoints (require authentication)
api_router.include_router(
    platforms.router, prefix="/platforms", tags=["platforms"],
    dependencies=_auth_required,
)
api_router.include_router(
    agents.router, prefix="/agents", tags=["agents"],
    dependencies=_auth_required,
)
api_router.include_router(
    tools.router, prefix="/tools", tags=["tools"],
    dependencies=_auth_required,
)
api_router.include_router(
    workflows.router, prefix="/workflows", tags=["workflows"],
    dependencies=_auth_required,
)
api_router.include_router(
    executions.router, prefix="/executions", tags=["executions"],
    dependencies=_auth_required,
)
api_router.include_router(
    logs.router, prefix="/logs", tags=["logs"],
    dependencies=_auth_required,
)
api_router.include_router(
    settings.router, prefix="/settings", tags=["settings"],
    dependencies=_auth_required,
)
api_router.include_router(
    weaviate.router, prefix="/weaviate", tags=["weaviate"],
    dependencies=_auth_required,
)
api_router.include_router(
    mongodb.router, prefix="/mongodb", tags=["mongodb"],
    dependencies=_auth_required,
)
api_router.include_router(
    studio.router, prefix="/studio", tags=["studio"],
    dependencies=_auth_required,
)
api_router.include_router(
    tools_studio.router, prefix="/tools-studio", tags=["tools-studio"],
    dependencies=_auth_required,
)

# Platform-specific endpoints (protected)
api_router.include_router(
    hello_world_router,
    prefix="/platforms/hello-world",
    tags=["platform:hello-world"],
    dependencies=_auth_required,
)
api_router.include_router(
    newsletter_router,
    prefix="/platforms/newsletter",
    tags=["platform:newsletter"],
    dependencies=_auth_required,
)
