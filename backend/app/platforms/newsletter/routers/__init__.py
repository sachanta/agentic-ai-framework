"""
Newsletter Platform routers.

Modular routers for different API sections.
"""
from app.platforms.newsletter.routers.research import router as research_router
from app.platforms.newsletter.routers.writing import router as writing_router
from app.platforms.newsletter.routers.preference import router as preference_router

__all__ = [
    "research_router",
    "writing_router",
    "preference_router",
]
