"""
Newsletter Platform - AI-powered newsletter generation with multi-agent architecture.

This platform provides automated newsletter creation using specialized agents:
- Research Agent: Content discovery via Tavily search
- Writing Agent: Newsletter content generation
- Preference Agent: User personalization
- Custom Prompt Agent: NLP processing for natural language queries
- Mindmap Agent: Visual knowledge map generation

Structure:
- orchestrator/: LangGraph-based workflow with HITL checkpoints
- agents/: Specialized agents for each task
- schemas/: Request/response schemas
- services/: Business logic and external integrations
- models/: MongoDB document models
- repositories/: Data access layer
- tests/: Platform tests
"""
from app.platforms.newsletter.orchestrator import NewsletterOrchestrator
from app.platforms.registry import get_platform_registry


def register_platform():
    """Register the Newsletter platform."""
    registry = get_platform_registry()
    registry.register(
        platform_id="newsletter",
        name="Newsletter",
        description="AI-powered newsletter generation with multi-agent architecture",
        orchestrator_class=NewsletterOrchestrator,
        version="1.0.0",
        agents=["research", "writing", "preference", "custom_prompt", "mindmap"],
    )


__all__ = ["NewsletterOrchestrator", "register_platform"]
