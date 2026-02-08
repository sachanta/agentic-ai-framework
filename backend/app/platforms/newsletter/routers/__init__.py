"""
Newsletter Platform routers.

Modular routers for different API sections.
"""
from app.platforms.newsletter.routers.research import router as research_router
from app.platforms.newsletter.routers.writing import router as writing_router
from app.platforms.newsletter.routers.preference import router as preference_router
from app.platforms.newsletter.routers.newsletters import router as newsletters_router
from app.platforms.newsletter.routers.workflows import router as workflows_router
from app.platforms.newsletter.routers.campaigns import router as campaigns_router
from app.platforms.newsletter.routers.subscribers import router as subscribers_router
from app.platforms.newsletter.routers.templates import router as templates_router
from app.platforms.newsletter.routers.analytics import router as analytics_router

__all__ = [
    # Phase 6-8: Agent endpoints
    "research_router",
    "writing_router",
    "preference_router",
    # Phase 11: Complete REST API
    "newsletters_router",
    "workflows_router",
    "campaigns_router",
    "subscribers_router",
    "templates_router",
    "analytics_router",
]
