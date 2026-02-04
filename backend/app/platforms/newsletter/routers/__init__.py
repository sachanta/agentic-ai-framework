"""
Newsletter Platform routers.

Modular routers for different API sections.
"""
from app.platforms.newsletter.routers.research import router as research_router

__all__ = [
    "research_router",
]
