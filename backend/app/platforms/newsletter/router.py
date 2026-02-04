"""
Newsletter Platform API routes.

These routes are registered under /api/v1/platforms/newsletter/
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
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
from app.platforms.newsletter.routers import research_router

router = APIRouter()

# Include modular routers
router.include_router(research_router)


@router.get("/status", response_model=PlatformStatusResponse)
async def get_platform_status():
    """Get the status of the Newsletter platform."""
    return PlatformStatusResponse(
        platform_id="newsletter",
        name="Newsletter",
        status="active" if config.ENABLED else "disabled",
        agents=["research", "writing", "preference", "custom_prompt", "mindmap"],
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
            "status": "pending",  # Will be "active" after Phase 6
        },
        {
            "id": "writing",
            "name": "Writing Agent",
            "description": "Newsletter content generation",
            "status": "pending",  # Will be "active" after Phase 7
        },
        {
            "id": "preference",
            "name": "Preference Agent",
            "description": "User personalization and preference tracking",
            "status": "pending",  # Will be "active" after Phase 8
        },
        {
            "id": "custom_prompt",
            "name": "Custom Prompt Agent",
            "description": "NLP processing for natural language queries",
            "status": "pending",  # Will be "active" after Phase 8
        },
        {
            "id": "mindmap",
            "name": "Mindmap Agent",
            "description": "Visual knowledge map generation",
            "status": "pending",  # Will be "active" after Phase 9
        },
    ]


@router.post("/newsletters/generate", response_model=GenerateNewsletterResponse)
async def generate_newsletter(
    request: GenerateNewsletterRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Start newsletter generation workflow.

    This initiates the multi-agent workflow with HITL checkpoints.
    Returns a workflow_id to track progress.
    """
    service = NewsletterService()
    result = await service.generate_newsletter(
        user_id=current_user["id"],
        topics=request.topics,
        tone=request.tone.value,
        max_articles=request.max_articles,
        custom_prompt=request.custom_prompt,
        include_mindmap=request.include_mindmap,
    )
    return GenerateNewsletterResponse(
        workflow_id=result["workflow_id"],
        status=result["status"],
        message=result.get("message", "Newsletter generation started"),
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the status of a newsletter generation workflow."""
    service = NewsletterService()
    result = await service.get_workflow_status(workflow_id)

    if not result:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return result


@router.get("/workflows/{workflow_id}/checkpoint", response_model=CheckpointResponse)
async def get_pending_checkpoint(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the current pending checkpoint for a workflow."""
    service = NewsletterService()
    result = await service.get_pending_checkpoint(workflow_id)

    if not result:
        raise HTTPException(status_code=404, detail="No pending checkpoint")

    return result


@router.post("/workflows/{workflow_id}/approve")
async def approve_checkpoint(
    workflow_id: str,
    request: ApproveCheckpointRequest,
    current_user: dict = Depends(get_current_user),
):
    """Approve, edit, or reject the current checkpoint."""
    service = NewsletterService()
    result = await service.approve_checkpoint(
        workflow_id=workflow_id,
        checkpoint_id=request.checkpoint_id,
        action=request.action,
        modifications=request.modifications,
        feedback=request.feedback,
    )
    return result


@router.post("/workflows/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel a running workflow."""
    service = NewsletterService()
    result = await service.cancel_workflow(workflow_id)
    return result
