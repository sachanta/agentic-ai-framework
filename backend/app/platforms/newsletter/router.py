"""
Newsletter Platform API routes.

These routes are registered under /api/v1/platforms/newsletter/

Phase 11: Complete REST API with all routers.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user, require_platform
from app.platforms.newsletter.schemas import (
    GenerateNewsletterRequest,
    GenerateNewsletterResponse,
    PlatformStatusResponse,
    WorkflowStatusResponse,
    CheckpointResponse,
    ApproveCheckpointRequest,
)
from app.platforms.newsletter.services import NewsletterService
from app.platforms.newsletter.config import config
from app.platforms.newsletter.routers import (
    research_router,
    writing_router,
    preference_router,
    newsletters_router,
    workflows_router,
    campaigns_router,
    subscribers_router,
    templates_router,
    analytics_router,
)

router = APIRouter()

# Include modular routers - Phase 6-8 (Agents)
router.include_router(research_router)
router.include_router(writing_router)
router.include_router(preference_router)

# Include Phase 11 routers (Complete REST API)
router.include_router(newsletters_router)
router.include_router(workflows_router)
router.include_router(campaigns_router)
router.include_router(subscribers_router)
router.include_router(templates_router)
router.include_router(analytics_router)


@router.get("/status", response_model=PlatformStatusResponse)
async def get_platform_status():
    """Get the status of the Newsletter platform."""
    return PlatformStatusResponse(
        platform_id="newsletter",
        name="Newsletter",
        status="active" if config.ENABLED else "disabled",
        agents=["research", "writing", "preference", "custom_prompt"],
        version="1.0.0",
        llm_provider=config.effective_provider,
        llm_model=config.effective_model,
    )


@router.get("/config")
async def get_platform_config():
    """Get the current configuration for the platform."""
    return {
        "platform_id": "newsletter",
        "llm": {
            "provider": config.effective_provider,
            "model": config.effective_model,
            "temperature": config.effective_temperature,
            "max_tokens": config.effective_max_tokens,
        },
        "search": {
            "depth": config.SEARCH_DEPTH,
            "max_results_per_topic": config.MAX_RESULTS_PER_TOPIC,
            "recency_days": config.RECENCY_DAYS,
        },
        "content": {
            "max_articles": config.MAX_ARTICLES,
            "default_tone": config.DEFAULT_TONE,
            "default_frequency": config.DEFAULT_FREQUENCY,
            "max_word_count": config.MAX_WORD_COUNT,
        },
        "email": {
            "from_email": config.FROM_EMAIL,
            "from_name": config.FROM_NAME,
        },
    }


@router.get("/health")
async def check_health():
    """
    Check platform and LLM health.

    Returns the health status of the platform and its LLM provider.
    """
    service = NewsletterService()

    # Check LLM health
    llm_healthy = await service.check_llm_health()

    # Check external services
    tavily_configured = bool(config.TAVILY_API_KEY)
    resend_configured = bool(config.RESEND_API_KEY)

    return {
        "platform": "healthy" if config.ENABLED else "disabled",
        "llm": {
            "status": "healthy" if llm_healthy else "unavailable",
            "provider": config.effective_provider,
            "model": config.effective_model,
        },
        "services": {
            "tavily": "configured" if tavily_configured else "not_configured",
            "resend": "configured" if resend_configured else "not_configured",
        },
    }


@router.get("/agents")
async def list_agents():
    """List all agents in the Newsletter platform."""
    return [
        {
            "id": "research",
            "name": "Research Agent",
            "description": "Content discovery via Tavily search",
            "status": "active",
        },
        {
            "id": "writing",
            "name": "Writing Agent",
            "description": "Newsletter content generation",
            "status": "active",
        },
        {
            "id": "preference",
            "name": "Preference Agent",
            "description": "User personalization and preference tracking",
            "status": "active",
        },
        {
            "id": "custom_prompt",
            "name": "Custom Prompt Agent",
            "description": "NLP processing for natural language queries",
            "status": "active",
        },
    ]


# Legacy endpoints for backward compatibility
# These are now also available under /newsletters and /workflows prefixes

@router.post("/generate", response_model=GenerateNewsletterResponse,
              dependencies=[Depends(require_platform("newsletter"))])
async def generate_newsletter_legacy(
    request: GenerateNewsletterRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Start newsletter generation workflow.

    This initiates the multi-agent workflow with HITL checkpoints.
    Returns a workflow_id to track progress.

    Note: This is a legacy endpoint. Prefer using POST /newsletters/generate.
    """
    service = NewsletterService()
    result = await service.generate_newsletter(
        user_id=current_user["id"],
        topics=request.topics,
        tone=request.tone.value,
        max_articles=request.max_articles,
        custom_prompt=request.custom_prompt,
    )
    return GenerateNewsletterResponse(
        workflow_id=result["workflow_id"],
        status=result["status"],
        message=result.get("message", "Newsletter generation started"),
    )
