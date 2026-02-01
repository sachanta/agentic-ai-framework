"""
Platform management endpoints.
"""
import logging
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.platforms import get_platform_registry
from app.schemas.platform import (
    PlatformResponse,
    PlatformDetailResponse,
    PlatformListResponse,
    PlatformExecuteRequest,
    PlatformExecuteResponse,
    AgentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=PlatformListResponse)
async def list_platforms():
    """
    List all available platforms.

    Returns all registered platforms with their basic information.
    """
    registry = get_platform_registry()
    platforms = registry.list_all()

    items = [
        PlatformResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            version=p.version,
            status="active" if p.enabled else "inactive",
            agents=p.agents,
            enabled=p.enabled,
        )
        for p in platforms
    ]

    return PlatformListResponse(items=items, total=len(items))


@router.get("/enabled", response_model=PlatformListResponse)
async def list_enabled_platforms():
    """
    List only enabled platforms.

    Returns platforms that are currently enabled and available for use.
    """
    registry = get_platform_registry()
    platforms = registry.list_enabled()

    items = [
        PlatformResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            version=p.version,
            status="active",
            agents=p.agents,
            enabled=True,
        )
        for p in platforms
    ]

    return PlatformListResponse(items=items, total=len(items))


@router.get("/{platform_id}", response_model=PlatformDetailResponse)
async def get_platform(platform_id: str):
    """
    Get platform details.

    Args:
        platform_id: The platform identifier

    Returns:
        Detailed platform information including agents
    """
    registry = get_platform_registry()
    platform = registry.get(platform_id)

    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    # Get agent details from the orchestrator if available
    agents = []
    try:
        orchestrator = registry.create_orchestrator(platform_id)
        if orchestrator:
            for agent_name in orchestrator.list_agents():
                agent = orchestrator.get_agent(agent_name)
                if agent:
                    agents.append(
                        AgentResponse(
                            id=agent.name,
                            name=agent.name,
                            description=getattr(agent, "description", ""),
                            status="active",
                            capabilities=getattr(agent, "capabilities", []),
                        )
                    )
    except Exception as e:
        logger.warning(f"Could not get agents for platform {platform_id}: {e}")
        # Fall back to just agent names
        agents = [
            AgentResponse(
                id=name,
                name=name,
                description="",
                status="unknown",
                capabilities=[],
            )
            for name in platform.agents
        ]

    return PlatformDetailResponse(
        id=platform.id,
        name=platform.name,
        description=platform.description,
        version=platform.version,
        status="active" if platform.enabled else "inactive",
        agents=agents,
        config=platform.config,
        enabled=platform.enabled,
    )


@router.get("/{platform_id}/agents", response_model=List[AgentResponse])
async def list_platform_agents(platform_id: str):
    """
    List all agents in a platform.

    Args:
        platform_id: The platform identifier

    Returns:
        List of agents in the platform
    """
    registry = get_platform_registry()
    platform = registry.get(platform_id)

    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    agents = []
    try:
        orchestrator = registry.create_orchestrator(platform_id)
        if orchestrator:
            for agent_name in orchestrator.list_agents():
                agent = orchestrator.get_agent(agent_name)
                if agent:
                    agents.append(
                        AgentResponse(
                            id=agent.name,
                            name=agent.name,
                            description=getattr(agent, "description", ""),
                            status="active",
                            capabilities=getattr(agent, "capabilities", []),
                        )
                    )
    except Exception as e:
        logger.warning(f"Could not get agents for platform {platform_id}: {e}")
        agents = [
            AgentResponse(
                id=name,
                name=name,
                description="",
                status="unknown",
                capabilities=[],
            )
            for name in platform.agents
        ]

    return agents


@router.post("/{platform_id}/execute", response_model=PlatformExecuteResponse)
async def execute_platform(
    platform_id: str,
    request: PlatformExecuteRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Execute a platform workflow.

    Args:
        platform_id: The platform identifier
        request: Execution request with input data

    Returns:
        Execution result
    """
    registry = get_platform_registry()
    platform = registry.get(platform_id)

    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    if not platform.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Platform '{platform_id}' is not enabled",
        )

    try:
        orchestrator = registry.create_orchestrator(platform_id)
        if not orchestrator:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Could not create orchestrator for platform '{platform_id}'",
            )

        start_time = time.time()
        result = await orchestrator.run(request.input)
        duration_ms = (time.time() - start_time) * 1000

        logger.info(
            f"Platform '{platform_id}' executed by user '{current_user.get('username')}' "
            f"in {duration_ms:.2f}ms"
        )

        return PlatformExecuteResponse(
            success=True,
            result=result,
            duration_ms=duration_ms,
        )

    except Exception as e:
        logger.error(f"Platform execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Platform execution failed: {str(e)}",
        )


@router.post("/{platform_id}/enable")
async def enable_platform(
    platform_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Enable a platform.

    Args:
        platform_id: The platform identifier

    Returns:
        Success message
    """
    registry = get_platform_registry()

    if not registry.get(platform_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    registry.enable(platform_id)
    logger.info(f"Platform '{platform_id}' enabled by user '{current_user.get('username')}'")

    return {"message": f"Platform '{platform_id}' enabled"}


@router.post("/{platform_id}/disable")
async def disable_platform(
    platform_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Disable a platform.

    Args:
        platform_id: The platform identifier

    Returns:
        Success message
    """
    registry = get_platform_registry()

    if not registry.get(platform_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    registry.disable(platform_id)
    logger.info(f"Platform '{platform_id}' disabled by user '{current_user.get('username')}'")

    return {"message": f"Platform '{platform_id}' disabled"}
